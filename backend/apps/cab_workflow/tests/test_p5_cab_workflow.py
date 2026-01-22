# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
P5.2: Comprehensive tests for CAB Workflow Service.
Tests risk-based gates, approval workflows, and exception handling.
Coverage: CABApprovalRequest, CABException, CABApprovalDecision + Service logic.
"""
import pytest
from decimal import Decimal
from datetime import timedelta
from django.utils import timezone
from django.contrib.auth.models import User
from django.test import TestCase

from apps.cab_workflow.models import CABApprovalRequest, CABException, CABApprovalDecision
from apps.cab_workflow.services import CABWorkflowService
from apps.evidence_store.models import EvidencePackage
from apps.deployment_intents.models import DeploymentIntent


class CABWorkflowTestSetup(TestCase):
    """Setup fixtures for CAB workflow tests."""
    
    @classmethod
    def setUpTestData(cls):
        """Create common test data."""
        # Create users
        cls.requester = User.objects.create_user(
            username='requester',
            email='requester@example.com'
        )
        cls.cab_member = User.objects.create_user(
            username='cab_member',
            email='cab@example.com'
        )
        cls.security_reviewer = User.objects.create_user(
            username='security_reviewer',
            email='security@example.com'
        )
        
        # Create deployment intent
        cls.deployment = DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring='CANARY',
        )
        
        # Create evidence package
        cls.evidence = EvidencePackage.objects.create(
            deployment_intent_id=str(cls.deployment.id),
            evidence_data={
                'test_coverage': 92,
                'security_issues': 0,
                'manual_testing': 'completed',
                'rollback_validated': True,
                'change_scope': 5,
            },
            risk_score=Decimal('45'),
            risk_score_breakdown={
                'coverage': 0,
                'security': 0,
                'testing': 0,
                'rollback': 0,
                'scope': 0,
            }
        )


class TestRiskThresholdEvaluation(CABWorkflowTestSetup):
    """Test risk threshold evaluation logic."""
    
    def test_auto_approve_at_threshold(self):
        """Risk ≤ 50 should auto-approve."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal('50'))
        self.assertEqual(result, 'auto_approved')
    
    def test_auto_approve_below_threshold(self):
        """Risk < 50 should auto-approve."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal('30'))
        self.assertEqual(result, 'auto_approved')
    
    def test_manual_review_at_lower_bound(self):
        """Risk 50.01 should require manual review."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal('50.01'))
        self.assertEqual(result, 'manual_review')
    
    def test_manual_review_mid_range(self):
        """Risk 60 should require manual review."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal('60'))
        self.assertEqual(result, 'manual_review')
    
    def test_manual_review_at_upper_bound(self):
        """Risk ≤ 75 should still be manual review (not exception)."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal('75'))
        self.assertEqual(result, 'manual_review')
    
    def test_exception_required_above_threshold(self):
        """Risk > 75 should require exception."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal('75.01'))
        self.assertEqual(result, 'exception_required')
    
    def test_exception_required_high_risk(self):
        """Risk 85 should require exception."""
        result = CABWorkflowService.evaluate_risk_threshold(Decimal('85'))
        self.assertEqual(result, 'exception_required')


class TestCABSubmission(CABWorkflowTestSetup):
    """Test CAB submission and auto-approval logic."""
    
    def test_submit_low_risk_auto_approved(self):
        """Low risk (≤50) should auto-approve."""
        cab_req, decision = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('40'),
            submitted_by=self.requester,
            notes='Low risk deployment'
        )
        
        self.assertEqual(cab_req.status, 'auto_approved')
        self.assertEqual(decision, 'auto_approved')
        self.assertEqual(cab_req.risk_score, Decimal('40'))
        self.assertEqual(cab_req.approved_by, self.requester)
        self.assertIsNotNone(cab_req.approved_at)
    
    def test_submit_medium_risk_requires_review(self):
        """Medium risk (50-75) should require CAB review."""
        cab_req, decision = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('60'),
            submitted_by=self.requester,
            notes='Medium risk deployment'
        )
        
        self.assertEqual(cab_req.status, 'submitted')
        self.assertEqual(decision, 'manual_review')
        self.assertEqual(cab_req.risk_score, Decimal('60'))
        self.assertIsNone(cab_req.approved_by)
        self.assertIsNone(cab_req.approved_at)
    
    def test_submit_high_risk_requires_exception(self):
        """High risk (>75) should require exception."""
        cab_req, decision = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('80'),
            submitted_by=self.requester,
            notes='High risk deployment'
        )
        
        self.assertEqual(cab_req.status, 'exception_required')
        self.assertEqual(decision, 'exception_required')
        self.assertEqual(cab_req.risk_score, Decimal('80'))
    
    def test_submit_generates_correlation_id(self):
        """Submission should generate correlation ID if not provided."""
        cab_req, _ = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('40'),
            submitted_by=self.requester,
        )
        
        self.assertIsNotNone(cab_req.correlation_id)
        self.assertTrue(cab_req.correlation_id.startswith('CAB-'))
    
    def test_submit_custom_correlation_id(self):
        """Submission should use provided correlation ID."""
        custom_id = 'CUSTOM-12345'
        cab_req, _ = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('40'),
            submitted_by=self.requester,
            correlation_id=custom_id,
        )
        
        self.assertEqual(cab_req.correlation_id, custom_id)
    
    def test_submit_invalid_risk_score_negative(self):
        """Submission with negative risk should fail."""
        with self.assertRaises(ValueError) as ctx:
            CABWorkflowService.submit_for_approval(
                evidence_package_id=str(self.evidence.id),
                deployment_intent_id=str(self.deployment.id),
                risk_score=Decimal('-10'),
                submitted_by=self.requester,
            )
        self.assertIn('Invalid risk score', str(ctx.exception))
    
    def test_submit_invalid_risk_score_too_high(self):
        """Submission with risk > 100 should fail."""
        with self.assertRaises(ValueError) as ctx:
            CABWorkflowService.submit_for_approval(
                evidence_package_id=str(self.evidence.id),
                deployment_intent_id=str(self.deployment.id),
                risk_score=Decimal('101'),
                submitted_by=self.requester,
            )
        self.assertIn('Invalid risk score', str(ctx.exception))
    
    def test_submit_missing_evidence_package(self):
        """Submission with invalid evidence package should fail."""
        with self.assertRaises(ValueError) as ctx:
            CABWorkflowService.submit_for_approval(
                evidence_package_id='nonexistent',
                deployment_intent_id=str(self.deployment.id),
                risk_score=Decimal('40'),
                submitted_by=self.requester,
            )
        self.assertIn('Evidence package not found', str(ctx.exception))
    
    def test_submit_creates_auto_approved_decision(self):
        """Auto-approved submission should create CABApprovalDecision."""
        cab_req, _ = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('40'),
            submitted_by=self.requester,
        )
        
        decision = CABApprovalDecision.objects.filter(
            cab_request_id=str(cab_req.id)
        ).first()
        
        self.assertIsNotNone(decision)
        self.assertEqual(decision.decision, 'approved')
        self.assertIn('Auto-approved', decision.rationale)


class TestCABApproval(CABWorkflowTestSetup):
    """Test CAB approval workflow."""
    
    def setUp(self):
        """Create a pending CAB request for testing."""
        self.cab_req, _ = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('60'),
            submitted_by=self.requester,
        )
    
    def test_approve_pending_request(self):
        """CAB member can approve pending request."""
        updated = CABWorkflowService.approve_request(
            cab_request_id=str(self.cab_req.id),
            approver=self.cab_member,
            rationale='Risk assessment completed - acceptable',
        )
        
        self.assertEqual(updated.status, 'approved')
        self.assertEqual(updated.approved_by, self.cab_member)
        self.assertEqual(updated.approval_decision, 'approved')
        self.assertIsNotNone(updated.approved_at)
    
    def test_approve_creates_decision_record(self):
        """Approval should create immutable decision record."""
        CABWorkflowService.approve_request(
            cab_request_id=str(self.cab_req.id),
            approver=self.cab_member,
            rationale='Approved by CAB',
        )
        
        decisions = CABApprovalDecision.objects.filter(
            cab_request_id=str(self.cab_req.id)
        )
        # Should have exactly 1 decision (was submitted, not auto-approved)
        self.assertEqual(decisions.count(), 1)
        decision = decisions.first()
        self.assertEqual(decision.decision, 'approved')
    
    def test_approve_with_conditions(self):
        """CAB can approve with conditions."""
        conditions = {'must_monitor': True, 'max_rollout_pct': 5}
        
        updated = CABWorkflowService.approve_request(
            cab_request_id=str(self.cab_req.id),
            approver=self.cab_member,
            conditions=conditions,
        )
        
        self.assertEqual(updated.approval_conditions, conditions)
    
    def test_cannot_approve_already_approved(self):
        """Cannot approve already-approved request."""
        CABWorkflowService.approve_request(
            cab_request_id=str(self.cab_req.id),
            approver=self.cab_member,
        )
        
        with self.assertRaises(ValueError) as ctx:
            CABWorkflowService.approve_request(
                cab_request_id=str(self.cab_req.id),
                approver=self.cab_member,
            )
        self.assertIn('Cannot approve request', str(ctx.exception))
    
    def test_reject_pending_request(self):
        """CAB member can reject pending request."""
        updated = CABWorkflowService.reject_request(
            cab_request_id=str(self.cab_req.id),
            rejector=self.cab_member,
            rationale='Risk assessment incomplete',
        )
        
        self.assertEqual(updated.status, 'rejected')
        self.assertEqual(updated.approved_by, self.cab_member)
        self.assertEqual(updated.approval_decision, 'rejected')
    
    def test_reject_creates_decision_record(self):
        """Rejection should create immutable decision record."""
        CABWorkflowService.reject_request(
            cab_request_id=str(self.cab_req.id),
            rejector=self.cab_member,
            rationale='Rejected',
        )
        
        decisions = CABApprovalDecision.objects.filter(
            cab_request_id=str(self.cab_req.id)
        )
        self.assertEqual(decisions.count(), 1)
        decision = decisions.first()
        self.assertEqual(decision.decision, 'rejected')
    
    def test_cannot_reject_already_rejected(self):
        """Cannot reject already-rejected request."""
        CABWorkflowService.reject_request(
            cab_request_id=str(self.cab_req.id),
            rejector=self.cab_member,
        )
        
        with self.assertRaises(ValueError):
            CABWorkflowService.reject_request(
                cab_request_id=str(self.cab_req.id),
                rejector=self.cab_member,
            )


class TestCABException(CABWorkflowTestSetup):
    """Test CAB exception handling."""
    
    def test_create_exception_default_expiry(self):
        """Exception should have default 30-day expiry."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Urgent business need',
            risk_justification='Additional monitoring in place',
            compensating_controls=['24/7 monitoring', 'Quick rollback plan'],
        )
        
        self.assertEqual(exc.status, 'pending')
        self.assertIsNotNone(exc.expires_at)
        # Check expiry is approximately 30 days
        diff = (exc.expires_at - timezone.now()).days
        self.assertTrue(29 <= diff <= 31)
    
    def test_create_exception_custom_expiry(self):
        """Exception should accept custom expiry days."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Urgent business need',
            risk_justification='Additional monitoring in place',
            compensating_controls=['24/7 monitoring'],
            expiry_days=7,
        )
        
        diff = (exc.expires_at - timezone.now()).days
        self.assertTrue(6 <= diff <= 8)
    
    def test_create_exception_max_expiry(self):
        """Exception can have up to 90-day expiry."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Long-term deployment',
            risk_justification='Risk mitigated',
            compensating_controls=['Monitoring'],
            expiry_days=90,
        )
        
        self.assertIsNotNone(exc)
        diff = (exc.expires_at - timezone.now()).days
        self.assertTrue(89 <= diff <= 91)
    
    def test_create_exception_expiry_too_long_rejected(self):
        """Exception expiry > 90 days should fail."""
        with self.assertRaises(ValueError) as ctx:
            CABWorkflowService.create_exception(
                deployment_intent_id=str(self.deployment.id),
                requested_by=self.requester,
                reason='Long-term',
                risk_justification='Risk mitigated',
                compensating_controls=['Monitoring'],
                expiry_days=91,
            )
        self.assertIn('cannot exceed 90 days', str(ctx.exception))
    
    def test_create_exception_expiry_too_short_rejected(self):
        """Exception expiry < 1 day should fail."""
        with self.assertRaises(ValueError) as ctx:
            CABWorkflowService.create_exception(
                deployment_intent_id=str(self.deployment.id),
                requested_by=self.requester,
                reason='Short-term',
                risk_justification='Risk mitigated',
                compensating_controls=['Monitoring'],
                expiry_days=0,
            )
        self.assertIn('at least 1 day', str(ctx.exception))
    
    def test_approve_exception(self):
        """Security Reviewer can approve exception."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Urgent',
            risk_justification='Mitigated',
            compensating_controls=['Monitoring'],
        )
        
        approved = CABWorkflowService.approve_exception(
            exception_id=str(exc.id),
            approver=self.security_reviewer,
            rationale='Approved - compensating controls sufficient',
        )
        
        self.assertEqual(approved.status, 'approved')
        self.assertEqual(approved.approved_by, self.security_reviewer)
        self.assertIsNotNone(approved.approved_at)
    
    def test_reject_exception(self):
        """Security Reviewer can reject exception."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Urgent',
            risk_justification='Mitigated',
            compensating_controls=['Monitoring'],
        )
        
        rejected = CABWorkflowService.reject_exception(
            exception_id=str(exc.id),
            rejector=self.security_reviewer,
            rationale='Insufficient compensating controls',
        )
        
        self.assertEqual(rejected.status, 'rejected')
    
    def test_cannot_approve_expired_exception(self):
        """Cannot approve exception that has expired."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Urgent',
            risk_justification='Mitigated',
            compensating_controls=['Monitoring'],
            expiry_days=1,
        )
        
        # Manually set to expired
        exc.expires_at = timezone.now() - timedelta(hours=1)
        exc.save()
        
        with self.assertRaises(ValueError) as ctx:
            CABWorkflowService.approve_exception(
                exception_id=str(exc.id),
                approver=self.security_reviewer,
            )
        self.assertIn('already expired', str(ctx.exception))
    
    def test_exception_is_active_when_approved(self):
        """Active exception should return True for is_active."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Urgent',
            risk_justification='Mitigated',
            compensating_controls=['Monitoring'],
        )
        
        CABWorkflowService.approve_exception(
            exception_id=str(exc.id),
            approver=self.security_reviewer,
        )
        
        exc.refresh_from_db()
        self.assertTrue(exc.is_active)
    
    def test_exception_is_expired_when_past_expiry(self):
        """Expired exception should return True for is_expired."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Urgent',
            risk_justification='Mitigated',
            compensating_controls=['Monitoring'],
            expiry_days=1,
        )
        
        # Move to past expiry
        exc.expires_at = timezone.now() - timedelta(hours=1)
        exc.save()
        
        self.assertTrue(exc.is_expired)


class TestCABQueries(CABWorkflowTestSetup):
    """Test CAB query and retrieval methods."""
    
    def test_get_pending_requests(self):
        """Should retrieve all pending requests."""
        # Create 3 pending requests
        for i in range(3):
            CABWorkflowService.submit_for_approval(
                evidence_package_id=str(self.evidence.id),
                deployment_intent_id=str(self.deployment.id),
                risk_score=Decimal('60'),
                submitted_by=self.requester,
            )
        
        pending = CABWorkflowService.get_pending_requests()
        self.assertEqual(pending.count(), 3)
    
    def test_get_requests_by_deployment(self):
        """Should retrieve requests for specific deployment."""
        CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('60'),
            submitted_by=self.requester,
        )
        
        requests = CABWorkflowService.get_requests_by_deployment(str(self.deployment.id))
        self.assertEqual(requests.count(), 1)
    
    def test_get_active_exceptions(self):
        """Should retrieve active (approved, non-expired) exceptions."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Urgent',
            risk_justification='Mitigated',
            compensating_controls=['Monitoring'],
        )
        
        CABWorkflowService.approve_exception(
            exception_id=str(exc.id),
            approver=self.security_reviewer,
        )
        
        active = CABWorkflowService.get_active_exceptions_for_deployment(str(self.deployment.id))
        self.assertEqual(active.count(), 1)
    
    def test_cleanup_expired_exceptions(self):
        """Should mark expired exceptions as 'expired'."""
        exc = CABWorkflowService.create_exception(
            deployment_intent_id=str(self.deployment.id),
            requested_by=self.requester,
            reason='Urgent',
            risk_justification='Mitigated',
            compensating_controls=['Monitoring'],
            expiry_days=1,
        )
        
        CABWorkflowService.approve_exception(
            exception_id=str(exc.id),
            approver=self.security_reviewer,
        )
        
        # Move to past expiry
        exc.expires_at = timezone.now() - timedelta(hours=1)
        exc.save()
        
        count = CABWorkflowService.cleanup_expired_exceptions()
        self.assertEqual(count, 1)
        
        exc.refresh_from_db()
        self.assertEqual(exc.status, 'expired')
    
    def test_get_approval_status(self):
        """Should return comprehensive approval status."""
        cab_req, _ = CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('60'),
            submitted_by=self.requester,
        )
        
        status = CABWorkflowService.get_approval_status(str(self.deployment.id))
        
        self.assertIn('deployment_intent_id', status)
        self.assertIn('latest_request', status)
        self.assertIn('is_approved', status)
        self.assertIn('requires_exception', status)
        self.assertEqual(status['latest_status'], 'submitted')
    
    def test_get_approval_status_auto_approved(self):
        """Auto-approved deployments should show as approved."""
        CABWorkflowService.submit_for_approval(
            evidence_package_id=str(self.evidence.id),
            deployment_intent_id=str(self.deployment.id),
            risk_score=Decimal('40'),
            submitted_by=self.requester,
        )
        
        status = CABWorkflowService.get_approval_status(str(self.deployment.id))
        
        self.assertTrue(status['is_approved'])
        self.assertEqual(status['latest_status'], 'auto_approved')


