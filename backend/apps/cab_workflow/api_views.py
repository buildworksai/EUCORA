# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
P5.3: CAB Submission REST API Views
Provides endpoints for CAB approval workflow submission, review, and exception management.
"""
import logging
import uuid

from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.cab_workflow.models import CABApprovalDecision, CABApprovalRequest, CABException
from apps.cab_workflow.services import CABWorkflowService
from apps.deployment_intents.models import DeploymentIntent
from apps.evidence_store.models import EvidencePackage

from .serializers import (
    CABApprovalActionSerializer,
    CABApprovalDecisionSerializer,
    CABApprovalRequestDetailSerializer,
    CABApprovalRequestListSerializer,
    CABApprovalSubmitSerializer,
    CABExceptionApprovalSerializer,
    CABExceptionCreateSerializer,
    CABExceptionDetailSerializer,
    CABExceptionListSerializer,
)

logger = logging.getLogger(__name__)


# ============================================================================
# CAB Approval Request Endpoints
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def submit_cab_approval(request):
    """
    Submit evidence package for CAB approval.

    POST /api/v1/cab/submit/

    Body:
    {
        "evidence_package_id": "...",
        "risk_score": 65.5,
        "notes": "Deployment ready for review"
    }

    Returns:
    {
        "id": "...",
        "correlation_id": "CAB-...",
        "status": "submitted|auto_approved|exception_required",
        "risk_tier": {"tier": "MEDIUM", "description": "..."},
        "message": "..."
    }
    """
    serializer = CABApprovalSubmitSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    evidence_package_id = serializer.validated_data["evidence_package_id"]
    risk_score = serializer.validated_data["risk_score"]
    notes = serializer.validated_data.get("notes", "")

    # Validate evidence package exists
    try:
        evidence = EvidencePackage.objects.get(id=evidence_package_id)
    except EvidencePackage.DoesNotExist:
        return Response(
            {"error": f"Evidence package not found: {evidence_package_id}"}, status=status.HTTP_404_NOT_FOUND
        )
    except (ValueError, DjangoValidationError):
        # Invalid UUID format
        return Response(
            {"error": f"Evidence package not found: {evidence_package_id}"}, status=status.HTTP_404_NOT_FOUND
        )

    try:
        # Submit for approval using service
        cab_request, decision_status = CABWorkflowService.submit_for_approval(
            evidence_package_id=evidence_package_id,
            deployment_intent_id=str(evidence.deployment_intent_id),
            risk_score=risk_score,
            submitted_by=request.user,
            notes=notes,
        )

        # Determine message based on decision status
        messages = {
            "auto_approved": "Deployment auto-approved (low risk)",
            "manual_review": "Deployment submitted for CAB review",
            "exception_required": "Deployment flagged as high-risk, exception required",
        }

        serializer = CABApprovalRequestDetailSerializer(cab_request)
        return Response(
            {
                **serializer.data,
                "message": messages.get(decision_status, "Submitted for review"),
                "decision_status": decision_status,
            },
            status=status.HTTP_201_CREATED,
        )

    except ValueError as e:
        logger.warning(f"Invalid submission: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error submitting CAB request: {e}", exc_info=True)
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cab_request(request, cab_request_id):
    """
    Retrieve CAB approval request details.

    GET /api/v1/cab/{cab_request_id}/

    Returns detailed CAB request information including approval status and decisions.
    """
    try:
        cab_request = CABApprovalRequest.objects.get(id=cab_request_id)
    except CABApprovalRequest.DoesNotExist:
        return Response({"error": "CAB request not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check authorization (requester or CAB member or staff)
    if (
        cab_request.submitted_by != request.user
        and not request.user.is_staff
        and not request.user.groups.filter(name__in=["cab_member", "security_reviewer"]).exists()
    ):
        return Response({"error": "Not authorized to view this request"}, status=status.HTTP_403_FORBIDDEN)

    serializer = CABApprovalRequestDetailSerializer(cab_request)

    # Add decision information if available
    decision = CABApprovalDecision.objects.filter(cab_request_id=str(cab_request.id)).first()

    response_data = serializer.data.copy()
    if decision:
        decision_serializer = CABApprovalDecisionSerializer(decision)
        response_data["decision"] = decision_serializer.data

    return Response(response_data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_all_cab_requests(request):
    """
    List all CAB approval requests (API coverage endpoint).

    GET /api/v1/cab/

    Query params:
    - status: Filter by status
    - risk_min: Minimum risk score
    - risk_max: Maximum risk score

    Returns paginated list of all requests.
    """
    queryset = CABApprovalRequest.objects.all()

    # Filter by status if provided
    filter_status = request.query_params.get("status")
    if filter_status:
        queryset = queryset.filter(status=filter_status)

    # Filter by risk score range
    risk_min = request.query_params.get("risk_min")
    risk_max = request.query_params.get("risk_max")

    if risk_min:
        try:
            queryset = queryset.filter(risk_score__gte=float(risk_min))
        except ValueError:
            pass

    if risk_max:
        try:
            queryset = queryset.filter(risk_score__lte=float(risk_max))
        except ValueError:
            pass

    queryset = queryset.order_by("-submitted_at")

    serializer = CABApprovalRequestListSerializer(queryset, many=True)
    return Response({"count": queryset.count(), "results": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_pending_cab_requests(request):
    """
    List pending CAB approval requests.

    GET /api/v1/cab/pending/

    Query params:
    - status: Filter by status (submitted, under_review)
    - risk_min: Minimum risk score
    - risk_max: Maximum risk score

    Returns paginated list of pending requests.
    """
    queryset = CABApprovalRequest.objects.filter(status__in=["submitted", "under_review"])

    # Filter by status if provided
    filter_status = request.query_params.get("status")
    if filter_status in ["submitted", "under_review"]:
        queryset = queryset.filter(status=filter_status)

    # Filter by risk score range
    risk_min = request.query_params.get("risk_min")
    risk_max = request.query_params.get("risk_max")

    if risk_min:
        try:
            queryset = queryset.filter(risk_score__gte=float(risk_min))
        except ValueError:
            pass

    if risk_max:
        try:
            queryset = queryset.filter(risk_score__lte=float(risk_max))
        except ValueError:
            pass

    queryset = queryset.order_by("-submitted_at")

    serializer = CABApprovalRequestListSerializer(queryset, many=True)
    return Response({"count": queryset.count(), "results": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_my_cab_requests(request):
    """
    List CAB requests submitted by current user.

    GET /api/v1/cab/my-requests/

    Returns list of requests submitted by authenticated user.
    """
    queryset = CABApprovalRequest.objects.filter(submitted_by=request.user).order_by("-submitted_at")

    serializer = CABApprovalRequestListSerializer(queryset, many=True)
    return Response({"count": queryset.count(), "results": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def approve_cab_request(request, cab_request_id):
    """
    Approve CAB approval request (CAB member action).

    POST /api/v1/cab/{cab_request_id}/approve/

    Body:
    {
        "rationale": "Risk assessment complete, deployable",
        "conditions": {"max_rollout_pct": 5, "monitoring_required": true}
    }

    Returns updated CAB request with approval decision.
    """
    try:
        cab_request = CABApprovalRequest.objects.get(id=cab_request_id)
    except CABApprovalRequest.DoesNotExist:
        return Response({"error": "CAB request not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check authorization (CAB member or staff)
    if not (request.user.is_staff or request.user.groups.filter(name="cab_member").exists()):
        return Response({"error": "Not authorized (CAB member access required)"}, status=status.HTTP_403_FORBIDDEN)

    serializer = CABApprovalActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        updated_request = CABWorkflowService.approve_request(
            cab_request_id=str(cab_request.id),
            approver=request.user,
            rationale=serializer.validated_data["rationale"],
            conditions=serializer.validated_data.get("conditions", {}),
        )

        response_serializer = CABApprovalRequestDetailSerializer(updated_request)
        return Response(
            {**response_serializer.data, "message": "CAB request approved successfully"}, status=status.HTTP_200_OK
        )

    except ValueError as e:
        logger.warning(f"Cannot approve request: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error approving CAB request: {e}", exc_info=True)
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def reject_cab_request(request, cab_request_id):
    """
    Reject CAB approval request (CAB member action).

    POST /api/v1/cab/{cab_request_id}/reject/

    Body:
    {
        "rationale": "Risk assessment incomplete, needs more testing"
    }

    Returns updated CAB request with rejection decision.
    """
    try:
        cab_request = CABApprovalRequest.objects.get(id=cab_request_id)
    except CABApprovalRequest.DoesNotExist:
        return Response({"error": "CAB request not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check authorization (CAB member or staff)
    if not (request.user.is_staff or request.user.groups.filter(name="cab_member").exists()):
        return Response({"error": "Not authorized (CAB member access required)"}, status=status.HTTP_403_FORBIDDEN)

    serializer = CABApprovalActionSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        updated_request = CABWorkflowService.reject_request(
            cab_request_id=str(cab_request.id),
            rejector=request.user,
            rationale=serializer.validated_data["rationale"],
        )

        response_serializer = CABApprovalRequestDetailSerializer(updated_request)
        return Response(
            {**response_serializer.data, "message": "CAB request rejected successfully"}, status=status.HTTP_200_OK
        )

    except ValueError as e:
        logger.warning(f"Cannot reject request: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error rejecting CAB request: {e}", exc_info=True)
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ============================================================================
# CAB Exception Endpoints
# ============================================================================


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def create_cab_exception(request):
    """
    Create CAB exception for high-risk deployment.

    POST /api/v1/cab/exceptions/

    Body:
    {
        "deployment_intent_id": "...",
        "reason": "Urgent security patch",
        "risk_justification": "Risk acceptable with monitoring",
        "compensating_controls": ["24/7 monitoring", "Quick rollback plan"],
        "expiry_days": 30
    }

    Returns created exception (pending approval).
    """
    serializer = CABExceptionCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        exception = CABWorkflowService.create_exception(
            deployment_intent_id=serializer.validated_data["deployment_intent_id"],
            requested_by=request.user,
            reason=serializer.validated_data["reason"],
            risk_justification=serializer.validated_data["risk_justification"],
            compensating_controls=serializer.validated_data["compensating_controls"],
            expiry_days=serializer.validated_data.get("expiry_days", 30),
        )

        response_serializer = CABExceptionDetailSerializer(exception)
        return Response(
            {**response_serializer.data, "message": "Exception created, pending Security Reviewer approval"},
            status=status.HTTP_201_CREATED,
        )

    except ValueError as e:
        logger.warning(f"Invalid exception: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error creating exception: {e}", exc_info=True)
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def get_cab_exception(request, exception_id):
    """
    Retrieve CAB exception details.

    GET /api/v1/cab/exceptions/{exception_id}/

    Returns detailed exception information.
    """
    try:
        exception = CABException.objects.get(id=exception_id)
    except CABException.DoesNotExist:
        return Response({"error": "Exception not found"}, status=status.HTTP_404_NOT_FOUND)

    serializer = CABExceptionDetailSerializer(exception)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_pending_exceptions(request):
    """
    List pending CAB exceptions awaiting Security Reviewer approval.

    GET /api/v1/cab/exceptions/pending/

    Returns list of pending exceptions.
    """
    queryset = CABException.objects.filter(status="pending").order_by("-requested_at")

    serializer = CABExceptionListSerializer(queryset, many=True)
    return Response({"count": queryset.count(), "results": serializer.data})


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def list_my_exceptions(request):
    """
    List exceptions requested by current user.

    GET /api/v1/cab/exceptions/my-exceptions/

    Returns list of exceptions requested by authenticated user.
    """
    queryset = CABException.objects.filter(requested_by=request.user).order_by("-requested_at")

    serializer = CABExceptionListSerializer(queryset, many=True)
    return Response({"count": queryset.count(), "results": serializer.data})


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def approve_exception(request, exception_id):
    """
    Approve CAB exception (Security Reviewer action).

    POST /api/v1/cab/exceptions/{exception_id}/approve/

    Body:
    {
        "rationale": "Compensating controls sufficient"
    }

    Returns updated exception with approval.
    """
    try:
        exception = CABException.objects.get(id=exception_id)
    except CABException.DoesNotExist:
        return Response({"error": "Exception not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check authorization (Security Reviewer or staff)
    if not (request.user.is_staff or request.user.groups.filter(name="security_reviewer").exists()):
        return Response(
            {"error": "Not authorized (Security Reviewer access required)"}, status=status.HTTP_403_FORBIDDEN
        )

    serializer = CABExceptionApprovalSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        updated_exception = CABWorkflowService.approve_exception(
            exception_id=str(exception.id),
            approver=request.user,
            rationale=serializer.validated_data["rationale"],
        )

        response_serializer = CABExceptionDetailSerializer(updated_exception)
        return Response(
            {**response_serializer.data, "message": "Exception approved successfully"}, status=status.HTTP_200_OK
        )

    except ValueError as e:
        logger.warning(f"Cannot approve exception: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error approving exception: {e}", exc_info=True)
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
@transaction.atomic
def reject_exception(request, exception_id):
    """
    Reject CAB exception (Security Reviewer action).

    POST /api/v1/cab/exceptions/{exception_id}/reject/

    Body:
    {
        "rationale": "Compensating controls insufficient"
    }

    Returns updated exception with rejection.
    """
    try:
        exception = CABException.objects.get(id=exception_id)
    except CABException.DoesNotExist:
        return Response({"error": "Exception not found"}, status=status.HTTP_404_NOT_FOUND)

    # Check authorization (Security Reviewer or staff)
    if not (request.user.is_staff or request.user.groups.filter(name="security_reviewer").exists()):
        return Response(
            {"error": "Not authorized (Security Reviewer access required)"}, status=status.HTTP_403_FORBIDDEN
        )

    serializer = CABExceptionApprovalSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    try:
        updated_exception = CABWorkflowService.reject_exception(
            exception_id=str(exception.id),
            rejector=request.user,
            rationale=serializer.validated_data["rationale"],
        )

        response_serializer = CABExceptionDetailSerializer(updated_exception)
        return Response(
            {**response_serializer.data, "message": "Exception rejected successfully"}, status=status.HTTP_200_OK
        )

    except ValueError as e:
        logger.warning(f"Cannot reject exception: {e}")
        return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        logger.error(f"Error rejecting exception: {e}", exc_info=True)
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def cleanup_expired_exceptions(request):
    """
    Cleanup expired exceptions (admin action).

    POST /api/v1/cab/exceptions/cleanup/

    Returns count of exceptions marked as expired.
    """
    # Check authorization (staff only)
    if not request.user.is_staff:
        return Response({"error": "Not authorized (admin access required)"}, status=status.HTTP_403_FORBIDDEN)

    try:
        count = CABWorkflowService.cleanup_expired_exceptions()
        return Response({"message": f"Cleaned up {count} expired exceptions", "count": count})
    except Exception as e:
        logger.error(f"Error cleaning up exceptions: {e}", exc_info=True)
        return Response({"error": "Internal server error"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
