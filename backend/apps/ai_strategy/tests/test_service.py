# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Service integration tests for AI Strategy (9 tests).
"""
from django.test import TestCase

from apps.ai_strategy.providers import MockLLMProvider
from apps.ai_strategy.service import AIStrategyService


class AIStrategyServiceTests(TestCase):
    """Tests for AIStrategyService integration."""

    def setUp(self):
        """Set up test fixtures."""
        self.service = AIStrategyService(provider=MockLLMProvider())

    def test_classify_incident_basic(self):
        """Test basic incident classification."""
        result = self.service.classify_incident(
            title="Database Connection Failure",
            description="Unable to connect to production database",
            affected_systems="db-prod-01",
            error_messages="Connection timeout after 30s",
        )

        self.assertIn("classification", result)
        self.assertIn("confidence", result)
        self.assertIn("model", result)
        self.assertIn("provider", result)
        self.assertEqual(result["provider"], "mock")
        self.assertTrue(result["validation_passed"])

    def test_classify_incident_with_pii_detection(self):
        """Test incident classification with PII sanitization."""
        result = self.service.classify_incident(
            title="User Data Exposure",
            description="User email test@example.com was logged in error logs at 8.8.8.8",
            affected_systems="web-server-01",
            error_messages="",
            correlation_id="test-corr-001",
        )

        # PII should be detected and sanitized
        self.assertIsNotNone(result["pii_detected"])
        self.assertIn("email", result["pii_detected"])
        self.assertIn("ipv4", result["pii_detected"])
        self.assertTrue(result["evidence"]["input_sanitized"])

    def test_classify_incident_with_correlation_id(self):
        """Test correlation ID is tracked in evidence."""
        correlation_id = "test-corr-123"
        result = self.service.classify_incident(
            title="Test Incident", description="Test description", correlation_id=correlation_id
        )

        self.assertEqual(result["evidence"]["correlation_id"], correlation_id)

    def test_suggest_remediation_basic(self):
        """Test basic remediation suggestion."""
        result = self.service.suggest_remediation(
            issue_description="Service not starting after update",
            platform="linux",
            current_state="Service stopped",
            desired_state="Service running",
            constraints="No downtime allowed",
        )

        self.assertIn("remediation", result)
        self.assertIn("confidence", result)
        self.assertEqual(result["provider"], "mock")
        self.assertTrue(result["validation_passed"])

    def test_suggest_remediation_with_pii(self):
        """Test remediation suggestion with PII sanitization."""
        result = self.service.suggest_remediation(
            issue_description="API key sk-1234567890abcdef exposed in logs",
            platform="windows",
            current_state="Credentials compromised",
            desired_state="Credentials rotated",
            correlation_id="test-corr-002",
        )

        # PII (API key) should be detected
        self.assertIsNotNone(result["pii_detected"])
        self.assertTrue(result["evidence"]["input_sanitized"])

    def test_assess_deployment_risk_basic(self):
        """Test deployment risk assessment."""
        result = self.service.assess_deployment_risk(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            target_scope="global",
            privilege_level="admin",
            scan_summary={"critical": 0, "high": 1, "medium": 3},
            correlation_id="test-corr-003",
        )

        self.assertIn("risk_assessment", result)
        self.assertIn("confidence", result)
        self.assertTrue(result["validation_passed"])
        self.assertEqual(result["evidence"]["correlation_id"], "test-corr-003")

    def test_assess_deployment_risk_no_vulnerabilities(self):
        """Test risk assessment with clean scan."""
        result = self.service.assess_deployment_risk(
            package_name="safe-app",
            package_version="2.0.0",
            platform="macos",
            target_scope="department",
            privilege_level="user",
            scan_summary={"critical": 0, "high": 0, "medium": 0},
        )

        self.assertIn("risk_assessment", result)
        self.assertEqual(result["provider"], "mock")

    def test_health_check(self):
        """Test AI service health check."""
        health = self.service.health_check()

        self.assertIn("provider", health)
        self.assertIn("model", health)
        self.assertIn("healthy", health)
        self.assertIn("guardrails", health)

        self.assertEqual(health["provider"], "mock")
        self.assertTrue(health["healthy"])
        self.assertTrue(health["guardrails"]["pii_sanitizer"])
        self.assertTrue(health["guardrails"]["output_validator"])

    def test_service_uses_configured_provider(self):
        """Test service uses provider passed to constructor."""
        mock_provider = MockLLMProvider()
        service = AIStrategyService(provider=mock_provider)

        result = service.classify_incident(title="Test", description="Test incident")

        self.assertEqual(result["provider"], "mock")
        self.assertEqual(result["model"], "mock-gpt")
