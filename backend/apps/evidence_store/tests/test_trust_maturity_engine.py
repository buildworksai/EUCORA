# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
P5.5: Comprehensive tests for Trust Maturity Engine.
Tests maturity progression evaluation, criteria validation, and level transitions.
"""
from datetime import timedelta
from decimal import Decimal
from uuid import uuid4

import pytest
from django.contrib.auth.models import User
from django.test import TestCase
from django.utils import timezone

from apps.deployment_intents.models import DeploymentIntent
from apps.evidence_store.models_p5_5 import (
    DeploymentIncident,
    RiskModelVersion,
    TrustMaturityLevel,
    TrustMaturityProgress,
)
from apps.evidence_store.trust_maturity_engine import TrustMaturityEngine


class TrustMaturityEngineTestSetup(TestCase):
    """Setup fixtures for trust maturity engine tests."""

    @classmethod
    def setUpTestData(cls):
        """Create trust maturity levels and risk model."""
        cls.user, created = User.objects.get_or_create(username="testuser", defaults={"email": "test@example.com"})
        if created:
            cls.user.set_password("testpass123")
            cls.user.save()

        # Create trust maturity levels
        TrustMaturityLevel.objects.get_or_create(
            level="LEVEL_0_BASELINE",
            defaults={
                "description": "Baseline level - 100% CAB review",
                "weeks_required": 4,
                "max_incident_rate": Decimal("999.0"),  # No limit for baseline
                "max_p1_incidents": 999,
                "max_p2_incidents": 999,
                "risk_model_version": "1.1",
                "auto_approve_thresholds": {
                    "CRITICAL_INFRASTRUCTURE": 0,
                    "BUSINESS_CRITICAL": 0,
                    "PRODUCTIVITY_TOOLS": 0,
                    "NON_CRITICAL": 0,
                },
            },
        )

        TrustMaturityLevel.objects.get_or_create(
            level="LEVEL_1_CAUTIOUS",
            defaults={
                "description": "Cautious level - limited auto-approve",
                "weeks_required": 4,
                "max_incident_rate": Decimal("2.0"),
                "max_p1_incidents": 0,
                "max_p2_incidents": 2,
                "risk_model_version": "1.2",
                "auto_approve_thresholds": {
                    "CRITICAL_INFRASTRUCTURE": 0,
                    "BUSINESS_CRITICAL": 5,
                    "PRODUCTIVITY_TOOLS": 20,
                    "NON_CRITICAL": 30,
                },
            },
        )

        TrustMaturityLevel.objects.get_or_create(
            level="LEVEL_2_MODERATE",
            defaults={
                "description": "Moderate level - balanced automation",
                "weeks_required": 4,
                "max_incident_rate": Decimal("1.0"),
                "max_p1_incidents": 0,
                "max_p2_incidents": 1,
                "risk_model_version": "1.3",
                "auto_approve_thresholds": {
                    "CRITICAL_INFRASTRUCTURE": 0,
                    "BUSINESS_CRITICAL": 10,
                    "PRODUCTIVITY_TOOLS": 30,
                    "NON_CRITICAL": 50,
                },
            },
        )

        TrustMaturityLevel.objects.get_or_create(
            level="LEVEL_3_MATURE",
            defaults={
                "description": "Mature level - high automation",
                "weeks_required": 4,
                "max_incident_rate": Decimal("0.5"),
                "max_p1_incidents": 0,
                "max_p2_incidents": 0,
                "risk_model_version": "1.4",
                "auto_approve_thresholds": {
                    "CRITICAL_INFRASTRUCTURE": 0,
                    "BUSINESS_CRITICAL": 20,
                    "PRODUCTIVITY_TOOLS": 50,
                    "NON_CRITICAL": 70,
                },
            },
        )

        # Create risk model version (ensure only one active)
        RiskModelVersion.objects.filter(is_active=True).update(is_active=False)

        cls.risk_model = RiskModelVersion.objects.create(
            version="1.4",
            mode="MATURE",
            effective_date=timezone.now(),
            review_date=timezone.now() + timezone.timedelta(days=90),
            is_active=True,
            approved_by_cab=True,
            risk_factor_weights={
                "privilege": 0.2,
                "supply_chain": 0.15,
                "exploitability": 0.1,
                "data_access": 0.1,
                "sbom_vulnerabilities": 0.15,
                "blast_radius": 0.1,
                "operational_complexity": 0.1,
                "history": 0.1,
            },
            auto_approve_thresholds={
                "CRITICAL_INFRASTRUCTURE": 0,
                "BUSINESS_CRITICAL": 20,
                "PRODUCTIVITY_TOOLS": 50,
                "NON_CRITICAL": 70,
            },
            calibration_data={"incident_correlation": 0.85, "false_positive_rate": 0.05, "false_negative_rate": 0.03},
        )

        cls.engine = TrustMaturityEngine()

        # Create evidence package for deployment intents
        from apps.evidence_store.models import EvidencePackage

        cls.evidence = EvidencePackage.objects.create(
            evidence_data={"test": "data"},
            risk_score=Decimal("25.0"),
            risk_factors={"test": 0},
            correlation_id="TEST-EVD-001",
        )

    def create_deployment_intent(self):
        """Helper to create deployment intent."""
        return DeploymentIntent.objects.create(
            app_name="TestApp",
            version="1.0.0",
            target_ring="CANARY",
            submitter=self.user,
            evidence_pack_id=str(self.evidence.id),
        )


class TestMaturityProgressionBaseline(TrustMaturityEngineTestSetup):
    """Test progression from baseline level."""

    def test_baseline_insufficient_weeks_blocks_progression(self):
        """Less than 4 weeks should block progression."""
        # Create incidents over 3 weeks (insufficient)
        incident_date = timezone.now() - timedelta(weeks=2)

        result = self.engine.evaluate_maturity_progression(current_level="LEVEL_0_BASELINE", evaluation_period_weeks=3)

        self.assertFalse(result["ready_to_progress"])
        self.assertIn("weeks", " ".join(result["blocking_criteria"]).lower())

    def test_baseline_clean_record_allows_progression(self):
        """4+ weeks with clean record should allow progression to Level 1."""
        # No incidents in 4 weeks
        result = self.engine.evaluate_maturity_progression(current_level="LEVEL_0_BASELINE", evaluation_period_weeks=4)

        self.assertTrue(result["ready_to_progress"])
        self.assertEqual(result["next_level"], "LEVEL_1_CAUTIOUS")
        self.assertEqual(len(result["blocking_criteria"]), 0)

    def test_baseline_with_p1_incident_blocks_progression(self):
        """P1 incident should block progression to Level 1."""
        deployment = self.create_deployment_intent()

        # Create P1 incident
        DeploymentIncident.objects.create(
            deployment_intent_id=str(deployment.id),
            evidence_package_id=str(uuid4()),
            severity="P1",
            incident_date=timezone.now() - timedelta(weeks=2),
            detection_method="monitoring",
            title="Critical production failure",
            description="Service outage",
            was_auto_approved=False,
            risk_score_at_approval=Decimal("60"),
            blast_radius_class="BUSINESS_CRITICAL",
            created_by="system",
        )

        result = self.engine.evaluate_maturity_progression(current_level="LEVEL_0_BASELINE", evaluation_period_weeks=4)

        self.assertFalse(result["ready_to_progress"])
        self.assertIn("P1", " ".join(result["blocking_criteria"]))

    def test_baseline_with_high_incident_rate_blocks_progression(self):
        """High incident rate (>2%) should block progression."""
        deployment = self.create_deployment_intent()

        # Create 3 P3 incidents out of 100 deployments = 3% rate
        for i in range(3):
            DeploymentIncident.objects.create(
                deployment_intent_id=str(deployment.id),
                evidence_package_id=str(uuid4()),
                severity="P3",
                incident_date=timezone.now() - timedelta(weeks=2),
                detection_method="monitoring",
                title=f"Minor issue {i}",
                description="Minor impact",
                was_auto_approved=False,
                risk_score_at_approval=Decimal("40"),
                blast_radius_class="PRODUCTIVITY_TOOLS",
                created_by="system",
            )

        # Mock 100 total deployments
        result = self.engine.evaluate_maturity_progression(
            current_level="LEVEL_0_BASELINE", evaluation_period_weeks=4, total_deployments=100
        )

        self.assertFalse(result["ready_to_progress"])
        self.assertIn("incident rate", " ".join(result["blocking_criteria"]).lower())


class TestMaturityProgressionLevel1to2(TrustMaturityEngineTestSetup):
    """Test progression from Level 1 to Level 2."""

    def test_level1_requires_stricter_criteria(self):
        """Level 1 → 2 requires ≤1% incident rate, ≤1 P2."""
        # Create 2 P2 incidents (exceeds max)
        deployment = self.create_deployment_intent()

        for i in range(2):
            DeploymentIncident.objects.create(
                deployment_intent_id=str(deployment.id),
                evidence_package_id=str(uuid4()),
                severity="P2",
                incident_date=timezone.now() - timedelta(weeks=2),
                detection_method="monitoring",
                title=f"Moderate issue {i}",
                description="Moderate impact",
                was_auto_approved=False,
                risk_score_at_approval=Decimal("50"),
                blast_radius_class="BUSINESS_CRITICAL",
                created_by="system",
            )

        result = self.engine.evaluate_maturity_progression(
            current_level="LEVEL_1_CAUTIOUS", evaluation_period_weeks=4, total_deployments=100
        )

        self.assertFalse(result["ready_to_progress"])
        self.assertIn("P2", " ".join(result["blocking_criteria"]))

    def test_level1_clean_record_allows_progression(self):
        """Clean record allows progression to Level 2."""
        result = self.engine.evaluate_maturity_progression(
            current_level="LEVEL_1_CAUTIOUS", evaluation_period_weeks=4, total_deployments=100
        )

        self.assertTrue(result["ready_to_progress"])
        self.assertEqual(result["next_level"], "LEVEL_2_MODERATE")


class TestMaturityProgressionLevel2to3(TrustMaturityEngineTestSetup):
    """Test progression from Level 2 to Level 3."""

    def test_level2_requires_zero_p2_incidents(self):
        """Level 2 → 3 requires ZERO P2 incidents."""
        deployment = self.create_deployment_intent()

        # Create single P2 incident
        DeploymentIncident.objects.create(
            deployment_intent_id=str(deployment.id),
            evidence_package_id=str(uuid4()),
            severity="P2",
            incident_date=timezone.now() - timedelta(weeks=1),
            detection_method="monitoring",
            title="Moderate issue",
            description="Should block progression",
            was_auto_approved=False,
            risk_score_at_approval=Decimal("50"),
            blast_radius_class="BUSINESS_CRITICAL",
            created_by="system",
        )

        result = self.engine.evaluate_maturity_progression(
            current_level="LEVEL_2_MODERATE", evaluation_period_weeks=4, total_deployments=200
        )

        self.assertFalse(result["ready_to_progress"])
        self.assertIn("P2", " ".join(result["blocking_criteria"]))

    def test_level2_very_low_incident_rate_required(self):
        """Level 2 → 3 requires ≤0.5% incident rate."""
        deployment = self.create_deployment_intent()

        # Create 2 P3 incidents out of 200 deployments = 1% rate (exceeds 0.5%)
        for i in range(2):
            DeploymentIncident.objects.create(
                deployment_intent_id=str(deployment.id),
                evidence_package_id=str(uuid4()),
                severity="P3",
                incident_date=timezone.now() - timedelta(weeks=1),
                detection_method="monitoring",
                title=f"Minor issue {i}",
                description="Minor",
                was_auto_approved=True,
                risk_score_at_approval=Decimal("25"),
                blast_radius_class="NON_CRITICAL",
                created_by="system",
            )

        result = self.engine.evaluate_maturity_progression(
            current_level="LEVEL_2_MODERATE", evaluation_period_weeks=4, total_deployments=200
        )

        self.assertFalse(result["ready_to_progress"])


class TestMaturityProgressionLevel3to4(TrustMaturityEngineTestSetup):
    """Test progression from Level 3 to Level 4."""

    def test_level3_requires_exceptional_performance(self):
        """Level 3 → 4 requires ≤0.1% incident rate."""
        deployment = self.create_deployment_intent()

        # Create 1 P3 incident out of 500 deployments = 0.2% rate (exceeds 0.1%)
        DeploymentIncident.objects.create(
            deployment_intent_id=str(deployment.id),
            evidence_package_id=str(uuid4()),
            severity="P3",
            incident_date=timezone.now() - timedelta(weeks=1),
            detection_method="monitoring",
            title="Minor issue",
            description="Rare incident",
            was_auto_approved=True,
            risk_score_at_approval=Decimal("20"),
            blast_radius_class="NON_CRITICAL",
            created_by="system",
        )

        result = self.engine.evaluate_maturity_progression(
            current_level="LEVEL_3_MATURE", evaluation_period_weeks=4, total_deployments=500
        )

        self.assertFalse(result["ready_to_progress"])

    def test_level3_exceptional_record_allows_max_level(self):
        """Exceptional record (≤0.1% incidents) allows Level 4."""
        # 1 P4 incident out of 2000 deployments = 0.05% rate
        deployment = self.create_deployment_intent()

        DeploymentIncident.objects.create(
            deployment_intent_id=str(deployment.id),
            evidence_package_id=str(uuid4()),
            severity="P4",
            incident_date=timezone.now() - timedelta(weeks=1),
            detection_method="monitoring",
            title="Cosmetic issue",
            description="No impact",
            was_auto_approved=True,
            risk_score_at_approval=Decimal("15"),
            blast_radius_class="NON_CRITICAL",
            created_by="system",
        )

        result = self.engine.evaluate_maturity_progression(
            current_level="LEVEL_3_MATURE", evaluation_period_weeks=4, total_deployments=2000
        )

        self.assertTrue(result["ready_to_progress"])
        self.assertEqual(result["next_level"], "LEVEL_4_OPTIMIZED")


class TestMaturityEvaluationDetails(TrustMaturityEngineTestSetup):
    """Test evaluation result details and metadata."""

    def test_evaluation_includes_incident_analysis(self):
        """Evaluation should include detailed incident analysis."""
        deployment = self.create_deployment_intent()

        DeploymentIncident.objects.create(
            deployment_intent_id=str(deployment.id),
            evidence_package_id=str(uuid4()),
            severity="P3",
            incident_date=timezone.now() - timedelta(weeks=1),
            detection_method="monitoring",
            title="Test incident",
            description="For analysis",
            was_auto_approved=False,
            risk_score_at_approval=Decimal("45"),
            blast_radius_class="PRODUCTIVITY_TOOLS",
            created_by="system",
        )

        result = self.engine.evaluate_maturity_progression(
            current_level="LEVEL_0_BASELINE", evaluation_period_weeks=4, total_deployments=100
        )

        self.assertIn("incident_analysis", result)
        self.assertIn("total_incidents", result["incident_analysis"])
        self.assertIn("incident_rate", result["incident_analysis"])
        self.assertIn("p1_incidents", result["incident_analysis"])
        self.assertIn("p2_incidents", result["incident_analysis"])

    def test_evaluation_includes_criteria_evaluation(self):
        """Evaluation should include pass/fail for each criterion."""
        result = self.engine.evaluate_maturity_progression(current_level="LEVEL_0_BASELINE", evaluation_period_weeks=4)

        self.assertIn("criteria_evaluation", result)
        self.assertIsInstance(result["criteria_evaluation"], list)

        # Check that each criterion has pass/fail status
        for criterion in result["criteria_evaluation"]:
            self.assertIn("criterion", criterion)
            self.assertIn("passed", criterion)
            self.assertIn("details", criterion)

    def test_evaluation_generates_recommendation(self):
        """Evaluation should generate actionable recommendation."""
        result = self.engine.evaluate_maturity_progression(current_level="LEVEL_0_BASELINE", evaluation_period_weeks=4)

        self.assertIn("recommendation", result)
        self.assertGreater(len(result["recommendation"]), 20)

        if result["ready_to_progress"]:
            self.assertIn("LEVEL_1", result["recommendation"])
        else:
            self.assertIn("continue", result["recommendation"].lower())


class TestMaturityStatusRetrieval(TrustMaturityEngineTestSetup):
    """Test current maturity status retrieval."""

    def test_get_current_maturity_status(self):
        """Should return current maturity level and risk model."""
        status = self.engine.get_current_maturity_status()

        self.assertIn("current_level", status)
        self.assertIn("risk_model_version", status)
        self.assertIn("risk_model_mode", status)
        self.assertIn("auto_approve_thresholds", status)

        self.assertEqual(status["risk_model_version"], "1.1")
        self.assertEqual(status["risk_model_mode"], "GREENFIELD_CONSERVATIVE")

    def test_maturity_status_includes_latest_evaluation(self):
        """Status should include latest evaluation if available."""
        # Create evaluation record
        TrustMaturityProgress.objects.create(
            evaluation_date=timezone.now() - timedelta(days=1),
            current_level="LEVEL_0_BASELINE",
            next_level="LEVEL_1_CAUTIOUS",
            status="CRITERIA_MET",
            evaluation_period_weeks=4,
            incident_rate=Decimal("0.5"),
            p1_incidents=0,
            p2_incidents=0,
            p3_incidents=1,
            p4_incidents=0,
            total_deployments=200,
            blocking_criteria=[],
            cab_approved=False,
        )

        status = self.engine.get_current_maturity_status()

        self.assertIn("latest_evaluation", status)
        self.assertIsNotNone(status["latest_evaluation"])


class TestMaturityProgressionEdgeCases(TrustMaturityEngineTestSetup):
    """Test edge cases and boundary conditions."""

    def test_max_level_no_further_progression(self):
        """Level 4 should not progress further."""
        result = self.engine.evaluate_maturity_progression(current_level="LEVEL_4_OPTIMIZED", evaluation_period_weeks=4)

        self.assertFalse(result["ready_to_progress"])
        self.assertIsNone(result.get("next_level"))
        self.assertIn("maximum", result["recommendation"].lower())

    def test_zero_deployments_blocks_progression(self):
        """Zero deployments should block progression."""
        result = self.engine.evaluate_maturity_progression(
            current_level="LEVEL_0_BASELINE", evaluation_period_weeks=4, total_deployments=0
        )

        self.assertFalse(result["ready_to_progress"])
        self.assertIn("deployment", " ".join(result["blocking_criteria"]).lower())

    def test_negative_evaluation_period_raises_error(self):
        """Negative evaluation period should raise error."""
        with self.assertRaises(ValueError):
            self.engine.evaluate_maturity_progression(current_level="LEVEL_0_BASELINE", evaluation_period_weeks=-1)

    def test_invalid_level_raises_error(self):
        """Invalid maturity level should raise error."""
        with self.assertRaises(ValueError):
            self.engine.evaluate_maturity_progression(current_level="INVALID_LEVEL", evaluation_period_weeks=4)
