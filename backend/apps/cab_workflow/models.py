# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CAB Workflow models for approval workflows.
"""
import uuid

from django.contrib.auth.models import User
from django.db import models
from django.utils import timezone

from apps.core.models import DemoQuerySet, TimeStampedModel
from apps.deployment_intents.models import DeploymentIntent


class CABApproval(TimeStampedModel):
    """
    CAB approval record for deployment intent.
    """

    class Decision(models.TextChoices):
        PENDING = "PENDING", "Pending"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"
        CONDITIONAL = "CONDITIONAL", "Conditional"

    deployment_intent = models.OneToOneField(DeploymentIntent, on_delete=models.CASCADE, related_name="cab_approval")
    decision = models.CharField(max_length=20, choices=Decision.choices, default=Decision.PENDING)
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="cab_approvals")
    comments = models.TextField(blank=True, help_text="Approval/rejection comments")
    conditions = models.JSONField(default=list, help_text="Conditional approval conditions")
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    external_change_request_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text="External change request ID (ServiceNow CR, Jira issue key, etc.)",
    )
    is_demo = models.BooleanField(default=False, db_index=True, help_text="Whether this is demo data")

    objects = DemoQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["decision", "created_at"]),
            models.Index(fields=["approver", "created_at"]),
            models.Index(fields=["deployment_intent"]),
        ]
        verbose_name = "CAB Approval"
        verbose_name_plural = "CAB Approvals"

    def __str__(self):
        return f"CAB Approval for {self.deployment_intent.app_name} - {self.decision}"


# ============================================================================
# Phase P5.2+: CAB Approval Workflow with Risk-based Gates
# ============================================================================


class CABApprovalRequest(models.Model):
    """
    CAB approval request submitted with evidence package.
    Links evidence package to approval workflow with risk-based gates.

    Risk Gates:
    - ≤50: Auto-approve
    - 50-75: Manual CAB review required
    - >75: Exception required from Security Reviewer
    """

    STATUS_CHOICES = [
        ("submitted", "Submitted for Review"),
        ("auto_approved", "Auto-Approved (Low Risk)"),
        ("under_review", "Under CAB Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("conditional", "Conditionally Approved"),
        ("exception_required", "Exception Required (Risk > 75)"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    deployment_intent_id = models.CharField(max_length=255, help_text="Correlation to deployment intent")
    correlation_id = models.CharField(max_length=255, unique=True, help_text="Unique identifier for audit trail")

    # Evidence Reference
    evidence_package_id = models.CharField(max_length=255, help_text="ID of associated evidence package")
    risk_score = models.DecimalField(
        max_digits=5, decimal_places=2, help_text="Risk score from evidence package (0-100)"
    )

    # Submission
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="cab_submissions")
    submitted_at = models.DateTimeField(auto_now_add=True)

    # Status & Gates
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="submitted")

    # Approval (if applicable)
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="cab_decisions"
    )
    approval_decision = models.CharField(
        max_length=50,
        choices=[
            ("approved", "Approved"),
            ("rejected", "Rejected"),
            ("conditional", "Conditionally Approved"),
        ],
        null=True,
        blank=True,
    )
    approval_rationale = models.TextField(blank=True, help_text="Reason for approval/rejection decision")
    approval_conditions = models.JSONField(default=dict, help_text="Conditions if conditionally approved")
    approved_at = models.DateTimeField(null=True, blank=True)

    # Metadata
    notes = models.TextField(blank=True, help_text="Additional notes from submitter")

    class Meta:
        db_table = "cab_workflow_cabaprovalrequest"
        ordering = ["-submitted_at"]
        verbose_name = "CAB Approval Request"
        verbose_name_plural = "CAB Approval Requests"
        indexes = [
            models.Index(fields=["deployment_intent_id", "-submitted_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["risk_score"]),
        ]

    def __str__(self):
        return f"CAB {self.id} for {self.deployment_intent_id} (Risk: {self.risk_score})"

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
    Requires Security Reviewer approval with expiry dates.
    """

    STATUS_CHOICES = [
        ("pending", "Pending Security Review"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("expired", "Expired"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    deployment_intent_id = models.CharField(max_length=255, help_text="What exception applies to")
    correlation_id = models.CharField(max_length=255, unique=True, help_text="Unique identifier for audit trail")

    # Exception Details
    reason = models.TextField(help_text="Why exception is needed")
    risk_justification = models.TextField(help_text="Why risk is acceptable despite threshold")
    compensating_controls = models.JSONField(
        default=list, help_text="List of compensating controls (e.g., ['Additional monitoring', 'Rollback plan'])"
    )

    # Approval Workflow
    requested_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="exception_requests")
    requested_at = models.DateTimeField(auto_now_add=True)

    # Security Reviewer approval required
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="exception_approvals",
        help_text="Security Reviewer who approved",
    )
    approval_decision = models.CharField(
        max_length=50,
        choices=[
            ("approved", "Approved"),
            ("rejected", "Rejected"),
        ],
        null=True,
        blank=True,
    )
    approval_rationale = models.TextField(blank=True, help_text="Security Reviewer rationale")
    approved_at = models.DateTimeField(null=True, blank=True)

    # Expiry (mandatory)
    expires_at = models.DateTimeField(help_text="Exception automatically expires (no permanent exceptions)")

    # Status
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="pending")

    class Meta:
        db_table = "cab_workflow_cabexception"
        ordering = ["-requested_at"]
        verbose_name = "CAB Exception"
        verbose_name_plural = "CAB Exceptions"
        indexes = [
            models.Index(fields=["deployment_intent_id", "-requested_at"]),
            models.Index(fields=["status", "expires_at"]),
        ]

    def __str__(self):
        return f"Exception {self.id} for {self.deployment_intent_id} ({self.status})"

    @property
    def is_active(self) -> bool:
        """Exception is active if approved and not expired."""
        now = timezone.now()
        return self.status == "approved" and self.approved_at is not None and self.expires_at > now

    @property
    def is_expired(self) -> bool:
        """Exception has expired."""
        return timezone.now() > self.expires_at


class CABApprovalDecision(models.Model):
    """
    Immutable record of CAB approval decision.
    Stored as event for audit trail and compliance.

    Links to: CABApprovalRequest, user decision, timestamp.
    """

    DECISION_CHOICES = [
        ("approved", "Approved"),
        ("rejected", "Rejected"),
        ("conditional", "Conditionally Approved"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    cab_request_id = models.CharField(max_length=255, help_text="ID of CABApprovalRequest being decided")
    correlation_id = models.CharField(max_length=255, help_text="Audit trail identifier")

    # Decision
    decision = models.CharField(max_length=50, choices=DECISION_CHOICES)
    rationale = models.TextField(help_text="Why this decision was made")

    # Approval authority
    decided_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name="cab_decisions_made")
    decided_at = models.DateTimeField(auto_now_add=True)

    # Conditional approval conditions
    conditions = models.JSONField(default=dict, help_text="Conditions if decision is conditional")

    class Meta:
        db_table = "cab_workflow_cabapprovaldecision"
        ordering = ["-decided_at"]
        verbose_name = "CAB Approval Decision"
        verbose_name_plural = "CAB Approval Decisions"
        indexes = [
            models.Index(fields=["cab_request_id", "-decided_at"]),
            models.Index(fields=["decision", "-decided_at"]),
        ]

    def __str__(self):
        return f"Decision {self.id}: {self.decision} by {self.decided_by.username}"
