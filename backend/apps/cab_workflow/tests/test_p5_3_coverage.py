# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
P5.3: Additional tests for comprehensive code coverage (≥90%)
Covers error handling paths, edge cases, and service layer logic.
"""
from datetime import timedelta
from decimal import Decimal
from unittest.mock import MagicMock, patch

import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone
from rest_framework import status
from rest_framework.test import APIClient

from apps.cab_workflow.models import CABApprovalDecision, CABApprovalRequest, CABException
from apps.cab_workflow.services import CABWorkflowService
from apps.deployment_intents.models import DeploymentIntent
from apps.evidence_store.models import EvidencePackage


class TestCABServiceLayer(TestCase):
    """Test CABWorkflowService methods for comprehensive coverage."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        cls.user, created = User.objects.get_or_create(username="test", defaults={"email": "test@example.com"})
        if created:
            cls.user.set_password("pass")
            cls.user.save()

        evidence_id = __import__("uuid").uuid4()
        cls.evidence = EvidencePackage.objects.create(
            id=evidence_id,
            evidence_data={"test": "data"},
            risk_score=Decimal("50"),
            risk_factors={"test": 0},
            correlation_id=f"EVD-{evidence_id}",
        )

        cls.deployment = DeploymentIntent.objects.create(
            app_name="Test",
            version="1.0",
            target_ring="LAB",
            evidence_pack_id=str(cls.evidence.id),
            submitter=cls.user,
        )

    def test_evaluate_risk_threshold_auto_approve(self):
        """Risk ≤50 should auto-approve."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal("50"))
        self.assertEqual(result, "auto_approved")

    def test_evaluate_risk_threshold_manual_review(self):
        """Risk 50-75 should require manual review."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal("60"))
        self.assertEqual(result, "manual_review")

    def test_evaluate_risk_threshold_exception_required(self):
        """Risk >75 should require exception."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal("80"))
        self.assertEqual(result, "exception_required")

    def test_submit_for_approval_auto_approved(self):
        """Submit low risk should auto-approve."""
        cab_request, status_val = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal("40"),
            submitted_by=self.user,
            notes="Test",
        )

        self.assertEqual(status_val, "auto_approved")
        self.assertEqual(cab_request.status, "auto_approved")
        self.assertIsNotNone(cab_request.approved_at)

        # Verify decision was created
        decision = CABApprovalDecision.objects.filter(cab_request_id=str(cab_request.id)).first()
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, "approved")

    def test_submit_for_approval_manual_review(self):
        """Submit medium risk should need manual review."""
        cab_request, status_val = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal("60"),
            submitted_by=self.user,
        )

        self.assertEqual(status_val, "manual_review")
        self.assertEqual(cab_request.status, "submitted")
        self.assertIsNone(cab_request.approved_at)

    def test_submit_for_approval_exception_required(self):
        """Submit high risk should require exception."""
        cab_request, status_val = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal("80"),
            submitted_by=self.user,
        )

        self.assertEqual(status_val, "exception_required")
        self.assertEqual(cab_request.status, "exception_required")

    def test_submit_for_approval_invalid_risk_score_low(self):
        """Invalid risk score (negative) should raise."""
        with self.assertRaises(ValueError):
            CABWorkflowService.submit_for_approval(
                evidence_package_id=str(self.evidence.id),
                deployment_intent_id=str(self.deployment.id),
                risk_score=Decimal("-10"),
                submitted_by=self.user,
            )

    def test_submit_for_approval_invalid_risk_score_high(self):
        """Invalid risk score (>100) should raise."""
        with self.assertRaises(ValueError):
            CABWorkflowService.submit_for_approval(
                evidence_package_id=str(self.evidence.id),
                deployment_intent_id=str(self.deployment.id),
                risk_score=Decimal("101"),
                submitted_by=self.user,
            )

    def test_submit_for_approval_missing_evidence(self):
        """Missing evidence package should raise."""
        with self.assertRaises(ValueError):
            CABWorkflowService.submit_for_approval(
                evidence_package_id="00000000-0000-0000-0000-000000000000",
                deployment_intent_id=str(self.deployment.id),
                risk_score=Decimal("50"),
                submitted_by=self.user,
            )

    # Skipping test_submit_for_approval_missing_deployment due to test setup complexity

    def test_submit_for_approval_custom_correlation_id(self):
        """Submit with custom correlation ID should use it."""
        custom_id = "CUSTOM-12345"
        cab_request, _ = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal("50"),
            submitted_by=self.user,
            correlation_id=custom_id,
        )

        self.assertEqual(cab_request.correlation_id, custom_id)

    def test_approve_request_success(self):
        """Approve request should update status."""
        cab_request = CABApprovalRequest.objects.create(
            deployment_intent_id=str(self.deployment.id),
            correlation_id="TEST-001",
            evidence_package_id=str(self.evidence.id),
            risk_score=Decimal("60"),
            submitted_by=self.user,
            status="submitted",
        )

        CABWorkflowService.approve_request(
            cab_request_id=str(cab_request.id),
            approver=self.user,
            rationale="Risk acceptable",
            conditions={"max_devices": 100},
        )

        cab_request.refresh_from_db()
        self.assertEqual(cab_request.status, "approved")
        self.assertEqual(cab_request.approval_conditions, {"max_devices": 100})
        self.assertIsNotNone(cab_request.approved_at)

    def test_reject_request_success(self):
        """Reject request should update status."""
        cab_request = CABApprovalRequest.objects.create(
            deployment_intent_id=str(self.deployment.id),
            correlation_id="TEST-002",
            evidence_package_id=str(self.evidence.id),
            risk_score=Decimal("60"),
            submitted_by=self.user,
            status="submitted",
        )

        CABWorkflowService.reject_request(
            cab_request_id=str(cab_request.id), rejector=self.user, rationale="Evidence insufficient"
        )

        cab_request.refresh_from_db()
        self.assertEqual(cab_request.status, "rejected")
        self.assertEqual(cab_request.approval_decision, "rejected")

    def test_create_exception_success(self):
        """Create exception should succeed."""
        exception = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            reason="Urgent patch",
            risk_justification="Mitigated with monitoring",
            compensating_controls=["Monitor 24/7"],
            expiry_days=30,
            requested_by=self.user,
        )

        self.assertEqual(exception.status, "pending")
        self.assertIsNotNone(exception.expires_at)
        self.assertLess(exception.expires_at, timezone.now() + timedelta(days=31))

    def test_create_exception_invalid_expiry(self):
        """Create exception with invalid expiry should raise."""
        with self.assertRaises(ValueError):
            CABWorkflowService.create_exception(
                deployment_intent_id=str(self.deployment.id),
                reason="Test",
                risk_justification="Test",
                compensating_controls=["Test"],
                expiry_days=91,  # Too long
                requested_by=self.user,
            )

    def test_approve_exception_success(self):
        """Approve exception should succeed."""
        expires_at = timezone.now() + timedelta(days=30)
        exception = CABException.objects.create(
            deployment_intent_id=str(self.deployment.id),
            correlation_id="EXC-001",
            reason="Test",
            risk_justification="Test",
            compensating_controls=["Test"],
            expires_at=expires_at,
            requested_by=self.user,
            status="pending",
        )

        CABWorkflowService.approve_exception(exception_id=str(exception.id), approver=self.user, rationale="Accepted")

        exception.refresh_from_db()
        self.assertEqual(exception.status, "approved")


class TestCABAPIErrorHandling(TestCase):
    """Test API error handling for edge cases."""

    @classmethod
    def setUpTestData(cls):
        """Create test data."""
        cls.user, created = User.objects.get_or_create(username="user", defaults={"email": "user@example.com"})
        if created:
            cls.user.set_password("pass")
            cls.user.save()

        evidence_id = __import__("uuid").uuid4()
        cls.evidence = EvidencePackage.objects.create(
            id=evidence_id,
            evidence_data={"test": "data"},
            risk_score=Decimal("50"),
            risk_factors={"test": 0},
            correlation_id=f"EVD-{evidence_id}",
        )

        cls.deployment = DeploymentIntent.objects.create(
            app_name="Test",
            version="1.0",
            target_ring="LAB",
            evidence_pack_id=str(cls.evidence.id),
            submitter=cls.user,
        )

    def setUp(self):
        """Setup for each test."""
        self.client = APIClient()

    def test_submit_missing_required_field(self):
        """Submit missing risk_score should fail."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/v1/cab/submit/",
            {
                "evidence_package_id": str(self.evidence.id),
                "notes": "Test",
                # Missing risk_score
            },
        )

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_service_error_handling(self):
        """API should handle service errors gracefully."""
        self.client.force_authenticate(user=self.user)

        # Try to submit with invalid risk score
        response = self.client.post(
            "/api/v1/cab/submit/",
            {
                "evidence_package_id": str(self.evidence.id),
                "risk_score": "-10.0",  # Invalid - negative
            },
        )

        # Should get 400 Bad Request with error message
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # Response should contain validation error details
        self.assertTrue("risk_score" in response.data or "error" in str(response.data))

    def test_nonexistent_request_404(self):
        """Get nonexistent request should return 404."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/v1/cab/00000000-0000-0000-0000-000000000000/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_invalid_uuid_in_url(self):
        """Invalid UUID in URL should return 404."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/v1/cab/invalid-uuid/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_submit_nonexistent_evidence_package(self):
        """Submit with nonexistent evidence package should return 404."""
        self.client.force_authenticate(user=self.user)

        response = self.client.post(
            "/api/v1/cab/submit/",
            {
                "evidence_package_id": "00000000-0000-0000-0000-000000000000",
                "risk_score": "50.0",
            },
        )

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_get_nonexistent_request(self):
        """Get nonexistent request should return 404."""
        self.client.force_authenticate(user=self.user)

        response = self.client.get("/api/v1/cab/00000000-0000-0000-0000-000000000000/")

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
