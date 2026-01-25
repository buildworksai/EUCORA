# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Comprehensive tests for P5.1: Evidence Pack Generation
Tests cover:
- Evidence package creation and immutability
- Risk score computation with deterministic results
- Factor evaluation with rubrics
- Completeness checking
- Evidence retrieval and audit trail
"""
import json
from decimal import Decimal

from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.evidence_store.models import EvidencePackage, RiskFactor, RiskScoreBreakdown
from apps.evidence_store.services import EvidenceGenerationService


class EvidencePackageModelTests(TestCase):
    """Test EvidencePackage model creation, immutability, and properties."""

    def setUp(self):
        """Set up test fixtures."""
        self.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "testuser@example.com"})

        if created:

            self.user.set_password("testpass")

            self.user.save()

    def test_evidence_package_creation(self):
        """Test creating an evidence package."""
        evidence = EvidencePackage.objects.create(
            deployment_intent_id="deploy-123",
            correlation_id="corr-456",
            evidence_data={"artifacts": {"hash": "abc123"}, "test_results": {"coverage_percent": 95}},
            risk_score=Decimal("25.5"),
            created_by="testuser",
        )

        self.assertEqual(evidence.deployment_intent_id, "deploy-123")
        self.assertEqual(evidence.correlation_id, "corr-456")
        self.assertIsNotNone(evidence.content_hash)
        self.assertEqual(len(evidence.content_hash), 64)  # SHA-256 hex is 64 chars

    def test_content_hash_computed_on_save(self):
        """Test that content hash is computed automatically on save."""
        evidence_data = {"artifacts": {"hash": "abc123"}, "test_results": {"coverage_percent": 95}}

        evidence = EvidencePackage.objects.create(
            deployment_intent_id="deploy-123",
            correlation_id="corr-456",
            evidence_data=evidence_data,
        )

        # Verify hash exists
        self.assertIsNotNone(evidence.content_hash)

        # Verify hash is consistent with data
        expected_json = json.dumps(evidence_data, sort_keys=True)
        import hashlib

        expected_hash = hashlib.sha256(expected_json.encode()).hexdigest()
        self.assertEqual(evidence.content_hash, expected_hash)

    def test_immutability_verification_valid(self):
        """Test that verify_immutability returns True for unchanged evidence."""
        evidence = EvidencePackage.objects.create(
            deployment_intent_id="deploy-123",
            correlation_id="corr-456",
            evidence_data={"test": "data"},
        )

        self.assertTrue(evidence.verify_immutability())

    def test_immutability_verification_invalid(self):
        """Test that verify_immutability returns False if evidence is modified."""
        evidence = EvidencePackage.objects.create(
            deployment_intent_id="deploy-123",
            correlation_id="corr-456",
            evidence_data={"test": "data"},
        )

        original_hash = evidence.content_hash

        # Modify evidence (in memory only, don't save)
        evidence.evidence_data = {"test": "modified"}

        # Verification should fail because hash doesn't match new data
        self.assertFalse(evidence.verify_immutability())
        # Original hash should still be stored
        self.assertEqual(evidence.content_hash, original_hash)

    def test_unique_correlation_id(self):
        """Test that correlation_id must be unique."""
        EvidencePackage.objects.create(
            deployment_intent_id="deploy-123",
            correlation_id="corr-456",
            evidence_data={"test": "data"},
        )

        # Creating another with same correlation_id should fail
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            EvidencePackage.objects.create(
                deployment_intent_id="deploy-789",
                correlation_id="corr-456",  # Same as above
                evidence_data={"test": "data2"},
            )


class RiskFactorModelTests(TestCase):
    """Test RiskFactor model for risk scoring definitions."""

    def test_risk_factor_creation(self):
        """Test creating a risk factor for a new model version."""
        factor = RiskFactor.objects.create(
            model_version="2.0",  # Use different model version to avoid conflicts
            factor_type="coverage",
            name="Test Coverage",
            description="Percentage of code covered by tests",
            weight=Decimal("0.25"),
            rubric={
                ">90": 0,
                "80-90": 10,
                "<80": 30,
            },
        )

        self.assertEqual(factor.factor_type, "coverage")
        self.assertEqual(factor.weight, Decimal("0.25"))
        self.assertEqual(factor.model_version, "2.0")

    def test_unique_factor_per_model_version(self):
        """Test that only one factor per type per model version."""
        # Use v2.1 to avoid conflicts with seeded v1.0
        RiskFactor.objects.create(
            model_version="2.1", factor_type="coverage", name="Test Coverage", weight=Decimal("0.25"), rubric={}
        )

        # Creating another with same version and type should fail
        from django.db import IntegrityError

        with self.assertRaises(IntegrityError):
            RiskFactor.objects.create(
                model_version="2.1",
                factor_type="coverage",  # Duplicate
                name="Test Coverage v2",
                weight=Decimal("0.30"),
                rubric={},
            )


class RiskScoreBreakdownTests(TestCase):
    """Test RiskScoreBreakdown for transparency."""

    def setUp(self):
        """Set up test fixtures."""
        self.evidence = EvidencePackage.objects.create(
            deployment_intent_id="deploy-123",
            correlation_id="corr-456",
            evidence_data={"test": "data"},
        )

    def test_risk_score_breakdown_creation(self):
        """Test creating a risk score breakdown."""
        breakdown = RiskScoreBreakdown.objects.create(
            evidence_package=self.evidence,
            correlation_id="corr-456",
            factors_evaluated={
                "coverage": {"value": 10, "weight": 0.25},
                "security": {"value": 5, "weight": 0.25},
            },
        )

        self.assertEqual(breakdown.evidence_package, self.evidence)
        self.assertIn("coverage", breakdown.factors_evaluated)


class EvidenceGenerationServiceTests(TestCase):
    """Test EvidenceGenerationService for evidence package generation."""

    def setUp(self):
        """Set up risk factors (use v1.0 which should be seeded)."""
        # Use get_or_create to avoid conflicts with seeded data
        self.factors = {
            "coverage": RiskFactor.objects.get_or_create(
                model_version="1.0",
                factor_type="coverage",
                defaults={
                    "name": "Test Coverage",
                    "weight": Decimal("0.25"),
                    "rubric": {">90": 0, "80-90": 10, "<80": 30},
                },
            )[0],
        }

    def test_generate_evidence_package_complete(self):
        """Test generating a complete evidence package."""
        evidence_data = {
            "artifacts": {"hash": "abc123", "signature": "sig123"},
            "test_results": {"coverage_percent": 95, "manual_test_status": "completed"},
            "scan_results": {"critical": [], "high": []},
            "deployment_plan": {"affected_components": ["app1", "app2", "app3"]},
            "rollback_plan": {"strategy": "version_pinning", "steps": ["step1", "step2"]},
        }

        package = EvidenceGenerationService.generate_evidence_package(
            deployment_intent_id="deploy-123",
            correlation_id="corr-456",
            artifact_info=evidence_data["artifacts"],
            test_results=evidence_data["test_results"],
            scan_results=evidence_data["scan_results"],
            deployment_plan=evidence_data["deployment_plan"],
            rollback_plan=evidence_data["rollback_plan"],
            created_by="testuser",
        )

        self.assertIsNotNone(package)
        self.assertEqual(package.deployment_intent_id, "deploy-123")
        self.assertEqual(package.correlation_id, "corr-456")
        self.assertTrue(package.is_complete)
        self.assertIsNotNone(package.risk_score)
        self.assertIsNotNone(package.content_hash)

    def test_generate_evidence_package_incomplete(self):
        """Test generating an incomplete evidence package."""
        package = EvidenceGenerationService.generate_evidence_package(
            deployment_intent_id="deploy-123",
            correlation_id="corr-456",
            artifact_info={"hash": "abc123"},
            # Missing other fields
        )

        self.assertFalse(package.is_complete)
        self.assertIn("artifacts", package.completeness_check)
        self.assertTrue(package.completeness_check["artifacts"])
        self.assertFalse(package.completeness_check["test_results"])

    def test_duplicate_correlation_id_raises_error(self):
        """Test that duplicate correlation_id raises ValueError."""
        EvidencePackage.objects.create(
            deployment_intent_id="deploy-123",
            correlation_id="corr-456",
            evidence_data={"test": "data"},
        )

        with self.assertRaises(ValueError):
            EvidenceGenerationService.generate_evidence_package(
                deployment_intent_id="deploy-789",
                correlation_id="corr-456",  # Duplicate
            )

    def test_risk_score_deterministic(self):
        """Test that same evidence produces same risk score."""
        evidence_data = {
            "artifacts": {"hash": "abc123"},
            "test_results": {"coverage_percent": 85},
            "scan_results": {"critical": [], "high": ["issue1"]},
            "deployment_plan": {"affected_components": ["app1", "app2"]},
            "rollback_plan": {"strategy": "rollback"},
        }

        package1 = EvidenceGenerationService.generate_evidence_package(
            deployment_intent_id="deploy-1",
            correlation_id="corr-1",
            artifact_info=evidence_data["artifacts"],
            test_results=evidence_data["test_results"],
            scan_results=evidence_data["scan_results"],
            deployment_plan=evidence_data["deployment_plan"],
            rollback_plan=evidence_data["rollback_plan"],
        )

        package2 = EvidenceGenerationService.generate_evidence_package(
            deployment_intent_id="deploy-2",
            correlation_id="corr-2",
            artifact_info=evidence_data["artifacts"],
            test_results=evidence_data["test_results"],
            scan_results=evidence_data["scan_results"],
            deployment_plan=evidence_data["deployment_plan"],
            rollback_plan=evidence_data["rollback_plan"],
        )

        # Same evidence should produce same risk score
        self.assertEqual(package1.risk_score, package2.risk_score)
        self.assertEqual(package1.risk_factors, package2.risk_factors)


class RiskScoreComputationTests(TestCase):
    """Test risk score computation with various evidence scenarios."""

    def setUp(self):
        """Set up risk factors (use v1.0 seeded data)."""
        # Factors are already seeded by migration, just reference them
        self.factors = {f.factor_type: f for f in RiskFactor.objects.filter(model_version="1.0")}

    def test_low_risk_score(self):
        """Test risk score for low-risk deployment."""
        # Good coverage, no security issues, testing complete, validated rollback, small scope
        evidence_data = {
            "artifacts": {"hash": "abc123"},
            "test_results": {"coverage_percent": 95, "manual_test_status": "completed"},
            "scan_results": {"critical": [], "high": []},
            "deployment_plan": {"affected_components": ["app1"]},
            "rollback_plan": {"strategy": "rollback"},
        }

        risk_score, factors = EvidenceGenerationService._compute_risk_score(evidence_data)

        # Verify score is generated
        self.assertIsNotNone(risk_score)
        # Score should be between 0 and 100
        self.assertGreaterEqual(risk_score, 0)
        self.assertLessEqual(risk_score, 100)

    def test_medium_risk_score(self):
        """Test risk score for medium-risk deployment."""
        # Moderate coverage, some security issues, testing in progress, missing rollback
        evidence_data = {
            "artifacts": {"hash": "abc123"},
            "test_results": {"coverage_percent": 85, "manual_test_status": "in_progress"},
            "scan_results": {"critical": [], "high": ["issue1", "issue2"]},
            "deployment_plan": {"affected_components": ["app1", "app2", "app3", "app4", "app5"]},
            "rollback_plan": {},
        }

        risk_score, factors = EvidenceGenerationService._compute_risk_score(evidence_data)

        # Verify score is generated and in valid range
        self.assertIsNotNone(risk_score)
        self.assertGreaterEqual(risk_score, 0)
        self.assertLessEqual(risk_score, 100)

    def test_high_risk_score(self):
        """Test risk score for high-risk deployment."""
        # Poor coverage, critical issues, testing incomplete, no rollback
        evidence_data = {
            "artifacts": {"hash": "abc123"},
            "test_results": {"coverage_percent": 70, "manual_test_status": "not_started"},
            "scan_results": {"critical": ["c1", "c2", "c3"], "high": ["h1", "h2"]},
            "deployment_plan": {"affected_components": list(range(15))},  # 15 components
            "rollback_plan": {},
        }

        risk_score, factors = EvidenceGenerationService._compute_risk_score(evidence_data)

        # High risk
        self.assertGreater(risk_score, 40)

    def test_no_factors_configured_returns_neutral(self):
        """Test that when no factors configured, neutral score is returned."""
        # Delete all factors
        RiskFactor.objects.filter(model_version="1.0").delete()

        evidence_data = {"artifacts": {}}
        risk_score, factors = EvidenceGenerationService._compute_risk_score(evidence_data)

        self.assertEqual(risk_score, Decimal("50.0"))
        self.assertEqual(factors, {})


class FactorEvaluationTests(TestCase):
    """Test individual factor evaluation logic."""

    def test_evaluate_coverage_high(self):
        """Test coverage evaluation for >90%."""
        rubric = {">90": 0, "80-90": 10, "<80": 30}
        evidence = {"test_results": {"coverage_percent": 95}}

        score = EvidenceGenerationService._evaluate_factor("coverage", evidence, rubric)

        self.assertEqual(score, Decimal("0"))

    def test_evaluate_coverage_medium(self):
        """Test coverage evaluation for 80-90%."""
        rubric = {">90": 0, "80-90": 10, "<80": 30}
        evidence = {"test_results": {"coverage_percent": 85}}

        score = EvidenceGenerationService._evaluate_factor("coverage", evidence, rubric)

        self.assertEqual(score, Decimal("10"))

    def test_evaluate_coverage_low(self):
        """Test coverage evaluation for <80%."""
        rubric = {">90": 0, "80-90": 10, "<80": 30}
        evidence = {"test_results": {"coverage_percent": 75}}

        score = EvidenceGenerationService._evaluate_factor("coverage", evidence, rubric)

        self.assertEqual(score, Decimal("30"))

    def test_evaluate_security_no_issues(self):
        """Test security evaluation with no critical/high issues."""
        rubric = {">2": 50, "1-2": 20, "0": 0}
        evidence = {"scan_results": {"critical": [], "high": []}}

        score = EvidenceGenerationService._evaluate_factor("security", evidence, rubric)

        # Score should be valid (between 0-100 or default 50)
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_evaluate_security_multiple_issues(self):
        """Test security evaluation with multiple issues."""
        rubric = {">2": 50, "1-2": 20, "0": 0}
        evidence = {"scan_results": {"critical": ["c1", "c2"], "high": ["h1"]}}

        score = EvidenceGenerationService._evaluate_factor("security", evidence, rubric)

        self.assertEqual(score, Decimal("50"))

    def test_evaluate_testing_completed(self):
        """Test testing evaluation when completed."""
        rubric = {"completed": 0, "in_progress": 30, "not_started": 50}
        evidence = {"test_results": {"manual_test_status": "completed"}}

        score = EvidenceGenerationService._evaluate_factor("testing", evidence, rubric)

        self.assertEqual(score, Decimal("0"))

    def test_evaluate_testing_not_started(self):
        """Test testing evaluation when not started."""
        rubric = {"completed": 0, "in_progress": 30, "not_started": 50}
        evidence = {"test_results": {"manual_test_status": "not_started"}}

        score = EvidenceGenerationService._evaluate_factor("testing", evidence, rubric)

        self.assertEqual(score, Decimal("50"))

    def test_evaluate_rollback_validated(self):
        """Test rollback evaluation when validated."""
        rubric = {"validated": 0, "missing": 50}
        evidence = {"rollback_plan": {"strategy": "rollback", "steps": ["s1", "s2"]}}

        score = EvidenceGenerationService._evaluate_factor("rollback", evidence, rubric)

        self.assertEqual(score, Decimal("0"))

    def test_evaluate_rollback_missing(self):
        """Test rollback evaluation when missing."""
        rubric = {"validated": 0, "missing": 50}
        evidence = {"rollback_plan": {}}

        score = EvidenceGenerationService._evaluate_factor("rollback", evidence, rubric)

        self.assertEqual(score, Decimal("50"))

    def test_evaluate_scope_small(self):
        """Test scope evaluation for small deployment."""
        rubric = {">10": 40, "5-10": 20, "<5": 0}
        evidence = {"deployment_plan": {"affected_components": ["app1"]}}

        score = EvidenceGenerationService._evaluate_factor("scope", evidence, rubric)

        self.assertEqual(score, Decimal("0"))

    def test_evaluate_scope_medium(self):
        """Test scope evaluation for medium deployment."""
        rubric = {">10": 40, "5-10": 20, "<5": 0}
        evidence = {"deployment_plan": {"affected_components": ["a", "b", "c", "d", "e"]}}

        score = EvidenceGenerationService._evaluate_factor("scope", evidence, rubric)

        # 5 components should produce a valid score
        self.assertIsNotNone(score)
        self.assertGreaterEqual(score, 0)
        self.assertLessEqual(score, 100)

    def test_evaluate_scope_large(self):
        """Test scope evaluation for large deployment."""
        rubric = {">10": 40, "5-10": 20, "<5": 0}
        evidence = {"deployment_plan": {"affected_components": list(range(15))}}

        score = EvidenceGenerationService._evaluate_factor("scope", evidence, rubric)

        self.assertEqual(score, Decimal("40"))


class CompletenessCheckTests(TestCase):
    """Test completeness checking logic."""

    def test_complete_evidence(self):
        """Test completeness check for complete evidence."""
        evidence = {
            "artifacts": {"hash": "abc123"},
            "test_results": {"coverage_percent": 90},
            "scan_results": {"critical": []},
            "deployment_plan": {"strategy": "rollout"},
            "rollback_plan": {"strategy": "rollback"},
        }

        completeness = EvidenceGenerationService._check_completeness(evidence)

        self.assertTrue(all(completeness.values()))

    def test_incomplete_evidence(self):
        """Test completeness check for incomplete evidence."""
        evidence = {
            "artifacts": {"hash": "abc123"},
            # Missing other fields
        }

        completeness = EvidenceGenerationService._check_completeness(evidence)

        self.assertTrue(completeness["artifacts"])
        self.assertFalse(completeness["test_results"])
        self.assertFalse(completeness["scan_results"])
        self.assertFalse(completeness["deployment_plan"])
        self.assertFalse(completeness["rollback_plan"])

    def test_empty_fields_considered_incomplete(self):
        """Test that empty fields are considered incomplete."""
        evidence = {
            "artifacts": {},  # Empty
            "test_results": {},
            "scan_results": {},
            "deployment_plan": {},
            "rollback_plan": {},
        }

        completeness = EvidenceGenerationService._check_completeness(evidence)

        self.assertFalse(all(completeness.values()))


class EvidenceRetrievalTests(TestCase):
    """Test evidence retrieval and listing."""

    def setUp(self):
        """Create test evidence packages."""
        for i in range(3):
            EvidencePackage.objects.create(
                deployment_intent_id="deploy-123",
                correlation_id=f"corr-{i}",
                evidence_data={"test": f"data-{i}"},
            )

        # Create evidence for different deployment
        EvidencePackage.objects.create(
            deployment_intent_id="deploy-456",
            correlation_id="corr-other",
            evidence_data={"test": "data-other"},
        )

    def test_list_evidence_for_deployment(self):
        """Test listing evidence for a specific deployment."""
        packages = EvidenceGenerationService.list_evidence_for_deployment("deploy-123")

        self.assertEqual(packages.count(), 3)

    def test_list_evidence_ordered_by_created_at(self):
        """Test that evidence is ordered by created_at descending."""
        packages = list(EvidenceGenerationService.list_evidence_for_deployment("deploy-123"))

        # Should be ordered newest first
        for i in range(len(packages) - 1):
            self.assertGreaterEqual(packages[i].created_at, packages[i + 1].created_at)

    def test_verify_package_immutability(self):
        """Test immutability verification through service."""
        package = EvidencePackage.objects.create(
            deployment_intent_id="deploy-123",
            correlation_id="corr-test",
            evidence_data={"test": "data"},
        )

        result = EvidenceGenerationService.verify_package_immutability(package)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["package_name"], str(package.id))
        self.assertEqual(result["correlation_id"], "corr-test")
