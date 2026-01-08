# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for CAB workflow views.
"""
import pytest
from django.urls import reverse
from apps.deployment_intents.models import DeploymentIntent
from apps.cab_workflow.models import CABApproval
import uuid


@pytest.mark.django_db
class TestCABWorkflowViews:
    """Test CAB workflow view endpoints."""
    
    def test_approve_deployment(self, authenticated_client, authenticated_user):
        """Test approving a deployment."""
        deployment = DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            status=DeploymentIntent.Status.AWAITING_CAB,
            submitter=authenticated_user,
        )
        
        url = reverse('cab_workflow:approve', kwargs={'correlation_id': deployment.correlation_id})
        response = authenticated_client.post(url, {
            'comments': 'Looks good',
        }, format='json')
        
        assert response.status_code == 200
        assert 'message' in response.data
        
        # Verify deployment status updated
        deployment.refresh_from_db()
        assert deployment.status == DeploymentIntent.Status.APPROVED
    
    def test_approve_deployment_with_conditions(self, authenticated_client, authenticated_user):
        """Test conditional approval."""
        deployment = DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            submitter=authenticated_user,
        )
        
        url = reverse('cab_workflow:approve', kwargs={'correlation_id': deployment.correlation_id})
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
        )
        
        url = reverse('cab_workflow:reject', kwargs={'correlation_id': deployment.correlation_id})
        response = authenticated_client.post(url, {
            'comments': 'Too risky',
        }, format='json')
        
        assert response.status_code == 200
        
        # Verify deployment status updated
        deployment.refresh_from_db()
        assert deployment.status == DeploymentIntent.Status.REJECTED
    
    def test_approve_nonexistent_deployment(self, authenticated_client):
        """Test approving non-existent deployment."""
        url = reverse('cab_workflow:approve', kwargs={'correlation_id': uuid.uuid4()})
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
        )

        url = reverse('cab_workflow:pending')
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert len(response.data['approvals']) == 1
        assert response.data['approvals'][0]['correlation_id'] == str(deployment.correlation_id)

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
        )
        CABApproval.objects.create(
            deployment_intent=deployment,
            decision=CABApproval.Decision.APPROVED,
            approver=authenticated_user,
            comments='Approved',
            reviewed_at=deployment.created_at,
        )

        url = reverse('cab_workflow:pending') + '?decision=APPROVED'
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
        )
        CABApproval.objects.create(
            deployment_intent=deployment,
            decision=CABApproval.Decision.APPROVED,
            approver=authenticated_user,
            comments='Approved',
            reviewed_at=deployment.created_at,
        )

        url = reverse('cab_workflow:list') + '?decision=APPROVED'
        response = authenticated_client.get(url)

        assert response.status_code == 200
        assert response.data['approvals'][0]['decision'] == CABApproval.Decision.APPROVED
