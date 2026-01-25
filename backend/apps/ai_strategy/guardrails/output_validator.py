# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Output validation guardrails.
"""
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class ValidationResult:
    """Validation result."""

    is_valid: bool
    issues: List[str]
    sanitized_output: str


class OutputValidator:
    """
    Validate LLM outputs before use.

    Checks for:
    - Harmful commands (rm -rf, DROP TABLE, etc.)
    - Unsafe suggestions
    - Required structure
    - Length limits
    """

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r"rm\s+-rf\s+/",
        r"DROP\s+TABLE",
        r"DELETE\s+FROM.*WHERE\s+1=1",
        r";\s*rm\s+-rf",
        r"eval\(",
        r"exec\(",
        r"__import__",
        r"format\s*\(",  # Format string attacks
    ]

    # Required structure patterns for specific use cases
    STRUCTURE_PATTERNS = {
        "incident_classification": [
            r"Severity:\s*(CRITICAL|HIGH|MEDIUM|LOW)",
            r"Confidence:\s*[0-9.]+",
        ],
        "remediation": [
            r"Steps:",
            r"Rollback:",
        ],
    }

    def __init__(self):
        """Initialize validator with compiled patterns."""
        self.dangerous_compiled = [re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS]

    def validate(self, output: str, use_case: Optional[str] = None, max_length: int = 5000) -> ValidationResult:
        """
        Validate LLM output.

        Args:
            output: LLM output text
            use_case: Use case for structure validation
            max_length: Maximum allowed length

        Returns:
            ValidationResult with validity and issues
        """
        issues = []

        # Length check
        if len(output) > max_length:
            issues.append(f"Output exceeds maximum length ({len(output)} > {max_length})")

        # Dangerous pattern check
        for pattern in self.dangerous_compiled:
            if pattern.search(output):
                issues.append(f"Dangerous pattern detected: {pattern.pattern}")

        # Structure check if use case specified
        if use_case and use_case in self.STRUCTURE_PATTERNS:
            required_patterns = self.STRUCTURE_PATTERNS[use_case]
            for pattern_str in required_patterns:
                pattern = re.compile(pattern_str, re.IGNORECASE)
                if not pattern.search(output):
                    issues.append(f"Missing required structure: {pattern_str}")

        # Sanitize output (remove any remaining dangerous content)
        sanitized = self._sanitize_dangerous_content(output)

        return ValidationResult(is_valid=len(issues) == 0, issues=issues, sanitized_output=sanitized)

    def _sanitize_dangerous_content(self, text: str) -> str:
        """Remove dangerous content from text."""
        sanitized = text

        for pattern in self.dangerous_compiled:
            sanitized = pattern.sub("[DANGEROUS_CONTENT_REMOVED]", sanitized)

        return sanitized

    def validate_json_structure(self, data: Dict[str, Any], required_fields: List[str]) -> ValidationResult:
        """
        Validate JSON structure.

        Args:
            data: JSON data
            required_fields: Required field names

        Returns:
            ValidationResult
        """
        issues = []

        for field in required_fields:
            if field not in data:
                issues.append(f"Missing required field: {field}")

        return ValidationResult(is_valid=len(issues) == 0, issues=issues, sanitized_output=str(data))
