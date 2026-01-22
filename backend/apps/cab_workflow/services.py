# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CAB Workflow Service - P5.2 Risk-based Approval Gates
Implements:
- Risk-based decision gates (auto-approve, manual review, exception required)
- Evidence linking and validation
- Approval workflow orchestration
"""
import uuid
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.db import transaction
from django.contrib.auth.models import User
from typing import Dict, Optional, Tuple, List

from .models import CABApprovalRequest, CABException, CABApprovalDecision
from apps.evidence_store.models import EvidencePackage
from apps.deployment_intents.models import DeploymentIntent


class CABWorkflowService:
    """
    Service for CAB approval workflow with risk-based gates.
    
    Risk-based decision tree:
    - risk_score ≤ 50: Auto-approve (no CAB needed)
    - 50 < risk_score ≤ 75: Manual CAB review required
    - risk_score > 75: Exception required with Security Reviewer approval
    """
    
    # Risk thresholds (from CLAUDE.md and architecture)
    AUTO_APPROVE_THRESHOLD = Decimal('50')
    MANUAL_REVIEW_THRESHOLD = Decimal('75')
    EXCEPTION_REQUIRED_THRESHOLD = Decimal('75')
    
    def __init__(self):
        """Initialize CAB workflow service."""
        pass
    
    @staticmethod
    def submit_for_approval(
        evidence_package_id: str,
        deployment_intent_id: str,
        risk_score: Decimal,
        submitted_by: User,
        notes: str = "",
        correlation_id: Optional[str] = None,
    ) -> Tuple[CABApprovalRequest, str]:
        """
        Submit evidence package for CAB approval.
        
        Implements risk-based gates:
        - ≤50: Auto-approved
        - 50-75: Submitted for manual review
        - >75: Requires exception (cannot auto-approve)
        
        Args:
            evidence_package_id: ID of evidence package
            deployment_intent_id: Deployment intent being approved
            risk_score: Computed risk score (0-100)
            submitted_by: User submitting for approval
            notes: Optional submission notes
            correlation_id: Optional custom correlation ID (generated if not provided)
        
        Returns:
            Tuple[CABApprovalRequest, decision_status]:
            - CABApprovalRequest: Created approval request
            - decision_status: 'auto_approved' | 'submitted' | 'exception_required'
        
        Raises:
            ValueError: If evidence package not found or invalid risk score
            DeploymentIntent.DoesNotExist: If deployment intent not found
        """
        # Validate inputs
        if not (Decimal('0') <= risk_score <= Decimal('100')):
            raise ValueError(f"Invalid risk score: {risk_score}. Must be 0-100.")
        
        # Verify evidence package exists
        try:
            evidence = EvidencePackage.objects.get(id=evidence_package_id)
        except EvidencePackage.DoesNotExist:
            raise ValueError(f"Evidence package not found: {evidence_package_id}")
        
        # Verify deployment intent exists
        deployment_intent = DeploymentIntent.objects.get(id=deployment_intent_id)
        
        # Generate correlation ID if not provided
        if not correlation_id:
            correlation_id = f"CAB-{uuid.uuid4().hex[:12].upper()}"
        
        # Determine initial status based on risk gates
        decision_status = CABWorkflowService.evaluate_risk_threshold(risk_score)
        
        initial_status = {
            'auto_approved': 'auto_approved',
            'manual_review': 'submitted',
            'exception_required': 'exception_required',
        }[decision_status]
        
        with transaction.atomic():
            # Create approval request
            cab_request = CABApprovalRequest.objects.create(
                deployment_intent_id=deployment_intent_id,
                correlation_id=correlation_id,
                evidence_package_id=evidence_package_id,
                risk_score=risk_score,
                submitted_by=submitted_by,
                status=initial_status,
                notes=notes,
            )
            
            # If auto-approved, immediately record decision
            if decision_status == 'auto_approved':
                CABApprovalDecision.objects.create(
                    cab_request_id=str(cab_request.id),
                    correlation_id=correlation_id,
                    decision='approved',
                    rationale=f'Auto-approved: Risk score {risk_score} ≤ {CABWorkflowService.AUTO_APPROVE_THRESHOLD}',
                    decided_by=submitted_by,
                    conditions={},
                )
                cab_request.status = 'auto_approved'
                cab_request.approved_by = submitted_by
                cab_request.approval_decision = 'approved'
                cab_request.approved_at = timezone.now()
                cab_request.save(update_fields=['status', 'approved_by', 'approval_decision', 'approved_at'])
        
        return cab_request, decision_status
    
    @staticmethod
    def evaluate_risk_threshold(risk_score: Decimal) -> str:
        """
        Evaluate risk score and determine approval gate.
        
        Args:
            risk_score: Risk score 0-100
        
        Returns:
            'auto_approved' | 'manual_review' | 'exception_required'
        """
        if risk_score <= CABWorkflowService.AUTO_APPROVE_THRESHOLD:
            return 'auto_approved'
        elif risk_score <= CABWorkflowService.MANUAL_REVIEW_THRESHOLD:
            return 'manual_review'
        else:
            return 'exception_required'
    
    @staticmethod
    def approve_request(
        cab_request_id: str,
        approver: User,
        rationale: str = "",
        conditions: Optional[Dict] = None,
    ) -> CABApprovalRequest:
        """
        Approve CAB request by authorized approver.
        
        Args:
            cab_request_id: ID of CABApprovalRequest
            approver: User approving the request
            rationale: Approval rationale
            conditions: Optional conditions if conditionally approved
        
        Returns:
            Updated CABApprovalRequest
        
        Raises:
            CABApprovalRequest.DoesNotExist: If request not found
            ValueError: If request cannot be approved (already decided, auto-approved, etc.)
        """
        try:
            cab_request = CABApprovalRequest.objects.get(id=cab_request_id)
        except CABApprovalRequest.DoesNotExist:
            raise ValueError(f"CAB request not found: {cab_request_id}")
        
        # Only submissions and under_review can be approved
        if cab_request.status not in ['submitted', 'under_review']:
            raise ValueError(
                f"Cannot approve request with status '{cab_request.status}'. "
                f"Only 'submitted' or 'under_review' requests can be approved."
            )
        
        with transaction.atomic():
            # Update request
            cab_request.status = 'approved'
            cab_request.approved_by = approver
            cab_request.approval_decision = 'approved'
            cab_request.approval_rationale = rationale
            cab_request.approval_conditions = conditions or {}
            cab_request.approved_at = timezone.now()
            cab_request.save()
            
            # Record immutable decision
            CABApprovalDecision.objects.create(
                cab_request_id=str(cab_request.id),
                correlation_id=cab_request.correlation_id,
                decision='approved',
                rationale=rationale or 'Approved by CAB member',
                decided_by=approver,
                conditions=conditions or {},
            )
        
        return cab_request
    
    @staticmethod
    def reject_request(
        cab_request_id: str,
        rejector: User,
        rationale: str = "",
    ) -> CABApprovalRequest:
        """
        Reject CAB request.
        
        Args:
            cab_request_id: ID of CABApprovalRequest
            rejector: User rejecting the request
            rationale: Rejection rationale
        
        Returns:
            Updated CABApprovalRequest
        
        Raises:
            CABApprovalRequest.DoesNotExist: If request not found
            ValueError: If request cannot be rejected
        """
        try:
            cab_request = CABApprovalRequest.objects.get(id=cab_request_id)
        except CABApprovalRequest.DoesNotExist:
            raise ValueError(f"CAB request not found: {cab_request_id}")
        
        # Only submissions and under_review can be rejected
        if cab_request.status not in ['submitted', 'under_review']:
            raise ValueError(
                f"Cannot reject request with status '{cab_request.status}'. "
                f"Only 'submitted' or 'under_review' requests can be rejected."
            )
        
        with transaction.atomic():
            # Update request
            cab_request.status = 'rejected'
            cab_request.approved_by = rejector
            cab_request.approval_decision = 'rejected'
            cab_request.approval_rationale = rationale
            cab_request.approved_at = timezone.now()
            cab_request.save()
            
            # Record immutable decision
            CABApprovalDecision.objects.create(
                cab_request_id=str(cab_request.id),
                correlation_id=cab_request.correlation_id,
                decision='rejected',
                rationale=rationale or 'Rejected by CAB member',
                decided_by=rejector,
                conditions={},
            )
        
        return cab_request
    
    @staticmethod
    def create_exception(
        deployment_intent_id: str,
        requested_by: User,
        reason: str,
        risk_justification: str,
        compensating_controls: List[str],
        expiry_days: int = 30,
        correlation_id: Optional[str] = None,
    ) -> CABException:
        """
        Create exception for high-risk deployment (risk > 75).
        
        Mandatory expiry date enforced (no permanent exceptions).
        Requires Security Reviewer approval before exception becomes active.
        
        Args:
            deployment_intent_id: What the exception applies to
            requested_by: User requesting exception
            reason: Why exception is needed
            risk_justification: Why risk is acceptable despite threshold
            compensating_controls: List of compensating controls (e.g., monitoring, rollback plan)
            expiry_days: Days until exception expires (default 30, max 90)
            correlation_id: Optional custom correlation ID
        
        Returns:
            Created CABException (status='pending' until approved)
        
        Raises:
            ValueError: If expiry_days > 90 (prevents permanent exceptions)
        """
        if expiry_days > 90:
            raise ValueError("Exception expiry cannot exceed 90 days")
        if expiry_days < 1:
            raise ValueError("Exception expiry must be at least 1 day")
        
        if not correlation_id:
            correlation_id = f"EXC-{uuid.uuid4().hex[:12].upper()}"
        
        expires_at = timezone.now() + timedelta(days=expiry_days)
        
        exception = CABException.objects.create(
            deployment_intent_id=deployment_intent_id,
            correlation_id=correlation_id,
            reason=reason,
            risk_justification=risk_justification,
            compensating_controls=compensating_controls,
            requested_by=requested_by,
            expires_at=expires_at,
            status='pending',
        )
        
        return exception
    
    @staticmethod
    def approve_exception(
        exception_id: str,
        approver: User,
        rationale: str = "",
    ) -> CABException:
        """
        Approve exception (by Security Reviewer).
        
        Args:
            exception_id: ID of CABException
            approver: User approving (should be Security Reviewer)
            rationale: Approval rationale
        
        Returns:
            Updated CABException
        
        Raises:
            CABException.DoesNotExist: If exception not found
            ValueError: If exception cannot be approved
        """
        try:
            exception = CABException.objects.get(id=exception_id)
        except CABException.DoesNotExist:
            raise ValueError(f"Exception not found: {exception_id}")
        
        if exception.status != 'pending':
            raise ValueError(f"Cannot approve exception with status '{exception.status}'")
        
        if timezone.now() > exception.expires_at:
            exception.status = 'expired'
            exception.save(update_fields=['status'])
            raise ValueError("Exception has already expired")
        
        exception.status = 'approved'
        exception.approved_by = approver
        exception.approval_decision = 'approved'
        exception.approval_rationale = rationale
        exception.approved_at = timezone.now()
        exception.save()
        
        return exception
    
    @staticmethod
    def reject_exception(
        exception_id: str,
        rejector: User,
        rationale: str = "",
    ) -> CABException:
        """
        Reject exception (by Security Reviewer).
        
        Args:
            exception_id: ID of CABException
            rejector: User rejecting (should be Security Reviewer)
            rationale: Rejection rationale
        
        Returns:
            Updated CABException
        
        Raises:
            CABException.DoesNotExist: If exception not found
            ValueError: If exception cannot be rejected
        """
        try:
            exception = CABException.objects.get(id=exception_id)
        except CABException.DoesNotExist:
            raise ValueError(f"Exception not found: {exception_id}")
        
        if exception.status != 'pending':
            raise ValueError(f"Cannot reject exception with status '{exception.status}'")
        
        exception.status = 'rejected'
        exception.approved_by = rejector
        exception.approval_decision = 'rejected'
        exception.approval_rationale = rationale
        exception.approved_at = timezone.now()
        exception.save()
        
        return exception
    
    @staticmethod
    def get_pending_exceptions() -> List[CABException]:
        """Get all pending exceptions awaiting Security Reviewer approval."""
        return CABException.objects.filter(status='pending').order_by('expires_at')
    
    @staticmethod
    def get_pending_requests() -> List[CABApprovalRequest]:
        """Get all pending CAB requests awaiting review."""
        return CABApprovalRequest.objects.filter(status='submitted').order_by('-submitted_at')
    
    @staticmethod
    def get_requests_by_deployment(deployment_intent_id: str) -> List[CABApprovalRequest]:
        """Get all CAB requests for a deployment intent."""
        return CABApprovalRequest.objects.filter(
            deployment_intent_id=deployment_intent_id
        ).order_by('-submitted_at')
    
    @staticmethod
    def get_decisions_for_request(cab_request_id: str) -> List[CABApprovalDecision]:
        """Get all decisions for a CAB request (should be 1, immutable)."""
        return CABApprovalDecision.objects.filter(
            cab_request_id=cab_request_id
        ).order_by('-decided_at')
    
    @staticmethod
    def get_active_exceptions_for_deployment(deployment_intent_id: str) -> List[CABException]:
        """Get active (approved, non-expired) exceptions for deployment."""
        now = timezone.now()
        return CABException.objects.filter(
            deployment_intent_id=deployment_intent_id,
            status='approved',
            expires_at__gt=now,
        ).order_by('-approved_at')
    
    @staticmethod
    def cleanup_expired_exceptions() -> int:
        """Mark all expired exceptions as 'expired'. Returns count updated."""
        now = timezone.now()
        expired = CABException.objects.filter(
            expires_at__lte=now,
            status__in=['pending', 'approved'],
        )
        count = expired.update(status='expired')
        return count
    
    @staticmethod
    def get_approval_status(deployment_intent_id: str) -> Dict:
        """
        Get comprehensive approval status for deployment intent.
        
        Returns dict with:
        - requests: All CAB approval requests
        - latest_request: Most recent request
        - decision: Latest decision (if any)
        - exceptions: Active exceptions
        - is_approved: Whether deployment is approved (auto or manual)
        - requires_exception: Whether deployment requires valid exception
        """
        requests = CABApprovalRequest.objects.filter(
            deployment_intent_id=deployment_intent_id
        ).order_by('-submitted_at')
        
        latest_request = requests.first()
        
        latest_decision = None
        if latest_request:
            latest_decision = CABApprovalDecision.objects.filter(
                cab_request_id=str(latest_request.id)
            ).first()
        
        exceptions = CABWorkflowService.get_active_exceptions_for_deployment(deployment_intent_id)
        
        is_approved = (
            latest_request and 
            latest_request.status in ['auto_approved', 'approved']
        )
        
        requires_exception = (
            latest_request and
            latest_request.status == 'exception_required'
        )
        
        return {
            'deployment_intent_id': deployment_intent_id,
            'requests': requests,
            'latest_request': latest_request,
            'decision': latest_decision,
            'exceptions': exceptions,
            'is_approved': is_approved,
            'requires_exception': requires_exception,
            'latest_status': latest_request.status if latest_request else None,
        }
