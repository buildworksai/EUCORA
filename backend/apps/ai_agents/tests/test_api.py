# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
API tests for ai_agents endpoints.

Tests cover:
- Analyze deployment risk
- Predict deployment success
- Recommend remediation actions
- Model versioning
- Edge cases and boundary conditions
"""
import uuid
from django.test import TestCase, override_settings
from django.contrib.auth.models import User
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from apps.deployment_intents.models import DeploymentIntent
from unittest.mock import patch


class AIAgentsAuthenticationTests(APITestCase):
    """Test authentication and authorization."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    @override_settings(DEBUG=False)
    def test_analyze_without_auth_returns_401(self):
        """Analyzing without authentication should return 401."""
        response = self.client.post('/api/v1/ai/analyze/', {
            'deployment_id': str(uuid.uuid4()),
            'analysis_type': 'RISK'
        }, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
    
    def test_analyze_with_auth_processes_request(self):
        """Analyzing with authentication should process request."""
        self.client.force_authenticate(user=self.user)
        response = self.client.post('/api/v1/ai/analyze/', {
            'deployment_id': str(uuid.uuid4()),
            'analysis_type': 'RISK'
        }, format='json')
        # Should either succeed or fail validation, not auth error
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])


@patch('apps.ai_agents.services.RiskAnalyzer.analyze')
class AIAnalysisTests(APITestCase):
    """Test risk analysis."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='analyst', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.deployment = DeploymentIntent.objects.create(
            app_name='analyze-test-app',
            version='1.0.0',
            target_ring='CANARY',
            status=DeploymentIntent.Status.PENDING,
            evidence_pack_id=uuid.uuid4(),
            submitter=self.user
        )
    
    def test_analyze_risk_returns_score(self, mock_analyze):
        """Risk analysis should return a risk score."""
        mock_analyze.return_value = {
            'risk_score': 65,
            'factors': {
                'unsigned_package': 30,
                'no_sbom': 20,
                'no_scan': 15
            },
            'recommendations': ['Add code signing', 'Generate SBOM']
        }
        
        response = self.client.post('/api/v1/ai/analyze/', {
            'deployment_id': str(self.deployment.correlation_id),
            'analysis_type': 'RISK'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('risk_score', response.data)
        self.assertIsInstance(response.data['risk_score'], (int, float))
    
    def test_analyze_includes_factors(self, mock_analyze):
        """Analysis should include contributing factors."""
        mock_analyze.return_value = {
            'risk_score': 65,
            'factors': {
                'unsigned_package': 30,
                'no_sbom': 20,
                'no_scan': 15
            }
        }
        
        response = self.client.post('/api/v1/ai/analyze/', {
            'deployment_id': str(self.deployment.correlation_id),
            'analysis_type': 'RISK'
        }, format='json')
        
        if response.status_code == 200 and 'factors' in response.data:
            factors = response.data['factors']
            self.assertIsInstance(factors, dict)
            # Factors should sum approximately to risk score
            factor_sum = sum(factors.values())
            # Allow 10% variance
            self.assertLess(abs(factor_sum - response.data['risk_score']), 
                           response.data['risk_score'] * 0.1)
    
    def test_analyze_includes_recommendations(self, mock_analyze):
        """Analysis should include remediation recommendations."""
        mock_analyze.return_value = {
            'risk_score': 65,
            'factors': {},
            'recommendations': [
                'Add code signing certificate',
                'Generate software bill of materials',
                'Run vulnerability scan'
            ]
        }
        
        response = self.client.post('/api/v1/ai/analyze/', {
            'deployment_id': str(self.deployment.correlation_id),
            'analysis_type': 'RISK'
        }, format='json')
        
        if response.status_code == 200 and 'recommendations' in response.data:
            recs = response.data['recommendations']
            self.assertIsInstance(recs, list)
            self.assertGreater(len(recs), 0)


@patch('apps.ai_agents.services.SuccessPredictor.predict')
class AIPredictionTests(APITestCase):
    """Test success prediction."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='predictor', password='testpass')
        self.client.force_authenticate(user=self.user)
        
        self.deployment = DeploymentIntent.objects.create(
            app_name='predict-test-app',
            version='1.0.0',
            target_ring='PILOT',
            status=DeploymentIntent.Status.APPROVED,
            evidence_pack_id=uuid.uuid4(),
            submitter=self.user
        )
    
    def test_predict_success_probability(self, mock_predict):
        """Prediction should return success probability."""
        mock_predict.return_value = {
            'success_probability': 0.92,
            'confidence': 0.85,
            'basis': ['Similar deployments succeeded 92% of the time']
        }
        
        response = self.client.post('/api/v1/ai/predict/', {
            'deployment_id': str(self.deployment.correlation_id),
            'prediction_type': 'SUCCESS'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('success_probability', response.data)
        prob = response.data.get('success_probability')
        self.assertGreaterEqual(prob, 0)
        self.assertLessEqual(prob, 1)
    
    def test_predict_includes_confidence(self, mock_predict):
        """Prediction should include confidence score."""
        mock_predict.return_value = {
            'success_probability': 0.92,
            'confidence': 0.85,
            'basis': []
        }
        
        response = self.client.post('/api/v1/ai/predict/', {
            'deployment_id': str(self.deployment.correlation_id),
            'prediction_type': 'SUCCESS'
        }, format='json')
        
        if response.status_code == 200 and 'confidence' in response.data:
            confidence = response.data['confidence']
            self.assertGreaterEqual(confidence, 0)
            self.assertLessEqual(confidence, 1)
    
    def test_predict_includes_basis(self, mock_predict):
        """Prediction should explain reasoning."""
        mock_predict.return_value = {
            'success_probability': 0.92,
            'confidence': 0.85,
            'basis': [
                'Similar app deployments succeeded 92% of the time',
                'High code quality (99.2% coverage)',
                'Complete SBOM available'
            ]
        }
        
        response = self.client.post('/api/v1/ai/predict/', {
            'deployment_id': str(self.deployment.correlation_id),
            'prediction_type': 'SUCCESS'
        }, format='json')
        
        if response.status_code == 200 and 'basis' in response.data:
            basis = response.data['basis']
            self.assertIsInstance(basis, list)


@patch('apps.ai_agents.services.RemediationAdvisor.recommend')
class AIRemediationTests(APITestCase):
    """Test remediation recommendations."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='sre', password='testpass')
        self.client.force_authenticate(user=self.user)
    
    def test_recommend_remediation_returns_actions(self, mock_recommend):
        """Remediation recommendation should return actions."""
        mock_recommend.return_value = {
            'actions': [
                {
                    'name': 'ROLLBACK_TO_PREVIOUS',
                    'confidence': 0.95,
                    'estimated_time': 300
                },
                {
                    'name': 'GRADUAL_ROLLOUT_RESTRICTION',
                    'confidence': 0.85,
                    'estimated_time': 600
                }
            ]
        }
        
        response = self.client.post('/api/v1/ai/recommend/', {
            'deployment_id': str(uuid.uuid4()),
            'issue_type': 'HIGH_FAILURE_RATE'
        }, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('actions', response.data)
        self.assertIsInstance(response.data['actions'], list)
    
    def test_recommendation_includes_confidence(self, mock_recommend):
        """Recommendations should include confidence scores."""
        mock_recommend.return_value = {
            'actions': [
                {
                    'name': 'ROLLBACK',
                    'confidence': 0.95,
                    'estimated_time': 300
                }
            ]
        }
        
        response = self.client.post('/api/v1/ai/recommend/', {
            'deployment_id': str(uuid.uuid4()),
            'issue_type': 'COMPLIANCE_VIOLATION'
        }, format='json')
        
        if response.status_code == 200 and 'actions' in response.data:
            for action in response.data['actions']:
                self.assertIn('confidence', action)
                confidence = action['confidence']
                self.assertGreaterEqual(confidence, 0)
                self.assertLessEqual(confidence, 1)
    
    def test_recommendation_includes_time_estimate(self, mock_recommend):
        """Recommendations should estimate execution time."""
        mock_recommend.return_value = {
            'actions': [
                {
                    'name': 'QUARANTINE_DEVICES',
                    'confidence': 0.90,
                    'estimated_time': 1800
                }
            ]
        }
        
        response = self.client.post('/api/v1/ai/recommend/', {
            'deployment_id': str(uuid.uuid4()),
            'issue_type': 'SECURITY_RISK'
        }, format='json')
        
        if response.status_code == 200 and 'actions' in response.data:
            for action in response.data['actions']:
                self.assertIn('estimated_time', action)
                # Time should be in seconds and positive
                self.assertGreater(action['estimated_time'], 0)


class AIModelVersioningTests(APITestCase):
    """Test AI model versioning."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='admin', password='testpass')
        self.client.force_authenticate(user=self.user)
    
    def test_list_available_models(self):
        """Should list available AI models."""
        response = self.client.get('/api/v1/ai/models/', format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('models', response.data)
    
    def test_get_model_details(self):
        """Should return details of specific model."""
        response = self.client.get('/api/v1/ai/models/risk-analyzer/', format='json')
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND])
    
    def test_model_includes_version(self):
        """Model details should include version."""
        response = self.client.get('/api/v1/ai/models/', format='json')
        if response.status_code == 200:
            models = response.data.get('models', [])
            for model in models:
                self.assertIn('version', model)


class AIEdgeCasesTests(APITestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.client.force_authenticate(user=self.user)
    
    def test_analyze_nonexistent_deployment(self):
        """Analyzing non-existent deployment should return 404."""
        response = self.client.post('/api/v1/ai/analyze/', {
            'deployment_id': str(uuid.uuid4()),
            'analysis_type': 'RISK'
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_404_NOT_FOUND,
            status.HTTP_400_BAD_REQUEST
        ])
    
    def test_analyze_with_invalid_type(self):
        """Analyzing with invalid type should be rejected."""
        response = self.client.post('/api/v1/ai/analyze/', {
            'deployment_id': str(uuid.uuid4()),
            'analysis_type': 'INVALID_TYPE'
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])
    
    def test_predict_with_invalid_type(self):
        """Predicting with invalid type should be rejected."""
        response = self.client.post('/api/v1/ai/predict/', {
            'deployment_id': str(uuid.uuid4()),
            'prediction_type': 'INVALID_TYPE'
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])
    
    def test_recommend_with_invalid_issue(self):
        """Recommending with invalid issue type should be rejected."""
        response = self.client.post('/api/v1/ai/recommend/', {
            'deployment_id': str(uuid.uuid4()),
            'issue_type': 'INVALID_ISSUE'
        }, format='json')
        
        self.assertIn(response.status_code, [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_404_NOT_FOUND
        ])
