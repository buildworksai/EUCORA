# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Phase P5.5: CAB Workflow Service Integration with Blast Radius Classification

Extends CABWorkflowService with blast-radius-aware approval gates.
"""
from decimal import Decimal
from typing import Dict, Optional, Tuple

from django.contrib.auth.models import User

from apps.evidence_store.models_p5_5 import BlastRadiusClass, RiskModelVersion

from .models import CABApprovalRequest
from .services import CABWorkflowService


class CABWorkflowServiceP55(CABWorkflowService):
    """
    Extended CAB Workflow Service with blast-radius-aware gates.

    Overrides risk threshold evaluation to use:
    1. Active Risk Model Version (not hardcoded thresholds)
    2. Blast Radius Classification (context-aware gates)
    """

    @staticmethod
    def submit_for_approval_with_blast_radius(
        evidence_package_id: str,
        deployment_intent_id: str,
        risk_score: Decimal,
        blast_radius_class: str,
        submitted_by: User,
        notes: str = "",
        correlation_id: Optional[str] = None,
    ) -> Tuple[CABApprovalRequest, str]:
        """
        Submit with blast radius classification.

        Uses active risk model version + blast radius class to determine gates.

        Args:
            evidence_package_id: Evidence package ID
            deployment_intent_id: Deployment intent ID
            risk_score: Computed risk score (0-100)
            blast_radius_class: CRITICAL_INFRASTRUCTURE | BUSINESS_CRITICAL | PRODUCTIVITY_TOOLS | NON_CRITICAL
            submitted_by: User submitting
            notes: Optional notes
            correlation_id: Optional correlation ID

        Returns:
            (CABApprovalRequest, decision_status)
        """
        # Get active risk model
        try:
            risk_model = RiskModelVersion.get_active_version()
        except ValueError:
            # Fallback to hardcoded thresholds if no active model
            return CABWorkflowService.submit_for_approval(
                evidence_package_id=evidence_package_id,
                deployment_intent_id=deployment_intent_id,
                risk_score=risk_score,
                submitted_by=submitted_by,
                notes=notes,
                correlation_id=correlation_id,
            )

        # Get blast radius-specific threshold
        auto_approve_threshold = risk_model.get_auto_approve_threshold(blast_radius_class)

        # Override class-level threshold for this submission
        original_threshold = CABWorkflowService.AUTO_APPROVE_THRESHOLD
        CABWorkflowService.AUTO_APPROVE_THRESHOLD = Decimal(str(auto_approve_threshold))

        try:
            # Use parent submit logic with overridden threshold
            cab_request, decision_status = CABWorkflowService.submit_for_approval(
                evidence_package_id=evidence_package_id,
                deployment_intent_id=deployment_intent_id,
                risk_score=risk_score,
                submitted_by=submitted_by,
                notes=(
                    f"Blast Radius: {blast_radius_class}\n"
                    f"Risk Model: v{risk_model.version} ({risk_model.mode})\n"
                    f"Auto-approve threshold for {blast_radius_class}: ≤{auto_approve_threshold}\n\n"
                    f"{notes}"
                ),
                correlation_id=correlation_id,
            )

            # Add blast radius metadata to request
            cab_request.blast_radius_class = blast_radius_class
            cab_request.risk_model_version = risk_model.version
            cab_request.save(update_fields=["blast_radius_class", "risk_model_version"])

            return cab_request, decision_status

        finally:
            # Restore original threshold
            CABWorkflowService.AUTO_APPROVE_THRESHOLD = original_threshold

    @staticmethod
    def get_cab_quorum_required(blast_radius_class: str) -> int:
        """
        Get CAB quorum requirement for blast radius class.

        Args:
            blast_radius_class: Blast radius classification

        Returns:
            int: Minimum CAB members required for approval
        """
        try:
            br_class = BlastRadiusClass.objects.get(name=blast_radius_class)
            return br_class.cab_quorum_required
        except BlastRadiusClass.DoesNotExist:
            return 1  # Default: single CAB member

    @staticmethod
    def is_auto_approve_allowed(blast_radius_class: str) -> bool:
        """
        Check if auto-approve is allowed for blast radius class.

        CRITICAL_INFRASTRUCTURE: NEVER auto-approve (regardless of risk score)
        Others: Allowed if risk score within threshold

        Args:
            blast_radius_class: Blast radius classification

        Returns:
            bool: Whether auto-approve is permitted
        """
        try:
            br_class = BlastRadiusClass.objects.get(name=blast_radius_class)
            return br_class.auto_approve_allowed
        except BlastRadiusClass.DoesNotExist:
            return False  # Default: require CAB review

    @staticmethod
    def evaluate_blast_radius_gates(risk_score: Decimal, blast_radius_class: str) -> Dict[str, any]:
        """
        Evaluate approval gates based on risk score + blast radius.

        Returns decision with rationale.

        Args:
            risk_score: Risk score 0-100
            blast_radius_class: Blast radius classification

        Returns:
            {
                'decision': 'auto_approved' | 'manual_review' | 'exception_required',
                'auto_approve_threshold': int,
                'blast_radius_class': str,
                'cab_quorum_required': int,
                'rationale': str,
                'risk_model_version': str,
            }
        """
        # Get active risk model
        try:
            risk_model = RiskModelVersion.get_active_version()
        except ValueError:
            return {
                "decision": "manual_review",
                "auto_approve_threshold": 0,
                "blast_radius_class": blast_radius_class,
                "cab_quorum_required": 1,
                "rationale": "No active risk model configured - defaulting to manual CAB review",
                "risk_model_version": "UNKNOWN",
            }

        # Get blast radius details
        try:
            br_class = BlastRadiusClass.objects.get(name=blast_radius_class)
        except BlastRadiusClass.DoesNotExist:
            return {
                "decision": "manual_review",
                "auto_approve_threshold": 0,
                "blast_radius_class": blast_radius_class,
                "cab_quorum_required": 1,
                "rationale": f"Unknown blast radius class: {blast_radius_class} - defaulting to manual CAB review",
                "risk_model_version": risk_model.version,
            }

        # Get auto-approve threshold for this blast radius class
        auto_approve_threshold = risk_model.get_auto_approve_threshold(blast_radius_class)

        # Gate 1: Blast radius veto (e.g., CRITICAL_INFRASTRUCTURE never auto-approves)
        if not br_class.auto_approve_allowed:
            return {
                "decision": "manual_review",
                "auto_approve_threshold": auto_approve_threshold,
                "blast_radius_class": blast_radius_class,
                "cab_quorum_required": br_class.cab_quorum_required,
                "rationale": (
                    f"Blast radius class {blast_radius_class} prohibits auto-approve. "
                    f"Requires {br_class.cab_quorum_required} CAB member(s) approval."
                ),
                "risk_model_version": risk_model.version,
            }

        # Gate 2: Risk score within auto-approve threshold
        if risk_score <= Decimal(str(auto_approve_threshold)):
            return {
                "decision": "auto_approved",
                "auto_approve_threshold": auto_approve_threshold,
                "blast_radius_class": blast_radius_class,
                "cab_quorum_required": 0,  # No CAB needed
                "rationale": (
                    f"Risk score {risk_score} ≤ {auto_approve_threshold} for {blast_radius_class}. "
                    f"Auto-approved per Risk Model v{risk_model.version}."
                ),
                "risk_model_version": risk_model.version,
            }

        # Gate 3: Risk score exceeds threshold → manual review
        if risk_score <= Decimal("75"):  # Manual review zone
            return {
                "decision": "manual_review",
                "auto_approve_threshold": auto_approve_threshold,
                "blast_radius_class": blast_radius_class,
                "cab_quorum_required": br_class.cab_quorum_required,
                "rationale": (
                    f"Risk score {risk_score} > {auto_approve_threshold} for {blast_radius_class}. "
                    f"Requires {br_class.cab_quorum_required} CAB member(s) approval."
                ),
                "risk_model_version": risk_model.version,
            }

        # Gate 4: Very high risk → exception required
        return {
            "decision": "exception_required",
            "auto_approve_threshold": auto_approve_threshold,
            "blast_radius_class": blast_radius_class,
            "cab_quorum_required": br_class.cab_quorum_required,
            "rationale": (
                f"Risk score {risk_score} > 75 (high risk). "
                f"Requires Security Reviewer exception approval with compensating controls."
            ),
            "risk_model_version": risk_model.version,
        }
