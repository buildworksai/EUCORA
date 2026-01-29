# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for AI guardrails (15 tests).
"""
from django.test import TestCase

from apps.ai_strategy.guardrails import OutputValidator, PIISanitizer


class PIISanitizerTests(TestCase):
    """Tests for PII sanitization."""

    def setUp(self):
        """Set up sanitizer."""
        self.sanitizer = PIISanitizer()

    def test_email_redaction(self):
        """Test email addresses are redacted."""
        text = "Contact john.doe@example.com for help"
        sanitized, detected = self.sanitizer.sanitize(text)

        self.assertIn("[EMAIL_REDACTED]", sanitized)
        self.assertNotIn("john.doe@example.com", sanitized)
        self.assertIn("email", detected)

    def test_public_ip_redaction(self):
        """Test public IP addresses are redacted."""
        text = "Server at 203.0.113.42 is down"
        sanitized, detected = self.sanitizer.sanitize(text)

        self.assertIn("[IP_REDACTED]", sanitized)
        self.assertNotIn("203.0.113.42", sanitized)
        self.assertIn("ipv4", detected)

    def test_private_ip_not_redacted(self):
        """Test private IP addresses are NOT redacted."""
        text = "Internal server at 192.168.1.100"
        sanitized, detected = self.sanitizer.sanitize(text)

        self.assertIn("192.168.1.100", sanitized)
        self.assertNotIn("[IP_REDACTED]", sanitized)

    def test_credit_card_redaction(self):
        """Test credit card numbers are redacted."""
        text = "Card number: 4532-1234-5678-9010"
        sanitized, detected = self.sanitizer.sanitize(text)

        self.assertIn("[CC_REDACTED]", sanitized)
        self.assertNotIn("4532", sanitized)
        self.assertIn("credit_card", detected)

    def test_ssn_redaction(self):
        """Test SSN is redacted."""
        text = "SSN: 123-45-6789"
        sanitized, detected = self.sanitizer.sanitize(text)

        self.assertIn("[SSN_REDACTED]", sanitized)
        self.assertNotIn("123-45-6789", sanitized)
        self.assertIn("ssn", detected)

    def test_phone_redaction(self):
        """Test phone numbers are redacted."""
        text = "Call 555-123-4567 for support"
        sanitized, detected = self.sanitizer.sanitize(text)

        self.assertIn("[PHONE_REDACTED]", sanitized)
        self.assertIn("phone", detected)

    def test_password_in_log_redaction(self):
        """Test passwords in logs are redacted."""
        text = "Error: password=secret123 failed"
        sanitized, detected = self.sanitizer.sanitize(text)

        self.assertIn("[REDACTED]", sanitized)
        self.assertNotIn("secret123", sanitized)
        self.assertIn("password", detected)

    def test_token_redaction(self):
        """Test tokens are redacted."""
        text = "Authorization: Bearer abc123def456"
        sanitized, detected = self.sanitizer.sanitize(text)

        self.assertIn("[REDACTED]", sanitized)
        self.assertIn("token", detected)

    def test_empty_text(self):
        """Test empty text handling."""
        sanitized, detected = self.sanitizer.sanitize("")

        self.assertEqual(sanitized, "")
        self.assertEqual(detected, [])

    def test_dict_sanitization(self):
        """Test dictionary sanitization."""
        data = {"email": "test@example.com", "description": "Contact john@example.com"}

        sanitized, detected = self.sanitizer.sanitize_dict(data)

        self.assertIn("[EMAIL_REDACTED]", sanitized["email"])
        self.assertIn("email", detected)


class OutputValidatorTests(TestCase):
    """Tests for output validation."""

    def setUp(self):
        """Set up validator."""
        self.validator = OutputValidator()

    def test_safe_output_passes(self):
        """Test safe output passes validation."""
        output = "This is a safe recommendation: Update the package version."
        result = self.validator.validate(output)

        self.assertTrue(result.is_valid)
        self.assertEqual(len(result.issues), 0)

    def test_dangerous_rm_rf_detected(self):
        """Test dangerous rm -rf is detected."""
        output = "Run: rm -rf / to fix the issue"
        result = self.validator.validate(output)

        self.assertFalse(result.is_valid)
        self.assertGreater(len(result.issues), 0)
        self.assertIn("[DANGEROUS_CONTENT_REMOVED]", result.sanitized_output)

    def test_sql_injection_detected(self):
        """Test SQL injection patterns are detected."""
        output = "Execute: DELETE FROM users WHERE 1=1"
        result = self.validator.validate(output)

        self.assertFalse(result.is_valid)

    def test_length_limit_enforced(self):
        """Test length limits are enforced."""
        output = "A" * 6000
        result = self.validator.validate(output, max_length=5000)

        self.assertFalse(result.is_valid)
        self.assertIn("exceeds maximum length", result.issues[0])

    def test_structure_validation_incident(self):
        """Test structure validation for incident classification."""
        output = """Severity: HIGH
Confidence: 0.85
Analysis: This is a serious issue"""

        result = self.validator.validate(output, use_case="incident_classification")

        self.assertTrue(result.is_valid)
