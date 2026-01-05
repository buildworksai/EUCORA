# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine views for risk assessment.
"""
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework import status
from .models import RiskModel, RiskAssessment
from .services import calculate_risk_score
import logging

logger = logging.getLogger(__name__)


@api_view(['POST'])
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
    evidence_pack = request.data.get('evidence_pack')
    correlation_id = request.data.get('correlation_id', request.correlation_id)
    
    if not evidence_pack:
        return Response(
            {'error': 'Evidence pack required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        result = calculate_risk_score(evidence_pack, correlation_id)
        return Response(result)
    except ValueError as e:
        return Response(
            {'error': str(e)},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['GET'])
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
        return Response(
            {'error': 'No active risk model found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    return Response({
        'version': risk_model.version,
        'factors': risk_model.factors,
        'threshold': risk_model.threshold,
        'description': risk_model.description,
    })
