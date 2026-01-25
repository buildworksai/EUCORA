# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Evidence Store views for artifact management.
"""
import logging

from django.conf import settings
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.utils import apply_demo_filter, exempt_csrf_in_debug, get_demo_mode_enabled

from .models import EvidencePack

logger = logging.getLogger(__name__)


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def upload_evidence_pack(request):
    """
    List or upload evidence pack.

    GET /api/v1/evidence/ - List evidence packs
    POST /api/v1/evidence/ - Upload evidence pack
    """
    if request.method == "GET":
        # List evidence packs
        evidence_packs = apply_demo_filter(EvidencePack.objects.all(), request)

        # Apply pagination
        page = int(request.query_params.get("page", 1))
        page_size = min(int(request.query_params.get("page_size", 50)), 100)
        start = (page - 1) * page_size
        end = start + page_size

        total = evidence_packs.count()
        packs_page = evidence_packs[start:end]

        items = []
        for pack in packs_page:
            items.append(
                {
                    "id": str(pack.correlation_id),
                    "app_name": pack.app_name,
                    "version": pack.version,
                    "artifact_hash": pack.artifact_hash,
                    "is_validated": pack.is_validated,
                    "created_at": pack.created_at.isoformat(),
                }
            )

        return Response(
            {
                "evidence_packages": items,
                "total": total,
                "page": page,
                "page_size": page_size,
            }
        )

    # POST - Upload evidence pack
    # Content-Type: multipart/form-data
    #
    # Form fields:
    #     - app_name: str
    #     - version: str
    #     - artifact: file (binary)
    #     - sbom_data: JSON string
    #     - vulnerability_scan_results: JSON string
    #     - rollback_plan: str
    import json

    from .storage import get_storage

    # Validate required fields
    app_name = request.data.get("app_name")
    version = request.data.get("version")
    artifact_file = request.FILES.get("artifact")

    if not all([app_name, version, artifact_file]):
        return Response(
            {"error": "app_name, version, and artifact file are required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Parse JSON fields
    try:
        sbom_data = json.loads(request.data.get("sbom_data", "{}"))
        vulnerability_scan_results = json.loads(request.data.get("vulnerability_scan_results", "{}"))
    except json.JSONDecodeError as e:
        return Response(
            {"error": f"Invalid JSON in sbom_data or vulnerability_scan_results: {str(e)}"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    rollback_plan = request.data.get("rollback_plan", "")

    # Upload artifact to MinIO
    try:
        storage = get_storage()
        object_name = f"artifacts/{app_name}/{version}/{artifact_file.name}"
        artifact_path, artifact_hash = storage.upload_artifact(
            artifact_file, object_name, content_type=artifact_file.content_type or "application/octet-stream"
        )
    except Exception as e:
        logger.error(f"Failed to upload artifact to MinIO: {e}", extra={"correlation_id": request.correlation_id})
        return Response({"error": f"Failed to upload artifact: {str(e)}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # Validate evidence pack
    is_validated = _validate_evidence_pack(sbom_data, vulnerability_scan_results, rollback_plan)

    # Create evidence pack record
    evidence_pack = EvidencePack.objects.create(
        app_name=app_name,
        version=version,
        artifact_hash=artifact_hash,
        artifact_path=artifact_path,
        sbom_data=sbom_data,
        vulnerability_scan_results=vulnerability_scan_results,
        rollback_plan=rollback_plan,
        is_validated=is_validated,
        is_demo=get_demo_mode_enabled(),
    )

    logger.info(
        f"Evidence pack uploaded: {evidence_pack.correlation_id}",
        extra={
            "correlation_id": str(evidence_pack.correlation_id),
            "artifact_hash": artifact_hash,
            "is_validated": is_validated,
        },
    )

    return Response(
        {
            "correlation_id": str(evidence_pack.correlation_id),
            "artifact_hash": evidence_pack.artifact_hash,
            "artifact_path": evidence_pack.artifact_path,
            "is_validated": is_validated,
        },
        status=status.HTTP_201_CREATED,
    )


def _validate_evidence_pack(sbom_data: dict, vulnerability_scan_results: dict, rollback_plan: str) -> bool:
    """
    Validate evidence pack completeness.

    Args:
        sbom_data: SBOM data (SPDX or CycloneDX)
        vulnerability_scan_results: Vulnerability scan results
        rollback_plan: Rollback plan documentation

    Returns:
        True if evidence pack is complete and valid
    """
    # Check SBOM has required fields
    if not sbom_data or not sbom_data.get("packages"):
        logger.warning("SBOM missing or incomplete")
        return False

    # Check vulnerability scan has results
    if not vulnerability_scan_results:
        logger.warning("Vulnerability scan results missing")
        return False

    # Check rollback plan is not empty
    if not rollback_plan or len(rollback_plan.strip()) < 50:
        logger.warning("Rollback plan missing or too short")
        return False

    # Check for critical/high vulnerabilities
    critical_count = vulnerability_scan_results.get("critical", 0)
    high_count = vulnerability_scan_results.get("high", 0)

    if critical_count > 0:
        logger.warning(f"Evidence pack has {critical_count} critical vulnerabilities")
        return False

    if high_count > 5:  # Allow up to 5 high vulnerabilities with exceptions
        logger.warning(f"Evidence pack has {high_count} high vulnerabilities (threshold: 5)")
        return False

    return True


@api_view(["GET"])
@exempt_csrf_in_debug
@permission_classes([AllowAny if settings.DEBUG else IsAuthenticated])
def get_evidence_pack(request, correlation_id):
    """
    Get evidence pack details.

    GET /api/v1/evidence/{correlation_id}/
    """
    try:
        evidence_pack = apply_demo_filter(EvidencePack.objects.all(), request).get(correlation_id=correlation_id)
    except EvidencePack.DoesNotExist:
        return Response({"error": "Evidence pack not found"}, status=status.HTTP_404_NOT_FOUND)

    return Response(
        {
            "correlation_id": str(evidence_pack.correlation_id),
            "app_name": evidence_pack.app_name,
            "version": evidence_pack.version,
            "artifact_hash": evidence_pack.artifact_hash,
            "sbom_data": evidence_pack.sbom_data,
            "vulnerability_scan_results": evidence_pack.vulnerability_scan_results,
            "is_validated": evidence_pack.is_validated,
        }
    )
