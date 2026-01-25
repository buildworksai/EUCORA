# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Core deployment views - wrapper endpoints for API coverage.
"""
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.utils import apply_demo_filter
from apps.deployment_intents.models import DeploymentIntent

logger = logging.getLogger(__name__)


@api_view(["GET"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def list_core_deployments(request):
    """
    List deployments (wrapper to deployment_intents).

    GET /api/v1/core/deployments/
    """
    deployments = apply_demo_filter(DeploymentIntent.objects.all(), request)

    # Apply filtering
    status_filter = request.query_params.get("status")
    if status_filter:
        deployments = deployments.filter(status=status_filter)

    # Pagination
    page = int(request.query_params.get("page", 1))
    page_size = min(int(request.query_params.get("page_size", 50)), 100)
    start = (page - 1) * page_size
    end = start + page_size

    total = deployments.count()
    deployments_page = deployments[start:end]

    # Serialize
    items = []
    for deployment in deployments_page:
        items.append(
            {
                "id": str(deployment.correlation_id),
                "app_name": deployment.app_name,
                "version": deployment.version,
                "target_ring": deployment.target_ring,
                "status": deployment.status,
                "risk_score": deployment.risk_score,
                "requires_cab_approval": deployment.requires_cab_approval,
                "created_at": deployment.created_at.isoformat(),
                "submitter": deployment.submitter.username,
            }
        )

    return Response(
        {
            "deployments": items,
            "total": total,
            "page": page,
            "page_size": page_size,
        }
    )


@api_view(["GET"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def get_core_deployment(request, deployment_id):
    """
    Get deployment by ID.

    GET /api/v1/core/deployments/{deployment_id}/
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.all(), request).get(correlation_id=deployment_id)

        return Response(
            {
                "id": str(deployment.correlation_id),
                "app_name": deployment.app_name,
                "version": deployment.version,
                "target_ring": deployment.target_ring,
                "status": deployment.status,
                "risk_score": deployment.risk_score,
                "requires_cab_approval": deployment.requires_cab_approval,
                "evidence_pack_id": str(deployment.evidence_pack_id),
                "created_at": deployment.created_at.isoformat(),
                "updated_at": deployment.updated_at.isoformat(),
                "submitter": deployment.submitter.username,
            }
        )
    except DeploymentIntent.DoesNotExist:
        return Response({"error": "Deployment not found"}, status=status.HTTP_404_NOT_FOUND)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def create_core_deployment(request):
    """
    Create deployment.

    POST /api/v1/core/deployments/
    """
    # Redirect to deployment_intents app
    from apps.deployment_intents.views import create_deployment

    return create_deployment(request)
