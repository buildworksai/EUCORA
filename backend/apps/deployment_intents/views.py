# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Deployment Intent views for orchestration.
"""
import logging
from collections import defaultdict

from django.conf import settings
from django.db import transaction
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.application_portfolio.models import Application, ApplicationDependency
from apps.core.metrics import record_deployment, record_ring_promotion
from apps.core.utils import apply_demo_filter, get_demo_mode_enabled
from apps.policy_engine.risk_scoring import calculate_risk_score

from .models import DeploymentIntent
from .tasks import deploy_to_connector

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_deployment(request):
    """
    Create deployment intent with risk assessment.

    POST /api/v1/deployments/
    Body: {
        "app_name": "...",
        "version": "...",
        "target_ring": "LAB",
        "evidence_pack": {...}
    }
    """
    app_name = request.data.get("app_name")
    version = request.data.get("version")
    target_ring = request.data.get("target_ring")
    evidence_pack = request.data.get("evidence_pack", {})

    if not all([app_name, version, target_ring]):
        return Response(
            {"error": "app_name, version, and target_ring are required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Calculate risk score
    try:
        risk_result = calculate_risk_score(evidence_pack, request.correlation_id)
    except ValueError as e:
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Create deployment intent
    deployment = DeploymentIntent.objects.create(
        app_name=app_name,
        version=version,
        target_ring=target_ring,
        evidence_pack_id=request.correlation_id,
        risk_score=risk_result["risk_score"],
        requires_cab_approval=risk_result["requires_cab_approval"],
        status=(
            DeploymentIntent.Status.AWAITING_CAB
            if risk_result["requires_cab_approval"]
            else DeploymentIntent.Status.APPROVED
        ),
        submitter=request.user,
        is_demo=get_demo_mode_enabled(),
    )

    # Record metrics for deployment creation
    # Status 'pending' for awaiting CAB, 'approved' for immediate deployment
    deployment_status = "pending" if risk_result["requires_cab_approval"] else "approved"
    record_deployment(
        status=deployment_status,
        ring=target_ring,
        app_name=app_name,
        requires_cab=risk_result["requires_cab_approval"],
        duration=0,  # Creation has no meaningful duration
    )

    # Queue async deployment task if approved
    if not risk_result["requires_cab_approval"]:
        connector_type = request.data.get("connector_type", "intune")
        deploy_to_connector.delay(str(deployment.id), connector_type)

    logger.info(
        f"Deployment intent created: {deployment.correlation_id}",
        extra={"correlation_id": str(deployment.correlation_id), "risk_score": risk_result["risk_score"]},
    )

    return Response(
        {
            "correlation_id": str(deployment.correlation_id),
            "status": deployment.status,
            "risk_score": risk_result["risk_score"],
            "requires_cab_approval": risk_result["requires_cab_approval"],
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def list_deployments(request):
    """
    List deployment intents with filters.

    GET /api/v1/deployments/?status=PENDING&ring=LAB
    """
    queryset = apply_demo_filter(DeploymentIntent.objects.select_related("submitter").all(), request)

    # Filters
    status_filter = request.query_params.get("status")
    ring_filter = request.query_params.get("ring")

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if ring_filter:
        queryset = queryset.filter(target_ring=ring_filter)

    deployments = [
        {
            "correlation_id": str(d.correlation_id),
            "app_name": d.app_name,
            "version": d.version,
            "target_ring": d.target_ring,
            "status": d.status,
            "risk_score": d.risk_score,
            "created_at": d.created_at.isoformat(),
        }
        for d in queryset[:100]
    ]  # Limit to 100

    return Response({"deployments": deployments})


@api_view(["GET"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def list_applications_with_versions(request):
    """
    Return application-centric view of deployments grouped by version.

    GET /api/v1/deployments/applications
    Optional query params:
      - app_name: case-insensitive contains filter
      - status: filter by deployment status
      - ring: filter by target ring
    """
    queryset = apply_demo_filter(DeploymentIntent.objects.select_related("submitter").all(), request)

    status_filter = request.query_params.get("status")
    ring_filter = request.query_params.get("ring")
    app_filter = request.query_params.get("app_name")

    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if ring_filter:
        queryset = queryset.filter(target_ring=ring_filter)
    if app_filter:
        queryset = queryset.filter(app_name__icontains=app_filter)

    # Order newest-first within each app to compute latest version reliably
    queryset = queryset.order_by("app_name", "-created_at")

    applications = {}

    for deployment in queryset:
        app_entry = applications.get(deployment.app_name)
        if not app_entry:
            app_entry = {
                "app_name": deployment.app_name,
                "latest_version": deployment.version,
                "deployment_count": 0,
                "versions": {},
            }
            applications[deployment.app_name] = app_entry

        version_entry = app_entry["versions"].get(deployment.version)
        if not version_entry:
            version_entry = {
                "version": deployment.version,
                "latest_created_at": deployment.created_at,
                "deployments": [],
            }
            app_entry["versions"][deployment.version] = version_entry

        version_entry["deployments"].append(
            {
                "correlation_id": str(deployment.correlation_id),
                "target_ring": deployment.target_ring,
                "status": deployment.status,
                "risk_score": deployment.risk_score,
                "requires_cab_approval": deployment.requires_cab_approval,
                "created_at": deployment.created_at.isoformat(),
            }
        )

        app_entry["deployment_count"] += 1

    application_list = []
    for app_data in applications.values():
        versions = list(app_data["versions"].values())
        versions.sort(key=lambda v: v["latest_created_at"], reverse=True)

        application_list.append(
            {
                "app_name": app_data["app_name"],
                "latest_version": app_data["latest_version"],
                "deployment_count": app_data["deployment_count"],
                "versions": [
                    {
                        "version": version["version"],
                        "latest_created_at": version["latest_created_at"].isoformat(),
                        "deployments": version["deployments"],
                    }
                    for version in versions
                ],
            }
        )

    application_list.sort(key=lambda app: app["app_name"].lower())

    return Response({"applications": application_list})


@api_view(["GET"])
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def get_deployment(request, correlation_id):
    """
    Get deployment intent details.

    GET /api/v1/deployments/{correlation_id}/
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.select_related("submitter").all(), request).get(
            correlation_id=correlation_id
        )
    except DeploymentIntent.DoesNotExist:
        return Response({"error": "Deployment not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {
            "correlation_id": str(deployment.correlation_id),
            "app_name": deployment.app_name,
            "version": deployment.version,
            "target_ring": deployment.target_ring,
            "status": deployment.status,
            "risk_score": deployment.risk_score,
            "requires_cab_approval": deployment.requires_cab_approval,
            "submitter": deployment.submitter.username,
            "created_at": deployment.created_at.isoformat(),
        }
    )


