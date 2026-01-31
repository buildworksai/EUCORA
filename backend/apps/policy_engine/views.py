# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine views for risk assessment and application policies.
"""
import logging

from django.db.models import Q
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.request import Request
from rest_framework.response import Response

from .models import ApplicationPolicy, PolicySetting, PolicyTemplate, RiskModel

# Import from root services.py (not services/ subdirectory)
from .risk_scoring import calculate_risk_score
from .serializers import (
    ApplicationPolicyCreateSerializer,
    ApplicationPolicyListSerializer,
    ApplicationPolicySerializer,
    ApplicationPolicyUpdateSerializer,
    PolicyMappingPreviewSerializer,
    PolicyTemplateListSerializer,
    PolicyTemplateSerializer,
    PolicyValidationSerializer,
)
from .services.translator import PolicyTranslator

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def assess_risk(request):
    """
    Calculate risk score for a deployment intent.

    POST /api/v1/policy/assess
    Body: {
        "evidence_pack": {...},
        "correlation_id": "..."
    }

    Returns:
        200: {"risk_score": 75, "factor_scores": {...}, "requires_cab_approval": true, "model_version": "v1.0"}
        400: {"error": "Evidence pack required"}
        500: {"error": "No active risk model found"}
    """
    evidence_pack = request.data.get("evidence_pack")
    correlation_id = request.data.get("correlation_id", request.correlation_id)

    if not evidence_pack:
        return Response({"error": "Evidence pack required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        result = calculate_risk_score(evidence_pack, correlation_id)
        return Response(result)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAdminUser])
def get_active_risk_model(request):
    """
    Get active risk model.

    GET /api/v1/policy/risk-model

    Returns:
        200: {"version": "v1.0", "factors": [...], "threshold": 50}
        404: {"error": "No active risk model found"}
    """
    risk_model = RiskModel.objects.filter(is_active=True).first()

    if not risk_model:
        return Response({"error": "No active risk model found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {
            "version": risk_model.version,
            "factors": risk_model.factors,
            "threshold": risk_model.threshold,
            "description": risk_model.description,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_policies(request):
    """
    List all risk models.

    GET /api/v1/policy/

    Returns:
        200: [{"version": "v1.0", "is_active": true, ...}, ...]
    """
    risk_models = RiskModel.objects.all().order_by("-created_at")

    items = []
    for model in risk_models:
        items.append(
            {
                "version": model.version,
                "is_active": model.is_active,
                "threshold": model.threshold,
                "description": model.description,
                "created_at": model.created_at.isoformat(),
            }
        )

    return Response(items)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def evaluate_policy(request):
    """
    Evaluate policy for deployment.

    POST /api/v1/policy/evaluate/
    Body: {
        "package_version": "1.0.0",
        "risk_score": 30.0,
        "test_coverage": 85.5
    }

    Returns:
        200: {"approved": true/false, "reason": "..."}
        400: {"error": "..."}
    """
    package_version = request.data.get("package_version")  # noqa: F841
    risk_score = request.data.get("risk_score")
    test_coverage = request.data.get("test_coverage")  # noqa: F841

    if risk_score is None:
        return Response({"error": "risk_score is required"}, status=status.HTTP_400_BAD_REQUEST)

    # Get active risk model
    risk_model = RiskModel.objects.filter(is_active=True).first()
    if not risk_model:
        return Response({"error": "No active risk model found"}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

    # Evaluate against threshold
    approved = risk_score <= risk_model.threshold

    return Response(
        {
            "approved": approved,
            "risk_score": risk_score,
            "threshold": risk_model.threshold,
            "reason": (
                "Risk score below threshold" if approved else "Risk score above threshold - CAB approval required"
            ),
            "model_version": risk_model.version,
        }
    )


# =============================================================================
# APPLICATION POLICY VIEWSETS
# =============================================================================


class ApplicationPolicyViewSet(viewsets.ModelViewSet):
    """
    API endpoint for application policies.

    list: List all policies with filtering
    retrieve: Get policy details
    create: Create a new policy
    update: Update policy details
    destroy: Delete a policy
    apply_template: Apply a template to a policy
    validate: Validate policy settings
    preview_mapping: Preview execution plane mapping
    """

    queryset = (
        ApplicationPolicy.objects.select_related("application", "application_version", "created_by")
        .prefetch_related("settings")
        .all()
    )
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return ApplicationPolicyListSerializer
        if self.action == "create":
            return ApplicationPolicyCreateSerializer
        if self.action in ["update", "partial_update"]:
            return ApplicationPolicyUpdateSerializer
        return ApplicationPolicySerializer

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by application
        application_id = self.request.query_params.get("application")
        if application_id:
            queryset = queryset.filter(application_id=application_id)

        # Filter by platform
        platform = self.request.query_params.get("platform")
        if platform:
            queryset = queryset.filter(platform=platform)

        # Filter by active status
        is_active = self.request.query_params.get("is_active")
        if is_active is not None:
            queryset = queryset.filter(is_active=is_active.lower() == "true")

        # Filter by default
        is_default = self.request.query_params.get("is_default")
        if is_default is not None:
            queryset = queryset.filter(is_default=is_default.lower() == "true")

        # Search by name
        search = self.request.query_params.get("search")
        if search:
            queryset = queryset.filter(Q(name__icontains=search) | Q(description__icontains=search))

        return queryset

    def perform_create(self, serializer):
        """Set created_by on create."""
        serializer.save(created_by=self.request.user)

    @action(detail=True, methods=["post"])
    def apply_template(self, request: Request, pk=None):
        """Apply a template to this policy."""
        policy = self.get_object()
        template_id = request.data.get("template_id")

        if not template_id:
            return Response({"error": "template_id is required"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            template = PolicyTemplate.objects.get(id=template_id)
        except PolicyTemplate.DoesNotExist:
            return Response({"error": "Template not found"}, status=status.HTTP_404_NOT_FOUND)

        # Apply template settings
        settings = template.settings
        policy.settings.all().delete()

        for category, category_settings in settings.items():
            for key, value in category_settings.items():
                PolicySetting.objects.create(
                    policy=policy,
                    category=category,
                    setting_key=key,
                    setting_value=value,
                )

        serializer = self.get_serializer(policy)
        return Response(serializer.data)

    @action(detail=True, methods=["post"])
    def validate(self, request: Request, pk=None):
        """Validate policy settings."""
        policy = self.get_object()
        serializer = PolicyValidationSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # Basic validation: check required settings
        errors = []
        settings_dict = policy.get_settings_dict()

        # Validate installation settings
        if "installation" not in settings_dict:
            errors.append("Installation settings are required")

        # Validate uninstall settings
        if "uninstall" not in settings_dict:
            errors.append("Uninstall settings are required")

        if errors:
            return Response({"valid": False, "errors": errors}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"valid": True, "message": "Policy is valid"})

    @action(detail=True, methods=["post"])
    def preview_mapping(self, request: Request, pk=None):
        """Preview execution plane mapping for this policy."""
        policy = self.get_object()
        serializer = PolicyMappingPreviewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        target_plane = serializer.validated_data["target_plane"]
        translator = PolicyTranslator()

        try:
            mapping = translator.translate(policy, target_plane)
            return Response({"target_plane": target_plane, "mapping": mapping})
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)


class PolicyTemplateViewSet(viewsets.ReadOnlyModelViewSet):
    """
    API endpoint for policy templates.

    list: List all templates
    retrieve: Get template details
    """

    queryset = PolicyTemplate.objects.all()
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        """Return appropriate serializer based on action."""
        if self.action == "list":
            return PolicyTemplateListSerializer
        return PolicyTemplateSerializer

    def get_queryset(self):
        """Filter queryset based on query params."""
        queryset = super().get_queryset()

        # Filter by template type
        template_type = self.request.query_params.get("template_type")
        if template_type:
            queryset = queryset.filter(template_type=template_type)

        # Filter by platform
        platform = self.request.query_params.get("platform")
        if platform:
            queryset = queryset.filter(Q(platform=platform) | Q(platform=""))

        # Filter by system templates
        is_system = self.request.query_params.get("is_system")
        if is_system is not None:
            queryset = queryset.filter(is_system=is_system.lower() == "true")

        return queryset
