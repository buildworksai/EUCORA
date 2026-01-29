# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
PII sanitization guardrails.
"""
import re
from typing import Any, Dict, List, Tuple


class PIISanitizer:
    """
    Sanitize PII from text before sending to LLMs.

    Detects and redacts:
    - Email addresses
    - IP addresses (public only)
    - Credit card numbers
    - Social security numbers
    - Phone numbers
    - API keys/tokens
    - Passwords in logs
    """

    # Regex patterns for PII detection
    PATTERNS = {
        "email": r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",
        "ipv4": r"\b(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\b",
        "credit_card": r"\b(?:\d{4}[-\s]?){3}\d{4}\b",
        "ssn": r"\b\d{3}-\d{2}-\d{4}\b",
        "phone": r"\b(?:\+?1[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}\b",
        "api_key": r"\b[A-Za-z0-9]{32,}\b",  # Long alphanumeric strings
        "password_log": r"(?i)(password|passwd|pwd)[\s:=]+[^\s]+",
        "token": r"(?i)(token|bearer|api[\s_-]?key)[\s:=]+[^\s]+",
    }

    # Private IP ranges (don't redact these)
    PRIVATE_IP_PATTERNS = [
        r"^10\.",
        r"^172\.(1[6-9]|2[0-9]|3[01])\.",
        r"^192\.168\.",
        r"^127\.",
    ]

    def __init__(self):
        """Initialize sanitizer with compiled patterns."""
        self.compiled_patterns = {name: re.compile(pattern) for name, pattern in self.PATTERNS.items()}
        self.private_ip_patterns = [re.compile(pattern) for pattern in self.PRIVATE_IP_PATTERNS]

    def sanitize(self, text: str) -> Tuple[str, List[str]]:  # noqa: C901
        """
        Sanitize PII from text.

        Args:
            text: Input text

        Returns:
            Tuple of (sanitized_text, list_of_detected_pii_types)
        """
        if not text:
            return text, []

        sanitized = text
        detected_types = []

        # Email addresses
        if self.compiled_patterns["email"].search(sanitized):
            sanitized = self.compiled_patterns["email"].sub("[EMAIL_REDACTED]", sanitized)
            detected_types.append("email")

        # IP addresses (public only)
        ip_matches = self.compiled_patterns["ipv4"].findall(sanitized)
        for ip in ip_matches:
            if not self._is_private_ip(ip):
                sanitized = sanitized.replace(ip, "[IP_REDACTED]")
                if "ipv4" not in detected_types:
                    detected_types.append("ipv4")

        # Credit cards
        if self.compiled_patterns["credit_card"].search(sanitized):
            sanitized = self.compiled_patterns["credit_card"].sub("[CC_REDACTED]", sanitized)
            detected_types.append("credit_card")

        # SSN
        if self.compiled_patterns["ssn"].search(sanitized):
            sanitized = self.compiled_patterns["ssn"].sub("[SSN_REDACTED]", sanitized)
            detected_types.append("ssn")

        # Phone numbers
        if self.compiled_patterns["phone"].search(sanitized):
            sanitized = self.compiled_patterns["phone"].sub("[PHONE_REDACTED]", sanitized)
            detected_types.append("phone")

        # Passwords in logs
        if self.compiled_patterns["password_log"].search(sanitized):
            sanitized = self.compiled_patterns["password_log"].sub(r"\1=[REDACTED]", sanitized)
            detected_types.append("password")

        # Tokens
        if self.compiled_patterns["token"].search(sanitized):
            sanitized = self.compiled_patterns["token"].sub(r"\1=[REDACTED]", sanitized)
            detected_types.append("token")

        # API keys (aggressive - any 32+ char alphanumeric)
        # Only redact if looks like actual key (contains both letters and numbers)
        api_key_matches = self.compiled_patterns["api_key"].findall(sanitized)
        for match in api_key_matches:
            if re.search(r"[A-Za-z]", match) and re.search(r"[0-9]", match):
                sanitized = sanitized.replace(match, "[API_KEY_REDACTED]")
                if "api_key" not in detected_types:
                    detected_types.append("api_key")

        return sanitized, detected_types

    def _is_private_ip(self, ip: str) -> bool:
        """Check if IP address is private."""
        for pattern in self.private_ip_patterns:
            if pattern.match(ip):
                return True
        return False

    def sanitize_dict(self, data: Dict) -> Tuple[Dict, List[str]]:
        """
        Recursively sanitize dictionary.

        Args:
            data: Input dictionary

        Returns:
            Tuple of (sanitized_dict, list_of_detected_pii_types)
        """
        sanitized: Dict[str, Any] = {}
        all_detected: List[str] = []

        for key, value in data.items():
            if isinstance(value, str):
                sanitized[key], detected = self.sanitize(value)
                all_detected.extend(detected)
            elif isinstance(value, dict):
                sanitized[key], detected = self.sanitize_dict(value)
                all_detected.extend(detected)
            elif isinstance(value, list):
                sanitized[key] = []
                for item in value:
                    if isinstance(item, str):
                        clean_item, detected = self.sanitize(item)
                        sanitized[key].append(clean_item)
                        all_detected.extend(detected)
                    else:
                        sanitized[key].append(item)
            else:
                sanitized[key] = value

        return sanitized, list(set(all_detected))
