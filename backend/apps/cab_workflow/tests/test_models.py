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
    
    def test_create_cab_approval(self, sample_cab_request, admin_user):
        """Test creating a CAB approval."""
        approval = CABApproval.objects.create(
            cab_request=sample_cab_request,
            decision=CABApproval.Decision.APPROVED,
            approver=admin_user,
            comments='Looks good',
        )
        assert approval.decision == CABApproval.Decision.APPROVED
        assert approval.approver == admin_user
    
    def test_conditional_approval(self, sample_cab_request, admin_user):
        """Test conditional approval with conditions."""
        approval = CABApproval.objects.create(
            cab_request=sample_cab_request,
            decision=CABApproval.Decision.CONDITIONAL,
            approver=admin_user,
            comments='Approved with conditions',
            conditions=['Must deploy during maintenance window', 'Requires rollback plan review'],
        )
        assert approval.decision == CABApproval.Decision.CONDITIONAL
        assert len(approval.conditions) == 2
