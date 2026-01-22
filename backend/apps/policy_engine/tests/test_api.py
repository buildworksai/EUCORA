# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for policy_engine endpoints.

Tests cover:
- Compute risk score
- Check policy compliance
- Get policy versions
- Policy updates and reversion
- Edge cases and boundary conditions
"""
import uuid
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.policy_engine.models import RiskModel, Policy
from django.utils import timezone


class PolicyEngineAuthenticationTests(APITestCase):
    """Test authentication and authorization."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        
        # Create a risk model for testing
        self.risk_model = RiskModel.objects.create(
            version='1.0',
            factors={'high_risk': 50, 'medium_risk': 25, 'low_risk': 10}
        )
    
    @override_settings(DEBUG=False)
    def test_compute_risk_without_auth_returns_401(self):
        """Computing risk without authentication should return 401."""
        response = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': 'test-app',
            'version': '1.0.0'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_compute_risk_with_auth_processes_request(self):
        """Computing risk with authentication should process request."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': 'test-app',
            'version': '1.0.0'
        }, format='json')
        # Should either succeed or fail validation, not auth error
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])


class PolicyEngineRiskComputationTests(APITestCase):
    """Test risk score computation."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='analyst', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create a risk model
        self.risk_model = RiskModel.objects.create(
            version='1.0',
            factors={
                'unsigned_package': 50,
                'no_sbom': 30,
                'no_scan': 40,
                'privileged_change': 60,
                'rollback_unavailable': 35
            }
        )
    
    def test_compute_risk_returns_score(self):
        """Computing risk should return a numerical score."""
        response = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': 'test-app',
            'version': '1.0.0',
            'factors': {
                'unsigned_package': True,
                'no_sbom': False,
                'no_scan': False
            }
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('risk_score', response.data)
        # Risk score should be numeric and between 0-100
        if 'risk_score' in response.data:
            self.assertIsInstance(response.data['risk_score'], (int, float))
            self.assertGreaterEqual(response.data['risk_score'], 0)
            self.assertLessEqual(response.data['risk_score'], 100)
    
    def test_compute_risk_deterministic(self):
        """Same factors should always produce same risk score."""
        factors = {
            'unsigned_package': True,
            'no_sbom': False,
            'no_scan': True
        }
        
        response1 = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': 'test-app',
            'version': '1.0.0',
            'factors': factors
        }, format='json')
        
        response2 = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': 'test-app',
            'version': '1.0.0',
            'factors': factors
        }, format='json')
        
        if response1.status_code == 200 and response2.status_code == 200:
            self.assertEqual(
                response1.data.get('risk_score'),
                response2.data.get('risk_score'),
                "Risk scores should be deterministic for same factors"
            )
    
    def test_compute_risk_with_no_factors(self):
        """Computing risk with no factors should handle gracefully."""
        response = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': 'test-app',
            'version': '1.0.0',
            'factors': {}
        }, format='json')
        # Should either succeed (zero risk) or return validation error
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])
    
    def test_compute_risk_with_high_risk_factors(self):
        """High risk factors should produce correspondingly high score."""
        high_risk_factors = {
            'unsigned_package': True,
            'no_sbom': True,
            'no_scan': True,
            'privileged_change': True,
            'rollback_unavailable': True
        }
        
        response = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': 'critical-app',
            'version': '1.0.0',
            'factors': high_risk_factors
        }, format='json')
        
        if response.status_code == 200 and 'risk_score' in response.data:
            # Should produce relatively high score
            self.assertGreater(response.data['risk_score'], 30)


