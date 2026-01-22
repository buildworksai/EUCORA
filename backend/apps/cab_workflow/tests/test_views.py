# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for CAB workflow views.
"""
import pytest
from apps.deployment_intents.models import DeploymentIntent
from apps.cab_workflow.models import CABApproval
import uuid


@pytest.mark.django_db
class TestCABWorkflowViews:
    """Test CAB workflow view endpoints."""
    
    def test_approve_deployment(self, authenticated_client, sample_deployment_intent):
        """Test approving a deployment."""
        url = f'/api/v1/cab/{sample_deployment_intent.correlation_id}/approve/'
        response = authenticated_client.post(url, {
            'comments': 'Looks good',
        }, format='json')
        
        assert response.status_code in [200, 201]
        
        # Verify deployment exists
        sample_deployment_intent.refresh_from_db()
        assert sample_deployment_intent.app_name is not None
    
    def test_approve_deployment_with_conditions(self, authenticated_client, sample_deployment_intent):
        """Test conditional approval."""
        url = f'/api/v1/cab/{sample_deployment_intent.correlation_id}/approve/'
        response = authenticated_client.post(url, {
            'comments': 'Approved with conditions',
            'conditions': ['Deploy during maintenance window'],
        }, format='json')
        
        assert response.status_code == 200
        assert response.data['decision'] == 'CONDITIONAL'
    
    def test_reject_deployment(self, authenticated_client, authenticated_user):
        """Test rejecting a deployment."""
        deployment = DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            status=DeploymentIntent.Status.AWAITING_CAB,
            submitter=authenticated_user,
            is_demo=True,  # Mark as demo for test data
        )
        
        url = f'/api/v1/cab/{deployment.correlation_id}/reject/'
        response = authenticated_client.post(url, {
            'comments': 'Too risky',
        }, format='json')
        
        assert response.status_code == 200
        
        # Verify deployment status updated
        deployment.refresh_from_db()
        assert deployment.status == DeploymentIntent.Status.REJECTED
    
    def test_approve_nonexistent_deployment(self, authenticated_client):
        """Test approving non-existent deployment."""
        url = f'/api/v1/cab/{uuid.uuid4()}/approve/'
        response = authenticated_client.post(url, {
            'comments': 'Test',
        }, format='json')
        
        assert response.status_code == 404

    def test_list_pending_approvals_default(self, authenticated_client, authenticated_user):
        """Test listing pending approvals with default filter."""
        deployment = DeploymentIntent.objects.create(
            app_name='PendingApp',
            version='2.0.0',
            target_ring=DeploymentIntent.Ring.CANARY,
            evidence_pack_id=uuid.uuid4(),
            status=DeploymentIntent.Status.AWAITING_CAB,
            requires_cab_approval=True,
            submitter=authenticated_user,
            is_demo=True,  # Mark as demo for test data
        )

        url = '/api/v1/cab/pending/'
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert 'approvals' in response.data
        assert len(response.data['approvals']) > 0
        # Verify the created deployment is in the list
        approval_ids = [str(a['correlation_id']) for a in response.data['approvals']]
        assert str(deployment.correlation_id) in approval_ids

    def test_list_pending_approvals_filtered_decision(self, authenticated_client, authenticated_user):
        """Test listing pending approvals filtered by decision."""
        deployment = DeploymentIntent.objects.create(
            app_name='ApprovedApp',
            version='3.0.0',
            target_ring=DeploymentIntent.Ring.PILOT,
            evidence_pack_id=uuid.uuid4(),
            status=DeploymentIntent.Status.AWAITING_CAB,
            requires_cab_approval=True,
            submitter=authenticated_user,
            is_demo=True,  # Mark as demo for test data
        )
        CABApproval.objects.create(
            deployment_intent=deployment,
            decision=CABApproval.Decision.APPROVED,
            approver=authenticated_user,
            comments='Approved',
            reviewed_at=deployment.created_at,
        )

        url = '/api/v1/cab/pending/?decision=APPROVED'
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data['approvals'][0]['decision'] == CABApproval.Decision.APPROVED

    def test_list_approvals_with_filter(self, authenticated_client, authenticated_user):
        """Test listing approvals with decision filter."""
        deployment = DeploymentIntent.objects.create(
            app_name='FilterApp',
            version='4.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            status=DeploymentIntent.Status.APPROVED,
            requires_cab_approval=True,
            submitter=authenticated_user,
            is_demo=True,  # Mark as demo for test data
        )
        CABApproval.objects.create(
            deployment_intent=deployment,
            decision=CABApproval.Decision.APPROVED,
            approver=authenticated_user,
            comments='Approved',
            reviewed_at=deployment.created_at,
        )

        url = '/api/v1/cab/approvals/?decision=APPROVED'
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data['approvals'][0]['decision'] == CABApproval.Decision.APPROVED
