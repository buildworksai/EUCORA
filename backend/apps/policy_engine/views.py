# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine views for risk assessment.
"""
import logging

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from rest_framework.response import Response

from .models import RiskAssessment, RiskModel
from .services import calculate_risk_score

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
    package_version = request.data.get("package_version")
    risk_score = request.data.get("risk_score")
    test_coverage = request.data.get("test_coverage")

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
