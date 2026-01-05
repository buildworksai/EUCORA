# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for deployment_intents views.
"""
import pytest
from django.urls import reverse
from apps.deployment_intents.models import DeploymentIntent
from apps.policy_engine.models import RiskModel
import uuid


@pytest.mark.django_db
class TestDeploymentIntentsViews:
    """Test deployment intents view endpoints."""
    
    def setup_method(self):
        """Set up test risk model."""
        self.risk_model = RiskModel.objects.create(
            version='v1.0',
            factors=[
                {'name': 'Privilege Elevation', 'weight': 0.5},
                {'name': 'Blast Radius', 'weight': 0.5},
            ],
            threshold=50,
            is_active=True,
        )
    
    def test_create_deployment_low_risk(self, authenticated_client):
        """Test creating low-risk deployment intent."""
        url = reverse('deployment_intents:create')
        response = authenticated_client.post(url, {
            'app_name': 'TestApp',
            'version': '1.0.0',
            'target_ring': 'LAB',
            'evidence_pack': {
                'requires_admin': False,
                'target_ring': 'lab',
                'artifact_hash': 'abc123',
                'sbom_data': {'packages': []},
                'vulnerability_scan_results': {},
                'rollback_plan': 'Test plan',
            },
        }, format='json')
        
        assert response.status_code == 201
        assert 'correlation_id' in response.data
        assert response.data['requires_cab_approval'] is False
    
    def test_create_deployment_high_risk(self, authenticated_client):
        """Test creating high-risk deployment intent."""
        url = reverse('deployment_intents:create')
        response = authenticated_client.post(url, {
            'app_name': 'TestApp',
            'version': '1.0.0',
            'target_ring': 'GLOBAL',
            'evidence_pack': {
                'requires_admin': True,
                'target_ring': 'global',
                'artifact_hash': '',
                'sbom_data': {},
                'vulnerability_scan_results': {'critical': 5},
                'rollback_plan': '',
            },
        }, format='json')
        
        assert response.status_code == 201
        assert response.data['requires_cab_approval'] is True
        assert response.data['risk_score'] > 50
    
    def test_create_deployment_missing_fields(self, authenticated_client):
        """Test creating deployment with missing required fields."""
        url = reverse('deployment_intents:create')
        response = authenticated_client.post(url, {
            'app_name': 'TestApp',
        }, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    def test_list_deployments(self, authenticated_client, authenticated_user):
        """Test listing deployment intents."""
        # Create test deployment
        DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            submitter=authenticated_user,
        )
        
        url = reverse('deployment_intents:list')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'deployments' in response.data
        assert len(response.data['deployments']) > 0
    
    def test_list_deployments_with_filters(self, authenticated_client, authenticated_user):
        """Test listing deployments with status filter."""
        DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            status=DeploymentIntent.Status.APPROVED,
            submitter=authenticated_user,
        )
        
        url = reverse('deployment_intents:list')
        response = authenticated_client.get(url, {'status': 'APPROVED'})
        
        assert response.status_code == 200
        assert len(response.data['deployments']) > 0
    
    def test_get_deployment(self, authenticated_client, authenticated_user):
        """Test getting deployment intent details."""
        deployment = DeploymentIntent.objects.create(
            app_name='TestApp',
            version='1.0.0',
            target_ring=DeploymentIntent.Ring.LAB,
            evidence_pack_id=uuid.uuid4(),
            submitter=authenticated_user,
        )
        
        url = reverse('deployment_intents:get', kwargs={'correlation_id': deployment.correlation_id})
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert response.data['app_name'] == 'TestApp'
    
    def test_get_deployment_not_found(self, authenticated_client):
        """Test getting non-existent deployment."""
        url = reverse('deployment_intents:get', kwargs={'correlation_id': uuid.uuid4()})
        response = authenticated_client.get(url)
        
        assert response.status_code == 404
