# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CAB (Change Advisory Board) Workflow Models for P5
"""
import uuid
from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class CABApprovalRequest(models.Model):
    """
    CAB approval request submitted with evidence package.
    Links evidence package to approval workflow.
    """
    
    STATUS_CHOICES = [
        ('submitted', 'Submitted for Review'),
        ('under_review', 'Under CAB Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('conditional', 'Conditionally Approved'),
        ('exception_required', 'Exception Required (Risk > 75)'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    deployment_intent_id = models.CharField(
        max_length=255,
        help_text="Correlation to deployment intent"
    )
    correlation_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique identifier for audit trail"
    )
    
    # Evidence Reference
    evidence_package_id = models.CharField(
        max_length=255,
        help_text="ID of associated evidence package"
    )
    risk_score = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Risk score from evidence package"
    )
    
    # Submission
    submitted_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='cab_submissions'
    )
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    # Status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='submitted'
    )
    
    # Approval (if applicable)
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='cab_approvals'
    )
    approval_decision = models.CharField(
        max_length=50,
        choices=[
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('conditional', 'Conditionally Approved'),
        ],
        null=True,
        blank=True
    )
    approval_rationale = models.TextField(
        blank=True,
        help_text="Reason for approval/rejection decision"
    )
    approval_conditions = models.JSONField(
        default=dict,
        help_text="Conditions if conditionally approved"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Metadata
    notes = models.TextField(
        blank=True,
        help_text="Additional notes from submitter"
    )
    
    class Meta:
        db_table = 'cab_workflow_cabaprovalrequest'
        ordering = ['-submitted_at']
        verbose_name = 'CAB Approval Request'
        verbose_name_plural = 'CAB Approval Requests'
        indexes = [
            models.Index(fields=['deployment_intent_id', '-submitted_at']),
            models.Index(fields=['status']),
            models.Index(fields=['risk_score']),
        ]
    
    def __str__(self):
        return f"CAB {self.id} for {self.deployment_intent_id} ({self.status})"
    
    @property
    def auto_approve_threshold(self) -> bool:
        """True if risk score ≤ 50 (auto-approve)."""
        return float(self.risk_score) <= 50
    
    @property
    def manual_review_required(self) -> bool:
        """True if risk score 50-75 (manual review)."""
        return 50 < float(self.risk_score) <= 75
    
    @property
    def exception_required(self) -> bool:
        """True if risk score > 75 (exception required)."""
        return float(self.risk_score) > 75


class CABException(models.Model):
    """
    Exception to standard CAB gates.
    Used when risk score > 75 or other policy violations.
    Requires Security Reviewer approval.
    """
    
    STATUS_CHOICES = [
        ('pending', 'Pending Security Review'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('expired', 'Expired'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    deployment_intent_id = models.CharField(
        max_length=255,
        help_text="What exception applies to"
    )
    correlation_id = models.CharField(
        max_length=255,
        unique=True,
        help_text="Unique identifier for audit trail"
    )
    
    # Exception Details
    reason = models.TextField(
        help_text="Why exception is needed"
    )
    risk_justification = models.TextField(
        help_text="Why risk is acceptable despite threshold"
    )
    compensating_controls = models.JSONField(
        default=list,
        help_text="List of compensating controls (e.g., ['Additional monitoring', 'Rollback plan'])"
    )
    
    # Approval Workflow
    requested_by = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='exception_requests'
    )
    requested_at = models.DateTimeField(auto_now_add=True)
    
    # Security Reviewer approval required
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='exception_approvals',
        help_text="Security Reviewer who approved"
    )
    approval_decision = models.CharField(
        max_length=50,
        choices=[
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
        ],
        null=True,
        blank=True
    )
    approval_rationale = models.TextField(
        blank=True,
        help_text="Security Reviewer rationale"
    )
    approved_at = models.DateTimeField(
        null=True,
        blank=True
    )
    
    # Expiry (mandatory)
    expires_at = models.DateTimeField(
        help_text="Exception automatically expires (no permanent exceptions)"
    )
    
    # Status
    status = models.CharField(
        max_length=50,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    class Meta:
        db_table = 'cab_workflow_cabexception'
        ordering = ['-requested_at']
        verbose_name = 'CAB Exception'
        verbose_name_plural = 'CAB Exceptions'
        indexes = [
            models.Index(fields=['deployment_intent_id', '-requested_at']),
            models.Index(fields=['status', 'expires_at']),
        ]
    
    def __str__(self):
        return f"Exception {self.id} for {self.deployment_intent_id} ({self.status})"
    
    @property
    def is_active(self) -> bool:
        """Exception is active if approved and not expired."""
        now = timezone.now()
        return (
            self.status == 'approved' and
            self.approved_at is not None and
            self.expires_at > now
        )
    
    @property
    def is_expired(self) -> bool:
        """Exception has expired."""
        return timezone.now() > self.expires_at


class CABApprovalDecision(models.Model):
    """
    Immutable record of CAB approval decision.
    Stored in event store for audit trail.
    """
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    approval_request = models.OneToOneField(
        CABApprovalRequest,
        on_delete=models.CASCADE,
        related_name='decision'
    )
    correlation_id = models.CharField(
        max_length=255,
        help_text="Links to deployment intent audit trail"
    )
    
    # Decision
    decision = models.CharField(
        max_length=50,
        choices=[
            ('approved', 'Approved'),
            ('rejected', 'Rejected'),
            ('conditional', 'Conditionally Approved'),
            ('auto_approved', 'Auto-Approved (Risk ≤ 50)'),
        ]
    )
    
    # Evidence
    decision_maker = models.ForeignKey(
        User,
        on_delete=models.PROTECT,
        related_name='cab_decisions'
    )
    decision_rationale = models.TextField(
        help_text="Why this decision was made"
    )
    risk_score_at_decision = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        help_text="Risk score at time of decision"
    )
    
    # Metadata
    decided_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        db_table = 'cab_workflow_cabapprovaldecision'
        ordering = ['-decided_at']
        verbose_name = 'CAB Approval Decision'
        verbose_name_plural = 'CAB Approval Decisions'
        indexes = [
            models.Index(fields=['correlation_id']),
            models.Index(fields=['decision']),
        ]
    
    def __str__(self):
        return f"{self.decision} for {self.correlation_id}"


# ============================================================================
# Service Module (CAB Workflow)
# ============================================================================

class CABWorkflowService:
    """
    Service for managing CAB approval workflow.
    Implements P5.3-P5.4: CAB submission and approval.
    """
    
    @staticmethod
    def submit_for_approval(
        deployment_intent_id: str,
        correlation_id: str,
        evidence_package_id: str,
        risk_score: float,
        submitted_by: User,
        notes: str = "",
    ) -> CABApprovalRequest:
        """
        Submit deployment for CAB approval.
        
        Args:
            deployment_intent_id: ID of deployment
            correlation_id: Unique identifier
            evidence_package_id: Associated evidence package
            risk_score: Computed risk score (0-100)
            submitted_by: User submitting
            notes: Optional notes
        
        Returns:
            CABApprovalRequest: Created approval request
        
        Raises:
            ValueError: If evidence incomplete
        """
        
        # TODO: Validate evidence package completeness
        # if not evidence_package.is_complete:
        #     raise ValueError("Evidence package incomplete")
        
        request = CABApprovalRequest.objects.create(
            deployment_intent_id=deployment_intent_id,
            correlation_id=correlation_id,
            evidence_package_id=evidence_package_id,
            risk_score=risk_score,
            submitted_by=submitted_by,
            status='submitted',
            notes=notes,
        )
        
        # Auto-approve if risk score ≤ 50
        if request.auto_approve_threshold:
            CABWorkflowService._auto_approve(request)
        
        return request
    
    @staticmethod
    def _auto_approve(approval_request: CABApprovalRequest) -> None:
        """Auto-approve request with risk score ≤ 50."""
        approval_request.status = 'approved'
        approval_request.approval_decision = 'approved'
        approval_request.approval_rationale = f"Auto-approved: Risk score {approval_request.risk_score} ≤ 50"
        approval_request.approved_at = timezone.now()
        approval_request.approved_by = None  # System approval
        approval_request.save()
        
        # Record decision in event store (via CABApprovalDecision)
        CABApprovalDecision.objects.create(
            approval_request=approval_request,
            correlation_id=approval_request.correlation_id,
            decision='auto_approved',
            decision_maker=None,  # Would need system user
            decision_rationale=f"Automatic approval: risk score {approval_request.risk_score}",
            risk_score_at_decision=approval_request.risk_score,
        )
    
    @staticmethod
    def approve_request(
        approval_request: CABApprovalRequest,
        decision: str,  # 'approved', 'rejected', 'conditional'
        approved_by: User,
        rationale: str,
        conditions: dict = None,
    ) -> CABApprovalDecision:
        """
        Record CAB member approval decision.
        
        Args:
            approval_request: Request being decided on
            decision: 'approved', 'rejected', or 'conditional'
            approved_by: CAB member making decision
            rationale: Justification for decision
            conditions: Conditions if conditional approval
        
        Returns:
            CABApprovalDecision: Immutable decision record
        """
        
        # Update request
        approval_request.status = decision if decision != 'conditional' else 'conditional'
        approval_request.approval_decision = decision
        approval_request.approval_rationale = rationale
        approval_request.approved_by = approved_by
        approval_request.approved_at = timezone.now()
        
        if conditions:
            approval_request.approval_conditions = conditions
        
        approval_request.save()
        
        # Record decision in immutable event store
        decision_record = CABApprovalDecision.objects.create(
            approval_request=approval_request,
            correlation_id=approval_request.correlation_id,
            decision=decision,
            decision_maker=approved_by,
            decision_rationale=rationale,
            risk_score_at_decision=approval_request.risk_score,
        )
        
        return decision_record
    
    @staticmethod
    def request_exception(
        deployment_intent_id: str,
        correlation_id: str,
        reason: str,
        risk_justification: str,
        compensating_controls: list,
        expires_in_days: int,
        requested_by: User,
    ) -> CABException:
        """
        Request exception to CAB gates.
        Requires Security Reviewer approval.
        
        Args:
            deployment_intent_id: What exception applies to
            correlation_id: Unique ID
            reason: Why exception needed
            risk_justification: Why risk acceptable
            compensating_controls: Mitigating controls
            expires_in_days: Days until auto-expiry (max 30)
            requested_by: User requesting
        
        Returns:
            CABException: Created exception request
        """
        
        expires_at = timezone.now() + timezone.timedelta(days=min(expires_in_days, 30))
        
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