# =============================================================================
# STACK API ENDPOINTS (E6)
# =============================================================================


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stack_applications(request):
    """
    Get nested application stack structure.

    GET /api/v1/stack/applications/
    Returns nested structure: App → Version → Deployment → Ring
    """
    queryset = apply_demo_filter(
        DeploymentIntent.objects.select_related("submitter").prefetch_related("ring_deployments").all(), request
    )

    # Group by application
    apps_dict = defaultdict(lambda: {"versions": defaultdict(lambda: {"deployments": []})})

    for deployment in queryset.order_by("app_name", "-created_at"):
        app_name = deployment.app_name
        version = deployment.version

        # Get ring deployments
        rings = []
        for ring_deployment in deployment.ring_deployments.all():
            rings.append(
                {
                    "ring": ring_deployment.ring,
                    "success_rate": ring_deployment.success_rate,
                    "success_count": ring_deployment.success_count,
                    "failure_count": ring_deployment.failure_count,
                    "promoted_at": ring_deployment.promoted_at.isoformat() if ring_deployment.promoted_at else None,
                }
            )

        deployment_data = {
            "id": str(deployment.correlation_id),
            "correlation_id": str(deployment.correlation_id),
            "status": deployment.status,
            "target_ring": deployment.target_ring,
            "risk_score": deployment.risk_score,
            "created_at": deployment.created_at.isoformat(),
            "rings": rings,
        }

        apps_dict[app_name]["versions"][version]["deployments"].append(deployment_data)

    # Build response
    applications = []
    for app_name, app_data in sorted(apps_dict.items()):
        versions = []
        for version, version_data in sorted(app_data["versions"].items(), key=lambda x: x[0], reverse=True):
            versions.append(
                {
                    "version": version,
                    "deployments": version_data["deployments"],
                }
            )

        applications.append(
            {
                "id": app_name,  # Using app_name as ID for now
                "name": app_name,
                "versions": versions,
            }
        )

    return Response({"applications": applications})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stack_application_dependencies(request, app_id):
    """
    Get dependency graph for an application.

    GET /api/v1/stack/applications/{app_id}/dependencies/
    """
    try:
        # Try to find application by name (since deployment_intents uses app_name)
        application = Application.objects.filter(name=app_id).first()
        if not application:
            # Fallback: return empty if app not found in portfolio
            return Response(
                {
                    "application": {"id": app_id, "name": app_id},
                    "dependencies": [],
                    "dependents": [],
                }
            )

        dependencies = ApplicationDependency.objects.filter(application=application).select_related("depends_on")
        dependents = ApplicationDependency.objects.filter(depends_on=application).select_related("application")

        return Response(
            {
                "application": {
                    "id": str(application.id),
                    "name": application.name,
                },
                "dependencies": [
                    {
                        "id": str(dep.depends_on.id),
                        "name": dep.depends_on.name,
                        "type": dep.dependency_type,
                        "required": dep.is_required,
                    }
                    for dep in dependencies
                ],
                "dependents": [
                    {
                        "id": str(dep.application.id),
                        "name": dep.application.name,
                        "type": dep.dependency_type,
                    }
                    for dep in dependents
                ],
            }
        )
    except Exception as e:
        logger.error(f"Error fetching dependencies for {app_id}: {e}")
        return Response({"error": str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def stack_events(request):
    """
    Get deployment events timeline.

    GET /api/v1/stack/events/
    Query params: app_name, status, ring, date_from, date_to
    """
    queryset = apply_demo_filter(DeploymentIntent.objects.select_related("submitter").all(), request)

    # Filters
    app_name = request.query_params.get("app_name")
    status_filter = request.query_params.get("status")
    ring_filter = request.query_params.get("ring")

    if app_name:
        queryset = queryset.filter(app_name__icontains=app_name)
    if status_filter:
        queryset = queryset.filter(status=status_filter)
    if ring_filter:
        queryset = queryset.filter(target_ring=ring_filter)

    events = []
    for deployment in queryset.order_by("-created_at")[:100]:  # Limit to 100
        events.append(
            {
                "id": str(deployment.correlation_id),
                "type": "deployment",
                "title": f"{deployment.app_name} v{deployment.version} → {deployment.target_ring}",
                "description": f"Status: {deployment.status}",
                "status": deployment.status,
                "timestamp": deployment.created_at.isoformat(),
                "user": deployment.submitter.username,
                "item": {
                    "type": "deployment",
                    "id": str(deployment.correlation_id),
                    "app_name": deployment.app_name,
                    "version": deployment.version,
                },
            }
        )

    return Response({"events": events})


# =============================================================================
# DEPLOYMENT ACTION ENDPOINTS (E6)
# =============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def promote_deployment(request, correlation_id):
    """
    Promote deployment to next ring.

    POST /api/v1/stack/deployments/{correlation_id}/promote/
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.all(), request).get(correlation_id=correlation_id)
    except DeploymentIntent.DoesNotExist:
        return Response({"error": "Deployment not found"}, status=status.HTTP_404_NOT_FOUND)

    # Determine next ring
    ring_order = ["LAB", "CANARY", "PILOT", "DEPARTMENT", "GLOBAL"]
    current_index = ring_order.index(deployment.target_ring) if deployment.target_ring in ring_order else -1

    if current_index == -1 or current_index >= len(ring_order) - 1:
        return Response({"error": "Cannot promote further"}, status=status.HTTP_400_BAD_REQUEST)

    next_ring = ring_order[current_index + 1]

    # Update deployment
    from_ring = deployment.target_ring
    deployment.target_ring = next_ring
    deployment.save()

    # Record metrics
    record_ring_promotion(from_ring=from_ring, to_ring=next_ring, status="success")

    return Response(
        {
            "correlation_id": str(deployment.correlation_id),
            "new_ring": next_ring,
            "status": deployment.status,
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def pause_deployment(request, correlation_id):
    """
    Pause a deployment.

    POST /api/v1/stack/deployments/{correlation_id}/pause/
    Paused deployments can be resumed later.
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.all(), request).get(correlation_id=correlation_id)
    except DeploymentIntent.DoesNotExist:
        return Response({"error": "Deployment not found"}, status=status.HTTP_404_NOT_FOUND)

    if deployment.status not in [DeploymentIntent.Status.DEPLOYING, DeploymentIntent.Status.APPROVED]:
        return Response({"error": "Deployment cannot be paused"}, status=status.HTTP_400_BAD_REQUEST)

    deployment.status = DeploymentIntent.Status.PAUSED
    deployment.save()

    logger.info(f"Deployment paused: {correlation_id}", extra={"correlation_id": str(correlation_id)})

    return Response(
        {
            "correlation_id": str(deployment.correlation_id),
            "status": deployment.status,
            "message": "Deployment paused successfully",
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def resume_deployment(request, correlation_id):
    """
    Resume a paused deployment.

    POST /api/v1/stack/deployments/{correlation_id}/resume/
    Only PAUSED deployments can be resumed. REJECTED and CANCELLED cannot be resumed.
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.all(), request).get(correlation_id=correlation_id)
    except DeploymentIntent.DoesNotExist:
        return Response({"error": "Deployment not found"}, status=status.HTTP_404_NOT_FOUND)

    if deployment.status != DeploymentIntent.Status.PAUSED:
        return Response({"error": "Deployment is not paused"}, status=status.HTTP_400_BAD_REQUEST)

    deployment.status = DeploymentIntent.Status.DEPLOYING
    deployment.save()

    logger.info(f"Deployment resumed: {correlation_id}", extra={"correlation_id": str(correlation_id)})

    return Response(
        {
            "correlation_id": str(deployment.correlation_id),
            "status": deployment.status,
            "message": "Deployment resumed successfully",
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def rollback_deployment(request, correlation_id):
    """
    Initiate rollback for a deployment.

    POST /api/v1/stack/deployments/{correlation_id}/rollback/
    Body: {"reason": "..."}
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.all(), request).get(correlation_id=correlation_id)
    except DeploymentIntent.DoesNotExist:
        return Response({"error": "Deployment not found"}, status=status.HTTP_404_NOT_FOUND)

    if deployment.status == DeploymentIntent.Status.ROLLED_BACK:
        return Response({"error": "Deployment already rolled back"}, status=status.HTTP_400_BAD_REQUEST)

    reason = request.data.get("reason", "Manual rollback")

    deployment.status = DeploymentIntent.Status.ROLLED_BACK
    deployment.save()

    logger.info(
        f"Deployment rolled back: {correlation_id}", extra={"correlation_id": str(correlation_id), "reason": reason}
    )

    return Response(
        {
            "correlation_id": str(deployment.correlation_id),
            "status": deployment.status,
            "message": f"Rollback initiated: {reason}",
        }
    )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def cancel_deployment(request, correlation_id):
    """
    Cancel a deployment.

    POST /api/v1/stack/deployments/{correlation_id}/cancel/
    Body: {"reason": "..."}
    Cancellation is permanent - cancelled deployments cannot be resumed.
    """
    try:
        deployment = apply_demo_filter(DeploymentIntent.objects.all(), request).get(correlation_id=correlation_id)
    except DeploymentIntent.DoesNotExist:
        return Response({"error": "Deployment not found"}, status=status.HTTP_404_NOT_FOUND)

    # Cannot cancel already-completed, rolled-back, or cancelled deployments
    if deployment.status in [
        DeploymentIntent.Status.COMPLETED,
        DeploymentIntent.Status.ROLLED_BACK,
        DeploymentIntent.Status.CANCELLED,
    ]:
        return Response(
            {"error": "Cannot cancel completed, rolled back, or already cancelled deployment"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    reason = request.data.get("reason", "Manual cancellation")

    deployment.status = DeploymentIntent.Status.CANCELLED
    deployment.save()

    logger.info(
        f"Deployment cancelled: {correlation_id}", extra={"correlation_id": str(correlation_id), "reason": reason}
    )

    return Response(
        {
            "correlation_id": str(deployment.correlation_id),
            "status": deployment.status,
            "message": f"Deployment cancelled: {reason}",
        }
    )
