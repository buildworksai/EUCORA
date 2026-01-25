# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for prompt framework (8 tests).
"""
from django.test import TestCase

from apps.ai_strategy.prompts import PromptRegistry, PromptTemplate, registry


class PromptRegistryTests(TestCase):
    """Tests for prompt registry."""

    def test_registry_has_templates(self):
        """Test registry contains expected templates."""
        templates = registry.list_templates()

        self.assertIn("incident_classification:v1", templates)
        self.assertIn("remediation_suggestion:v1", templates)
        self.assertIn("deployment_risk_assessment:v1", templates)

    def test_get_template(self):
        """Test getting template by name and version."""
        template = registry.get("incident_classification", "v1")

        self.assertIsInstance(template, PromptTemplate)
        self.assertEqual(template.name, "incident_classification")
        self.assertEqual(template.version, "v1")

    def test_template_format(self):
        """Test template formatting with variables."""
        template = registry.get("incident_classification", "v1")

        messages = template.format(
            title="Test Incident",
            description="System is down",
            affected_systems="web-server-01",
            error_messages="Connection refused",
        )

        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0].role, "system")
        self.assertEqual(messages[1].role, "user")
        self.assertIn("Test Incident", messages[1].content)

    def test_remediation_template(self):
        """Test remediation template formatting."""
        template = registry.get("remediation_suggestion", "v1")

        messages = template.format(
            issue_description="Service not starting",
            platform="linux",
            current_state="Service stopped",
            desired_state="Service running",
            constraints="No downtime allowed",
        )

        self.assertIn("Service not starting", messages[1].content)
        self.assertIn("linux", messages[1].content)

    def test_risk_assessment_template(self):
        """Test risk assessment template formatting."""
        template = registry.get("deployment_risk_assessment", "v1")

        messages = template.format(
            package_name="test-app",
            package_version="1.0.0",
            platform="windows",
            target_scope="global",
            privilege_level="admin",
            scan_summary="2 high, 5 medium",
            dependencies="",
            history="",
        )

        self.assertIn("test-app", messages[1].content)
        self.assertIn("1.0.0", messages[1].content)

    def test_template_has_metadata(self):
        """Test template includes metadata."""
        template = registry.get("incident_classification", "v1")

        self.assertIsNotNone(template.metadata)
        self.assertIn("use_case", template.metadata)

    def test_nonexistent_template_raises_error(self):
        """Test getting nonexistent template raises KeyError."""
        with self.assertRaises(KeyError):
            registry.get("nonexistent_template", "v1")

    def test_register_new_template(self):
        """Test registering new template."""
        test_registry = PromptRegistry()

        template = PromptTemplate(
            name="test_prompt",
            version="v1",
            system_message="Test system message",
            user_template="Test user: {input}",
            description="Test template",
            metadata={},
        )

        test_registry.register(template)

        retrieved = test_registry.get("test_prompt", "v1")
        self.assertEqual(retrieved.name, "test_prompt")
