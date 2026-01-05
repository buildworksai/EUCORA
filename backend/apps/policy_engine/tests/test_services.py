# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for policy_engine app.
"""
import pytest
from apps.policy_engine.models import RiskModel, RiskAssessment
from apps.policy_engine.services import calculate_risk_score, _evaluate_factor


@pytest.mark.django_db
class TestRiskModel:
    """Test RiskModel model."""
    
    def test_create_risk_model(self):
        """Test creating a risk model."""
        risk_model = RiskModel.objects.create(
            version='v1.0',
            factors=[
                {'name': 'Privilege Elevation', 'weight': 0.15},
                {'name': 'Blast Radius', 'weight': 0.20},
            ],
            threshold=50,
            is_active=True,
        )
        assert risk_model.version == 'v1.0'
        assert len(risk_model.factors) == 2
        assert risk_model.is_active is True
    
    def test_only_one_active_risk_model(self):
        """Test that only one risk model can be active."""
        RiskModel.objects.create(version='v1.0', factors=[], threshold=50, is_active=True)
        RiskModel.objects.create(version='v2.0', factors=[], threshold=60, is_active=True)
        
        active_models = RiskModel.objects.filter(is_active=True)
        assert active_models.count() == 1
        assert active_models.first().version == 'v2.0'


@pytest.mark.django_db
class TestRiskScoring:
    """Test risk scoring logic."""
    
    def setup_method(self):
        """Set up test risk model."""
        self.risk_model = RiskModel.objects.create(
            version='v1.0',
            factors=[
                {'name': 'Privilege Elevation', 'weight': 0.15},
                {'name': 'Blast Radius', 'weight': 0.20},
                {'name': 'Rollback Complexity', 'weight': 0.15},
                {'name': 'Vulnerability Severity', 'weight': 0.20},
                {'name': 'Compliance Impact', 'weight': 0.10},
                {'name': 'Deployment Frequency', 'weight': 0.05},
                {'name': 'Evidence Completeness', 'weight': 0.10},
                {'name': 'Historical Success Rate', 'weight': 0.05},
            ],
            threshold=50,
            is_active=True,
        )
    
    def test_calculate_risk_score_low_risk(self):
        """Test risk score calculation for low-risk deployment."""
        import uuid
        
        evidence_pack = {
            'app_name': 'TestApp',
            'requires_admin': False,
            'target_ring': 'lab',
            'has_rollback_plan': True,
            'rollback_tested': True,
            'vulnerability_scan_results': {'critical': 0, 'high': 0, 'medium': 0},
            'compliance_tags': [],
            'artifact_hash': 'abc123',
            'sbom_data': {'packages': []},
            'rollback_plan': 'Test rollback plan',
        }
        
        result = calculate_risk_score(evidence_pack, str(uuid.uuid4()))
        
        assert result['risk_score'] < 30  # Low risk
        assert result['requires_cab_approval'] is False
        assert 'factor_scores' in result
    
    def test_calculate_risk_score_high_risk(self):
        """Test risk score calculation for high-risk deployment."""
        import uuid
        
        evidence_pack = {
            'app_name': 'TestApp',
            'requires_admin': True,  # High risk
            'target_ring': 'global',  # High risk
            'has_rollback_plan': False,  # High risk
            'vulnerability_scan_results': {'critical': 2, 'high': 5},  # High risk
            'compliance_tags': ['sox', 'hipaa'],  # High risk
            'artifact_hash': '',  # Missing
            'sbom_data': {},  # Missing
            'rollback_plan': '',  # Missing
        }
        
        result = calculate_risk_score(evidence_pack, str(uuid.uuid4()))
        
        assert result['risk_score'] > 70  # High risk
        assert result['requires_cab_approval'] is True
    
    def test_evaluate_privilege_elevation_factor(self):
        """Test privilege elevation factor evaluation."""
        # Requires admin
        assert _evaluate_factor('Privilege Elevation', {'requires_admin': True}, {}) == 1.0
        
        # Requests elevation
        assert _evaluate_factor('Privilege Elevation', {'requests_elevation': True}, {}) == 0.5
        
        # No elevation
        assert _evaluate_factor('Privilege Elevation', {}, {}) == 0.0
    
    def test_evaluate_blast_radius_factor(self):
        """Test blast radius factor evaluation."""
        assert _evaluate_factor('Blast Radius', {'target_ring': 'lab'}, {}) == 0.0
        assert _evaluate_factor('Blast Radius', {'target_ring': 'canary'}, {}) == 0.2
        assert _evaluate_factor('Blast Radius', {'target_ring': 'global'}, {}) == 1.0
    
    def test_evaluate_vulnerability_severity_factor(self):
        """Test vulnerability severity factor evaluation."""
        # Critical vulnerabilities
        assert _evaluate_factor('Vulnerability Severity', {
            'vulnerability_scan_results': {'critical': 1}
        }, {}) == 1.0
        
        # High vulnerabilities
        assert _evaluate_factor('Vulnerability Severity', {
            'vulnerability_scan_results': {'high': 1}
        }, {}) == 0.7
        
        # No vulnerabilities
        assert _evaluate_factor('Vulnerability Severity', {
            'vulnerability_scan_results': {}
        }, {}) == 0.0


@pytest.mark.django_db
class TestRiskAssessment:
    """Test RiskAssessment model."""
    
    def test_create_risk_assessment(self):
        """Test creating a risk assessment."""
        import uuid
        assessment = RiskAssessment.objects.create(
            deployment_intent_id=uuid.uuid4(),
            risk_model_version='v1.0',
            risk_score=75,
            factor_scores={'Privilege Elevation': 1.0},
            requires_cab_approval=True,
        )
        assert assessment.risk_score == 75
        assert assessment.requires_cab_approval is True
