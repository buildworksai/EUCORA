# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Additional tests for policy_engine services to reach 90% coverage.
"""
import pytest
from apps.policy_engine.services import _evaluate_factor
from apps.event_store.models import DeploymentEvent
from django.utils import timezone
from datetime import timedelta
import uuid


@pytest.mark.django_db
class TestPolicyEngineServicesCoverage:
    """Additional tests for policy_engine services coverage."""
    
    def test_evaluate_rollback_complexity_no_plan(self):
        """Test rollback complexity with no plan."""
        score = _evaluate_factor('Rollback Complexity', {
            'has_rollback_plan': False,
            'rollback_tested': False,
        }, {})
        assert score == 1.0  # High risk
    
    def test_evaluate_rollback_complexity_untested(self):
        """Test rollback complexity with untested plan."""
        score = _evaluate_factor('Rollback Complexity', {
            'has_rollback_plan': True,
            'rollback_tested': False,
        }, {})
        assert score == 0.5  # Medium risk
    
    def test_evaluate_rollback_complexity_tested(self):
        """Test rollback complexity with tested plan."""
        score = _evaluate_factor('Rollback Complexity', {
            'has_rollback_plan': True,
            'rollback_tested': True,
        }, {})
        assert score == 0.0  # Low risk
    
    def test_evaluate_compliance_impact_no_tags(self):
        """Test compliance impact with no tags."""
        score = _evaluate_factor('Compliance Impact', {
            'compliance_tags': [],
        }, {})
        assert score == 0.0  # Low risk
    
    def test_evaluate_compliance_impact_sox(self):
        """Test compliance impact with SOX tag."""
        score = _evaluate_factor('Compliance Impact', {
            'compliance_tags': ['sox'],
        }, {})
        assert score == 1.0  # Critical risk
    
    def test_evaluate_compliance_impact_pci(self):
        """Test compliance impact with PCI tag."""
        score = _evaluate_factor('Compliance Impact', {
            'compliance_tags': ['pci'],
        }, {})
        assert score == 0.7  # High risk
        
    def test_evaluate_compliance_impact_other(self):
        """Test compliance impact with other tags."""
        score = _evaluate_factor('Compliance Impact', {
            'compliance_tags': ['gdpr'],
        }, {})
        assert score == 0.3  # Low-Medium risk
    
    def test_evaluate_deployment_frequency_various_counts(self):
        """Test deployment frequency with various deployment counts."""
        # Create test events
        app_name = 'FrequencyTestApp'
        thirty_days_ago = timezone.now() - timedelta(days=30)
        
        # Create 3 deployments (should give 0.4 risk)
        for i in range(3):
            DeploymentEvent.objects.create(
                correlation_id=uuid.uuid4(),
                event_type=DeploymentEvent.EventType.DEPLOYMENT_CREATED,
                event_data={'app_name': app_name},
                actor='testuser',
            )
        
        score = _evaluate_factor('Deployment Frequency', {
            'app_name': app_name,
        }, {})
        assert score == 0.4  # 3-5 deployments
    
    def test_evaluate_historical_success_rate_high_success(self):
        """Test historical success rate with high success."""
        app_name = 'SuccessTestApp'
        
        # Create 9 successful, 1 failed (90% success rate)
        for i in range(9):
            DeploymentEvent.objects.create(
                correlation_id=uuid.uuid4(),
                event_type=DeploymentEvent.EventType.DEPLOYMENT_COMPLETED,
                event_data={'app_name': app_name},
                actor='testuser',
            )
        
        DeploymentEvent.objects.create(
            correlation_id=uuid.uuid4(),
            event_type=DeploymentEvent.EventType.DEPLOYMENT_FAILED,
            event_data={'app_name': app_name},
            actor='testuser',
        )
        
        score = _evaluate_factor('Historical Success Rate', {
            'app_name': app_name,
        }, {})
        assert score == 0.1  # 90-99% success
    
    def test_evaluate_historical_success_rate_low_success(self):
        """Test historical success rate with low success."""
        app_name = 'LowSuccessApp'
        
        # Create 2 successful, 3 failed (40% success rate)
        for i in range(2):
            DeploymentEvent.objects.create(
                correlation_id=uuid.uuid4(),
                event_type=DeploymentEvent.EventType.DEPLOYMENT_COMPLETED,
                event_data={'app_name': app_name},
                actor='testuser',
            )
        
        for i in range(3):
            DeploymentEvent.objects.create(
                correlation_id=uuid.uuid4(),
                event_type=DeploymentEvent.EventType.DEPLOYMENT_FAILED,
                event_data={'app_name': app_name},
                actor='testuser',
            )
        
        score = _evaluate_factor('Historical Success Rate', {
            'app_name': app_name,
        }, {})
        assert score == 1.0  # <50% success
    
    def test_evaluate_unknown_factor(self):
        """Test evaluation of unknown factor returns medium risk."""
        score = _evaluate_factor('Unknown Factor', {}, {})
        assert score == 0.5  # Default medium risk
