# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Phase P5.5: REST API Views for Defense-in-Depth Security Controls

Endpoints:
- Incident reporting and management
- Trust maturity evaluation
- Blast radius classification
- Risk model version management
"""
from decimal import Decimal

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .blast_radius_classifier import BlastRadiusClassifier
from .models_p5_5 import (
    BlastRadiusClass,
    DeploymentIncident,
    RiskModelVersion,
    TrustMaturityLevel,
    TrustMaturityProgress,
)
from .serializers_p5_5 import (
    BlastRadiusClassificationSerializer,
    DeploymentIncidentCreateSerializer,
    DeploymentIncidentSerializer,
    RiskModelVersionSerializer,
    TrustMaturityEvaluationSerializer,
    TrustMaturityStatusSerializer,
)
from .trust_maturity_engine import TrustMaturityEngine

# ============================================================================
# Incident Reporting & Management
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_incident(request):
    """
    Report a deployment incident.

    POST /api/v1/incidents/

    Required fields:
    - deployment_intent_id
    - evidence_package_id
    - severity (P1/P2/P3/P4)
    - title
    - description
    - incident_date (ISO 8601)
    - was_auto_approved
    - risk_score_at_approval
    - blast_radius_class

    Returns 201 with incident details.
    """
    serializer = DeploymentIncidentCreateSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    incident = serializer.save(created_by=request.user.username)

    return Response(DeploymentIncidentSerializer(incident).data, status=status.HTTP_201_CREATED)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_incidents(request):
    """
    List deployment incidents with filters.

    GET /api/v1/incidents/?severity=P1&blast_radius=CRITICAL_INFRASTRUCTURE&limit=50

    Query params:
    - severity: P1/P2/P3/P4
    - blast_radius: CRITICAL_INFRASTRUCTURE, BUSINESS_CRITICAL, etc.
    - was_auto_approved: true/false
    - start_date: ISO 8601
    - end_date: ISO 8601
    - limit: int (default 50)
    - offset: int (default 0)

    Returns paginated incident list.
    """
    queryset = DeploymentIncident.objects.all()

    # Filters
    severity = request.query_params.get("severity")
    if severity:
        queryset = queryset.filter(severity=severity.upper())

    blast_radius = request.query_params.get("blast_radius")
    if blast_radius:
        queryset = queryset.filter(blast_radius_class=blast_radius.upper())

    was_auto_approved = request.query_params.get("was_auto_approved")
    if was_auto_approved is not None:
        queryset = queryset.filter(was_auto_approved=was_auto_approved.lower() == "true")

    start_date = request.query_params.get("start_date")
    if start_date:
        queryset = queryset.filter(incident_date__gte=start_date)

    end_date = request.query_params.get("end_date")
    if end_date:
        queryset = queryset.filter(incident_date__lte=end_date)

    # Pagination
    limit = int(request.query_params.get("limit", 50))
    offset = int(request.query_params.get("offset", 0))

    total_count = queryset.count()
    incidents = queryset[offset : offset + limit]

    return Response(
        {
            "count": total_count,
            "limit": limit,
            "offset": offset,
            "results": DeploymentIncidentSerializer(incidents, many=True).data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_incident(request, incident_id):
    """
    Get incident details.

    GET /api/v1/incidents/{incident_id}/

    Returns incident with full details.
    """
    incident = get_object_or_404(DeploymentIncident, id=incident_id)
    return Response(DeploymentIncidentSerializer(incident).data)


@api_view(["PATCH"])
@permission_classes([IsAuthenticated])
def update_incident(request, incident_id):
    """
    Update incident (resolution, root cause, etc.).

    PATCH /api/v1/incidents/{incident_id}/

    Updatable fields:
    - root_cause
    - resolved_at
    - resolution_method
    - resolution_notes
    - was_preventable
    - preventability_notes
    - control_improvements
    """
    incident = get_object_or_404(DeploymentIncident, id=incident_id)

    # Update allowed fields
    if "root_cause" in request.data:
        incident.root_cause = request.data["root_cause"]

    if "resolved_at" in request.data:
        incident.resolved_at = request.data["resolved_at"]

    if "resolution_method" in request.data:
        incident.resolution_method = request.data["resolution_method"]

    if "resolution_notes" in request.data:
        incident.resolution_notes = request.data["resolution_notes"]

    if "was_preventable" in request.data:
        incident.was_preventable = request.data["was_preventable"]

    if "preventability_notes" in request.data:
        incident.preventability_notes = request.data["preventability_notes"]

    if "control_improvements" in request.data:
        incident.control_improvements = request.data["control_improvements"]

    incident.save()

    return Response(DeploymentIncidentSerializer(incident).data)


# ============================================================================
# Trust Maturity Evaluation
# ============================================================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_maturity_status(request):
    """
    Get current trust maturity status.

    GET /api/v1/maturity/status/

    Returns:
    - current_level
    - risk_model_version
    - auto_approve_thresholds
    - latest_evaluation
    """
    engine = TrustMaturityEngine()
    status_data = engine.get_current_maturity_status()

    return Response(TrustMaturityStatusSerializer(status_data).data)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def evaluate_maturity_progression(request):
    """
    Trigger trust maturity progression evaluation.

    POST /api/v1/maturity/evaluate/

    Body:
    - current_level (optional, auto-detected if not provided)
    - evaluation_period_weeks (default: 4)

    Returns evaluation result with progression recommendation.
    """
    current_level = request.data.get("current_level")

    if not current_level:
        # Auto-detect from active risk model
        try:
            active_model = RiskModelVersion.get_active_version()
            mode_to_level = {
                "GREENFIELD_CONSERVATIVE": "LEVEL_0_BASELINE",
                "CAUTIOUS": "LEVEL_1_CAUTIOUS",
                "MODERATE": "LEVEL_2_MODERATE",
                "MATURE": "LEVEL_3_MATURE",
                "OPTIMIZED": "LEVEL_4_OPTIMIZED",
            }
            current_level = mode_to_level.get(active_model.mode, "LEVEL_0_BASELINE")
        except ValueError:
            return Response({"error": "No active risk model version configured"}, status=status.HTTP_400_BAD_REQUEST)

    evaluation_period_weeks = int(request.data.get("evaluation_period_weeks", 4))

    engine = TrustMaturityEngine()
    result = engine.evaluate_maturity_progression(
        current_level=current_level, evaluation_period_weeks=evaluation_period_weeks
    )

    return Response(TrustMaturityEvaluationSerializer(result).data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_maturity_evaluations(request):
    """
    List historical maturity evaluations.

    GET /api/v1/maturity/evaluations/?limit=20

    Returns paginated list of evaluations.
    """
    limit = int(request.query_params.get("limit", 20))
    offset = int(request.query_params.get("offset", 0))

    evaluations = TrustMaturityProgress.objects.all()[offset : offset + limit]
    total_count = TrustMaturityProgress.objects.count()

    return Response(
        {
            "count": total_count,
            "limit": limit,
            "offset": offset,
            "results": [
                {
                    "id": str(eval.id),
                    "evaluation_date": eval.evaluation_date.isoformat(),
                    "current_level": eval.current_level,
                    "next_level": eval.next_level,
                    "status": eval.status,
                    "incident_rate": float(eval.incident_rate),
                    "p1_incidents": eval.p1_incidents,
                    "p2_incidents": eval.p2_incidents,
                    "ready_to_progress": eval.status == "CRITERIA_MET",
                }
                for eval in evaluations
            ],
        }
    )


# ============================================================================
# Blast Radius Classification
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def classify_deployment(request):
    """
    Classify deployment by blast radius.

    POST /api/v1/blast-radius/classify/

    Body:
    - app_name (required)
    - app_category (optional)
    - requires_admin (optional, default: false)
    - target_user_count (optional)
    - business_criticality (optional: HIGH/MEDIUM/LOW)
    - cmdb_data (optional, future integration)

    Returns classification with justification.
    """
    app_name = request.data.get("app_name")
    if not app_name:
        return Response({"error": "app_name is required"}, status=status.HTTP_400_BAD_REQUEST)

    classifier = BlastRadiusClassifier()

    blast_radius_class = classifier.classify_deployment(
        app_name=app_name,
        app_category=request.data.get("app_category"),
        requires_admin=request.data.get("requires_admin", False),
        target_user_count=request.data.get("target_user_count"),
        business_criticality=request.data.get("business_criticality"),
        cmdb_data=request.data.get("cmdb_data"),
    )

    details = classifier.get_classification_details(blast_radius_class)

    return Response(
        BlastRadiusClassificationSerializer(
            {"app_name": app_name, "blast_radius_class": blast_radius_class, **details}
        ).data
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_blast_radius_classes(request):
    """
    List all blast radius class definitions.

    GET /api/v1/blast-radius/classes/

    Returns all class definitions with policies.
    """
    classes = BlastRadiusClass.objects.all()

    return Response(
        {
            "count": classes.count(),
            "results": [
                {
                    "name": cls.name,
                    "description": cls.description,
                    "business_criticality": cls.business_criticality,
                    "cab_quorum_required": cls.cab_quorum_required,
                    "auto_approve_allowed": cls.auto_approve_allowed,
                    "user_impact_max": cls.user_impact_max,
                    "examples": cls.example_applications,
                }
                for cls in classes
            ],
        }
    )


# ============================================================================
# Risk Model Version Management
# ============================================================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_risk_model_versions(request):
    """
    List all risk model versions.

    GET /api/v1/risk-models/

    Returns all versions with active indicator.
    """
    versions = RiskModelVersion.objects.all()

    return Response(
        {
            "count": versions.count(),
            "active_version": (
                RiskModelVersion.get_active_version().version if versions.filter(is_active=True).exists() else None
            ),
            "results": RiskModelVersionSerializer(versions, many=True).data,
        }
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_active_risk_model(request):
    """
    Get currently active risk model version.

    GET /api/v1/risk-models/active/

    Returns active version with full configuration.
    """
    try:
        active_version = RiskModelVersion.get_active_version()
        return Response(RiskModelVersionSerializer(active_version).data)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def activate_risk_model_version(request, version):
    """
    Activate a risk model version (requires CAB approval).

    POST /api/v1/risk-models/{version}/activate/

    Body:
    - cab_approved: true (required)
    - cab_approval_notes (optional)

    Deactivates current version and activates new version.
    """
    # Check CAB approval
    if not request.data.get("cab_approved"):
        return Response(
            {"error": "CAB approval required to activate risk model version"}, status=status.HTTP_403_FORBIDDEN
        )

    # Get target version
    target_version = get_object_or_404(RiskModelVersion, version=version)

    if target_version.is_active:
        return Response({"error": f"Version {version} is already active"}, status=status.HTTP_400_BAD_REQUEST)

    # Deactivate current active version
    RiskModelVersion.objects.filter(is_active=True).update(is_active=False)

    # Activate target version
    target_version.is_active = True
    target_version.approved_by_cab = True
    target_version.cab_approval_date = timezone.now()
    target_version.cab_approval_notes = request.data.get("cab_approval_notes", "")
    target_version.save()

    return Response(
        {
            "message": f"Risk model version {version} activated",
            "version": RiskModelVersionSerializer(target_version).data,
        }
    )