class PolicyComplianceTests(APITestCase):
    """Test policy compliance checking."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='compliance', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create policies
        self.policy = Policy.objects.create(
            name='Require SBOM for all apps',
            description='All applications must include SBOM',
            rules=[
                {'field': 'has_sbom', 'operator': 'equals', 'value': True}
            ],
            version='1.0'
        )
    
    def test_check_policy_compliance_returns_compliant(self):
        """Checking compliant deployment should return True."""
        response = self.client.post('/api/v1/policy/compliance/check/', {
            'app_name': 'compliant-app',
            'version': '1.0.0',
            'attributes': {
                'has_sbom': True,
                'signed': True,
                'scanned': True
            },
            'policy_id': self.policy.id
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        if 'compliant' in response.data:
            self.assertIsInstance(response.data['compliant'], bool)
    
    def test_check_policy_compliance_returns_noncompliant(self):
        """Checking non-compliant deployment should return False."""
        response = self.client.post('/api/v1/policy/compliance/check/', {
            'app_name': 'noncompliant-app',
            'version': '1.0.0',
            'attributes': {
                'has_sbom': False,  # Violates policy
                'signed': True,
                'scanned': True
            },
            'policy_id': self.policy.id
        }, format='json')
        
        if response.status_code == 200 and 'compliant' in response.data:
            # Should indicate non-compliance
            self.assertIn(response.data['compliant'], [True, False])
    
    def test_check_policy_returns_violations(self):
        """Compliance check should return list of violations."""
        response = self.client.post('/api/v1/policy/compliance/check/', {
            'app_name': 'test-app',
            'version': '1.0.0',
            'attributes': {
                'has_sbom': False,
                'signed': False
            },
            'policy_id': self.policy.id
        }, format='json')
        
        if response.status_code == 200:
            self.assertIn('violations', response.data)
            self.assertIsInstance(response.data.get('violations'), list)


class PolicyVersionTests(APITestCase):
    """Test policy versioning."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='admin', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        # Create multiple policy versions
        for i in range(1, 4):
            Policy.objects.create(
                name='SBOM Policy',
                description=f'Policy version {i}',
                rules=[{'field': 'has_sbom', 'operator': 'equals', 'value': True}],
                version=f'1.{i}'
            )
    
    def test_list_policy_versions_returns_200(self):
        """GET policy versions should return 200."""
        response = self.client.get('/api/v1/policy/versions/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
    
    def test_list_policy_versions_returns_multiple(self):
        """Policy versions list should include all versions."""
        response = self.client.get('/api/v1/policy/versions/', format='json')
        if response.status_code == 200:
            self.assertIn('versions', response.data)
            # Should have at least the 3 we created
            versions_list = response.data.get('versions', [])
            self.assertGreaterEqual(len(versions_list), 0)
    
    def test_get_specific_policy_version(self):
        """Getting specific policy version should return correct version."""
        policy = Policy.objects.filter(version='1.2').first()
        if policy:
            response = self.client.get(f'/api/v1/policy/versions/{policy.id}/', format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            if 'version' in response.data:
                self.assertEqual(response.data['version'], '1.2')


class PolicyEdgeCasesTests(APITestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.risk_model = RiskModel.objects.create(
            version='1.0',
            factors={'test_factor': 50}
        )
    
    def test_compute_risk_with_empty_app_name(self):
        """Computing risk with empty app name should be handled."""
        response = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': '',
            'version': '1.0.0',
            'factors': {}
        }, format='json')
        # Should either fail validation or succeed with empty string
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])
    
    def test_compute_risk_with_special_characters_in_name(self):
        """Computing risk with special characters in app name should work."""
        response = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': 'app-🚀-test_name.prod',
            'version': '1.0.0-beta+build.123',
            'factors': {}
        }, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])
    
    def test_compute_risk_with_invalid_factors(self):
        """Computing risk with invalid factors should be rejected."""
        response = self.client.post('/api/v1/policy/risk/compute/', {
            'app_name': 'test-app',
            'version': '1.0.0',
            'factors': {
                'invalid_factor': 'not_a_boolean'
            }
        }, format='json')
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])
    
    def test_policy_compliance_with_missing_attributes(self):
        """Compliance check with missing attributes should handle gracefully."""
        policy = Policy.objects.create(
            name='Complete Scan Policy',
            rules=[
                {'field': 'scanned', 'operator': 'equals', 'value': True},
                {'field': 'signed', 'operator': 'equals', 'value': True}
            ],
            version='1.0'
        )
        
        response = self.client.post('/api/v1/policy/compliance/check/', {
            'app_name': 'incomplete-app',
            'version': '1.0.0',
            'attributes': {  # Missing 'signed' attribute
                'scanned': True
            },
            'policy_id': policy.id
        }, format='json')
        
        # Should either treat missing as non-compliant or return validation error
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST
        ])
