# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for deployment_intents app.
"""
import pytest
from apps.deployment_intents.models import DeploymentIntent, RingDeployment
from django.contrib.auth.models import User
import uuid


@pytest.mark.django_db
class TestDeploymentIntent:
    """Test DeploymentIntent model."""
    
    def setup_method(self):
        """Set up test user."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_create_deployment_intent(self):
        """Test creating a deployment intent."""
        deployment = DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            risk_score=25,
            requires_cab_approval=False,
            submitter=self.user,
        )
        assert deployment.app_name == 'TestApp'
        assert deployment.status == DeploymentIntent.Status.PENDING
        assert deployment.correlation_id is not None
    
    def test_deployment_state_transitions(self):
        """Test deployment state machine transitions."""
        deployment = DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            risk_score=75,
            requires_cab_approval=True,
            submitter=self.user,
        )
        
        # High risk should start in AWAITING_CAB
        assert deployment.status == DeploymentIntent.Status.PENDING
        
        # Transition to AWAITING_CAB
        deployment.status = DeploymentIntent.Status.AWAITING_CAB
        deployment.save()
        assert deployment.status == DeploymentIntent.Status.AWAITING_CAB
        
        # Transition to APPROVED
        deployment.status = DeploymentIntent.Status.APPROVED
        deployment.save()
        assert deployment.status == DeploymentIntent.Status.APPROVED


@pytest.mark.django_db
class TestRingDeployment:
    """Test RingDeployment model."""
    
    def setup_method(self):
        """Set up test deployment intent."""
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.deployment = DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            submitter=self.user,
        )
    
    def test_create_ring_deployment(self):
        """Test creating a ring deployment."""
        ring_deployment = RingDeployment.objects.create(
            deployment_intent=self.deployment,
            ring=DeploymentIntent.Ring.LAB,
            connector_type='intune',
            success_count=10,
            failure_count=2,
            success_rate=0.833,
        )
        assert ring_deployment.success_rate == 0.833
        assert ring_deployment.promotion_gate_passed is False
    
    def test_promotion_gate(self):
        """Test promotion gate logic."""
        ring_deployment = RingDeployment.objects.create(
            deployment_intent=self.deployment,
            ring=DeploymentIntent.Ring.LAB,
            connector_type='intune',
            success_count=95,
            failure_count=5,
            success_rate=0.95,
        )
        
        # 95% success rate should pass promotion gate
        if ring_deployment.success_rate >= 0.90:
            ring_deployment.promotion_gate_passed = True
            ring_deployment.save()
        
        assert ring_deployment.promotion_gate_passed is True