class TestCABModels(CABWorkflowTestSetup):
    """Test CAB model properties and behavior."""
    
    def test_cab_approval_request_auto_approve_threshold(self):
        """CABApprovalRequest.auto_approve_threshold property."""
        req = CABApprovalRequest(risk_score=Decimal('50'))
        self.assertTrue(req.auto_approve_threshold)
        
        req2 = CABApprovalRequest(risk_score=Decimal('50.01'))
        self.assertFalse(req2.auto_approve_threshold)
    
    def test_cab_approval_request_manual_review_required(self):
        """CABApprovalRequest.manual_review_required property."""
        req = CABApprovalRequest(risk_score=Decimal('60'))
        self.assertTrue(req.manual_review_required)
        
        req2 = CABApprovalRequest(risk_score=Decimal('40'))
        self.assertFalse(req2.manual_review_required)
    
    def test_cab_approval_request_exception_required(self):
        """CABApprovalRequest.exception_required property."""
        req = CABApprovalRequest(risk_score=Decimal('80'))
        self.assertTrue(req.exception_required)
        
        req2 = CABApprovalRequest(risk_score=Decimal('75'))
        self.assertFalse(req2.exception_required)
    
    def test_cab_exception_is_active(self):
        """CABException.is_active property."""
        exc = CABException(
            status='approved',
            expires_at=timezone.now() + timedelta(days=10),
            approved_at=timezone.now(),
        )
        self.assertTrue(exc.is_active)
    
    def test_cab_exception_is_active_false_when_pending(self):
        """Exception is not active if pending."""
        exc = CABException(
            status='pending',
            expires_at=timezone.now() + timedelta(days=10),
        )
        self.assertFalse(exc.is_active)
    
    def test_cab_exception_is_expired(self):
        """CABException.is_expired property."""
        exc = CABException(
            expires_at=timezone.now() - timedelta(hours=1),
        )
        self.assertTrue(exc.is_expired)
