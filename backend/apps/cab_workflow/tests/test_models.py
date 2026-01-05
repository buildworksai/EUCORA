# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for CAB workflow app.
"""
import pytest
from apps.cab_workflow.models import CABApproval
from apps.deployment_intents.models import DeploymentIntent
from django.contrib.auth.models import User
import uuid


@pytest.mark.django_db
class TestCABApproval:
    """Test CABApproval model."""
    
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
    
    def test_create_cab_approval(self):
        """Test creating a CAB approval."""
        approval = CABApproval.objects.create(
            deployment_intent=self.deployment,
            decision=CABApproval.Decision.APPROVED,
            approver=self.user,
            comments='Looks good',
        )
        assert approval.decision == CABApproval.Decision.APPROVED
        assert approval.approver == self.user
    
    def test_conditional_approval(self):
        """Test conditional approval with conditions."""
        approval = CABApproval.objects.create(
            deployment_intent=self.deployment,
            decision=CABApproval.Decision.CONDITIONAL,
            approver=self.user,
            comments='Approved with conditions',
            conditions=['Must deploy during maintenance window', 'Requires rollback plan review'],
        )
        assert approval.decision == CABApproval.Decision.CONDITIONAL
        assert len(approval.conditions) == 2
