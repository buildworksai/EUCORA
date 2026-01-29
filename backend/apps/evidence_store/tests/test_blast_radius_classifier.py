# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
P5.5: Comprehensive tests for Blast Radius Classifier.
Tests rule-based classification, CMDB integration, and manual overrides.
"""
import pytest
from django.test import TestCase

from apps.evidence_store.blast_radius_classifier import BlastRadiusClassifier
from apps.evidence_store.models_p5_5 import BlastRadiusClass


class BlastRadiusClassifierTestSetup(TestCase):
    """Setup fixtures for blast radius classifier tests."""

    @classmethod
    def setUpTestData(cls):
        """Create blast radius class definitions."""
        BlastRadiusClass.objects.get_or_create(
            name="CRITICAL_INFRASTRUCTURE",
            defaults={
                "description": "Security/infrastructure tools that affect enterprise security posture",
                "business_criticality": "CRITICAL",
                "cab_quorum_required": 3,
                "auto_approve_allowed": False,
                "user_impact_max": 100000,
                "example_applications": ["antivirus", "vpn", "security agents", "AD tools"],
            },
        )

        BlastRadiusClass.objects.get_or_create(
            name="BUSINESS_CRITICAL",
            defaults={
                "description": "Applications critical to business operations",
                "business_criticality": "HIGH",
                "cab_quorum_required": 2,
                "auto_approve_allowed": True,
                "user_impact_max": 50000,
                "example_applications": ["erp", "crm", "financial systems"],
            },
        )

        BlastRadiusClass.objects.get_or_create(
            name="PRODUCTIVITY_TOOLS",
            defaults={
                "description": "Standard productivity applications",
                "business_criticality": "MEDIUM",
                "cab_quorum_required": 1,
                "auto_approve_allowed": True,
                "user_impact_max": 10000,
                "example_applications": ["office", "slack", "zoom", "chrome"],
            },
        )

        BlastRadiusClass.objects.get_or_create(
            name="NON_CRITICAL",
            defaults={
                "description": "Utility and non-critical applications",
                "business_criticality": "LOW",
                "cab_quorum_required": 1,
                "auto_approve_allowed": True,
                "user_impact_max": 5000,
                "example_applications": ["calculator", "wallpaper", "screensavers"],
            },
        )

        cls.classifier = BlastRadiusClassifier()


class TestKeywordBasedClassification(BlastRadiusClassifierTestSetup):
    """Test keyword-based classification rules."""

    def test_critical_infrastructure_security_keywords(self):
        """Security-related apps should classify as CRITICAL_INFRASTRUCTURE."""
        apps = [
            "Windows Security Agent",
            "CrowdStrike Falcon Antivirus",
            "Cisco AnyConnect VPN Client",
            "Active Directory Management Tools",
            "PKI Certificate Manager",
        ]

        for app_name in apps:
            result = self.classifier.classify_deployment(app_name=app_name)
            self.assertEqual(result, "CRITICAL_INFRASTRUCTURE", f"{app_name} should be CRITICAL_INFRASTRUCTURE")

    def test_business_critical_erp_keywords(self):
        """ERP/CRM apps should classify as BUSINESS_CRITICAL."""
        apps = [
            "SAP ERP Client",
            "Oracle Financial Management",
            "Salesforce CRM Desktop",
            "Microsoft Dynamics 365",
            "Trading Platform Client",
        ]

        for app_name in apps:
            result = self.classifier.classify_deployment(app_name=app_name)
            self.assertEqual(result, "BUSINESS_CRITICAL", f"{app_name} should be BUSINESS_CRITICAL")

    def test_productivity_tools_office_keywords(self):
        """Standard productivity apps should classify as PRODUCTIVITY_TOOLS."""
        apps = [
            "Microsoft Office 365",
            "Slack Desktop",
            "Zoom Meetings",
            "Google Chrome Browser",
            "Adobe Acrobat Reader",
        ]

        for app_name in apps:
            result = self.classifier.classify_deployment(app_name=app_name)
            self.assertEqual(result, "PRODUCTIVITY_TOOLS", f"{app_name} should be PRODUCTIVITY_TOOLS")

    def test_non_critical_utility_keywords(self):
        """Utility apps should classify as NON_CRITICAL."""
        apps = [
            "Calculator Plus",
            "Wallpaper Engine",
            "Notepad++ Text Editor",
            "Paint.NET",
            "Screen Saver Collection",
        ]

        for app_name in apps:
            result = self.classifier.classify_deployment(app_name=app_name)
            self.assertEqual(result, "NON_CRITICAL", f"{app_name} should be NON_CRITICAL")


class TestPrivilegeLevelClassification(BlastRadiusClassifierTestSetup):
    """Test classification based on privilege requirements."""

    def test_admin_required_elevates_classification(self):
        """Apps requiring admin should classify higher."""
        # Without admin flag
        result_normal = self.classifier.classify_deployment(app_name="Generic Utility Tool", requires_admin=False)

        # With admin flag
        result_admin = self.classifier.classify_deployment(app_name="Generic Utility Tool", requires_admin=True)

        # Admin version should be at least as critical
        criticality_order = ["NON_CRITICAL", "PRODUCTIVITY_TOOLS", "BUSINESS_CRITICAL", "CRITICAL_INFRASTRUCTURE"]
        normal_idx = criticality_order.index(result_normal)
        admin_idx = criticality_order.index(result_admin)

        self.assertGreaterEqual(admin_idx, normal_idx)

    def test_system_level_always_critical_infrastructure(self):
        """System-level installs should always be CRITICAL_INFRASTRUCTURE."""
        result = self.classifier.classify_deployment(
            app_name="Generic Application", requires_admin=True, app_category="system"
        )

        self.assertEqual(result, "CRITICAL_INFRASTRUCTURE")


class TestUserCountImpactClassification(BlastRadiusClassifierTestSetup):
    """Test classification based on user impact."""

    def test_large_user_count_elevates_classification(self):
        """High user count should elevate classification."""
        # Small user count
        result_small = self.classifier.classify_deployment(app_name="Office Plugin", target_user_count=100)

        # Large user count
        result_large = self.classifier.classify_deployment(app_name="Office Plugin", target_user_count=50000)

        criticality_order = ["NON_CRITICAL", "PRODUCTIVITY_TOOLS", "BUSINESS_CRITICAL", "CRITICAL_INFRASTRUCTURE"]
        small_idx = criticality_order.index(result_small)
        large_idx = criticality_order.index(result_large)

        self.assertGreaterEqual(large_idx, small_idx)

    def test_enterprise_wide_deployment_high_criticality(self):
        """Enterprise-wide deployments should be high criticality."""
        result = self.classifier.classify_deployment(app_name="Standard Productivity Tool", target_user_count=100000)

        self.assertIn(result, ["BUSINESS_CRITICAL", "CRITICAL_INFRASTRUCTURE"])


class TestBusinessCriticalityClassification(BlastRadiusClassifierTestSetup):
    """Test classification based on business criticality."""

    def test_high_business_criticality_elevates(self):
        """HIGH business criticality should elevate classification."""
        result = self.classifier.classify_deployment(app_name="Custom Application", business_criticality="HIGH")

        self.assertIn(result, ["BUSINESS_CRITICAL", "CRITICAL_INFRASTRUCTURE"])

    def test_low_business_criticality_reduces(self):
        """LOW business criticality should reduce classification."""
        result = self.classifier.classify_deployment(app_name="Custom Application", business_criticality="LOW")

        self.assertIn(result, ["NON_CRITICAL", "PRODUCTIVITY_TOOLS"])


class TestCMDBIntegrationPlaceholder(BlastRadiusClassifierTestSetup):
    """Test CMDB integration placeholder logic."""

    def test_cmdb_classification_priority(self):
        """CMDB classification should take priority over rules."""
        cmdb_data = {"service_tier": "TIER_1", "business_criticality": "CRITICAL", "impact_scope": "GLOBAL"}

        result = self.classifier.classify_deployment(
            app_name="Generic Tool", cmdb_data=cmdb_data  # Would normally be NON_CRITICAL
        )

        # CMDB data should override keyword-based classification
        self.assertEqual(result, "CRITICAL_INFRASTRUCTURE")

    def test_cmdb_missing_falls_back_to_rules(self):
        """Missing CMDB data should fall back to rule-based classification."""
        result = self.classifier.classify_deployment(app_name="Security Agent", cmdb_data=None)  # No CMDB data

        # Should use keyword-based classification
        self.assertEqual(result, "CRITICAL_INFRASTRUCTURE")


class TestManualOverrideClassification(BlastRadiusClassifierTestSetup):
    """Test manual override functionality."""

    def test_manual_override_with_justification(self):
        """Manual override should be allowed with justification."""
        override_result = self.classifier.apply_manual_override(
            app_name="Generic Tool",
            computed_class="NON_CRITICAL",
            override_class="BUSINESS_CRITICAL",
            justification="Required by finance department for quarter-end processing",
            overridden_by="cab_member",
        )

        self.assertEqual(override_result["blast_radius_class"], "BUSINESS_CRITICAL")
        self.assertEqual(override_result["override_applied"], True)
        self.assertIn("justification", override_result)

    def test_manual_override_without_justification_fails(self):
        """Manual override without justification should fail."""
        with self.assertRaises(ValueError) as context:
            self.classifier.apply_manual_override(
                app_name="Generic Tool",
                computed_class="NON_CRITICAL",
                override_class="BUSINESS_CRITICAL",
                justification="",  # Empty justification
                overridden_by="cab_member",
            )

        self.assertIn("justification", str(context.exception).lower())


class TestClassificationDetails(BlastRadiusClassifierTestSetup):
    """Test classification details retrieval."""

    def test_get_classification_details(self):
        """Should return complete classification details."""
        details = self.classifier.get_classification_details("CRITICAL_INFRASTRUCTURE")

        self.assertEqual(details["blast_radius_class"], "CRITICAL_INFRASTRUCTURE")
        self.assertEqual(
            details["description"], "Security/infrastructure tools that affect enterprise security posture"
        )
        self.assertEqual(details["cab_quorum_required"], 3)
        self.assertEqual(details["auto_approve_allowed"], False)
        self.assertIn("example_applications", details)

    def test_get_classification_details_invalid_class(self):
        """Invalid classification should raise error."""
        with self.assertRaises(ValueError) as context:
            self.classifier.get_classification_details("INVALID_CLASS")

        self.assertIn("invalid", str(context.exception).lower())


class TestEdgeCases(BlastRadiusClassifierTestSetup):
    """Test edge cases and boundary conditions."""

    def test_empty_app_name(self):
        """Empty app name should default to most conservative classification."""
        result = self.classifier.classify_deployment(app_name="")

        # Should default to safest classification
        self.assertEqual(result, "CRITICAL_INFRASTRUCTURE")

    def test_unknown_app_name(self):
        """Unknown app with no keywords should classify conservatively."""
        result = self.classifier.classify_deployment(app_name="XYZABC123 Unknown Application")

        # Should default to conservative classification
        self.assertIn(result, ["PRODUCTIVITY_TOOLS", "BUSINESS_CRITICAL", "CRITICAL_INFRASTRUCTURE"])

    def test_mixed_signals_classification(self):
        """App with mixed signals should classify to highest criticality."""
        result = self.classifier.classify_deployment(
            app_name="Office Security Plugin",  # Has both 'office' and 'security'
            requires_admin=True,
            target_user_count=50000,
        )

        # Should classify as most critical due to 'security' keyword
        self.assertEqual(result, "CRITICAL_INFRASTRUCTURE")
