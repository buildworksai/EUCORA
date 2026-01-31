# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CMDB Validation Engine.

Validates CMDB data against configured rules and generates
quality scores and discrepancy reports.
"""
import logging
import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from ..models import CMDBValidationRule

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of validating a single field or record."""

    passed: bool
    rule_name: str
    rule_type: str
    severity: str
    field_name: Optional[str] = None
    message: str = ""
    expected_value: Optional[str] = None
    actual_value: Optional[str] = None
    auto_fix_available: bool = False
    suggested_fix: Optional[Any] = None


@dataclass
class RecordValidationResult:
    """Aggregated validation result for a record."""

    ci_sys_id: str
    ci_name: str
    ci_class: str
    is_valid: bool
    errors: List[ValidationResult] = field(default_factory=list)
    warnings: List[ValidationResult] = field(default_factory=list)
    infos: List[ValidationResult] = field(default_factory=list)

    @property
    def has_critical_issues(self) -> bool:
        """Check if record has any errors."""
        return len(self.errors) > 0

    @property
    def total_issues(self) -> int:
        """Total number of issues."""
        return len(self.errors) + len(self.warnings)


class CMDBValidationEngine:
    """
    Validates CMDB data against configured rules.

    Supports:
    - Required field validation
    - Format/regex validation
    - Range validation
    - Referential integrity
    - Custom rules
    """

    def __init__(self, rules: Optional[List[CMDBValidationRule]] = None):
        """
        Initialize validation engine.

        Args:
            rules: List of validation rules (or None to load from DB)
        """
        self.rules = rules or []
        self._rules_by_table: Dict[str, List[CMDBValidationRule]] = {}
        self._compile_rules()

    def _compile_rules(self) -> None:
        """Compile rules by table for faster lookup."""
        self._rules_by_table = {}
        for rule in self.rules:
            if rule.cmdb_table not in self._rules_by_table:
                self._rules_by_table[rule.cmdb_table] = []
            self._rules_by_table[rule.cmdb_table].append(rule)

    @classmethod
    async def create(cls, table: Optional[str] = None) -> "CMDBValidationEngine":
        """
        Create engine with rules from database.

        Args:
            table: Optional table name to filter rules

        Returns:
            Configured CMDBValidationEngine
        """
        query = CMDBValidationRule.objects.filter(is_active=True)
        if table:
            query = query.filter(cmdb_table=table)

        rules = [rule async for rule in query]
        return cls(rules=rules)

    def validate_record(
        self,
        record: Dict[str, Any],
        table: str,
    ) -> RecordValidationResult:
        """
        Validate a single CMDB record.

        Args:
            record: CI record data
            table: CMDB table name

        Returns:
            RecordValidationResult with all validation findings
        """
        ci_sys_id = record.get("sys_id", "")
        ci_name = record.get("name", record.get("u_name", "Unknown"))

        result = RecordValidationResult(
            ci_sys_id=ci_sys_id,
            ci_name=ci_name,
            ci_class=table,
            is_valid=True,
        )

        # Get rules for this table
        rules = self._rules_by_table.get(table, [])

        for rule in rules:
            validation = self._apply_rule(rule, record)

            if validation:
                if validation.severity == "error":
                    result.errors.append(validation)
                    result.is_valid = False
                elif validation.severity == "warning":
                    result.warnings.append(validation)
                else:
                    result.infos.append(validation)

        return result

    def _apply_rule(
        self,
        rule: CMDBValidationRule,
        record: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """
        Apply a single validation rule to a record.

        Args:
            rule: Validation rule to apply
            record: CI record data

        Returns:
            ValidationResult if rule fails, None if passes
        """
        if rule.rule_type == CMDBValidationRule.RuleType.REQUIRED:
            return self._validate_required(rule, record)
        elif rule.rule_type == CMDBValidationRule.RuleType.FORMAT:
            return self._validate_format(rule, record)
        elif rule.rule_type == CMDBValidationRule.RuleType.REGEX:
            return self._validate_regex(rule, record)
        elif rule.rule_type == CMDBValidationRule.RuleType.RANGE:
            return self._validate_range(rule, record)
        elif rule.rule_type == CMDBValidationRule.RuleType.REFERENCE:
            return self._validate_reference(rule, record)
        elif rule.rule_type == CMDBValidationRule.RuleType.CUSTOM:
            return self._validate_custom(rule, record)

        return None

    def _validate_required(
        self,
        rule: CMDBValidationRule,
        record: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """Validate required field."""
        field_name = rule.field_name
        value = record.get(field_name)

        if not value or (isinstance(value, str) and value.strip() == ""):
            return ValidationResult(
                passed=False,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                severity=rule.severity,
                field_name=field_name,
                message=f"Required field '{field_name}' is missing or empty",
                actual_value=str(value) if value else None,
                auto_fix_available=False,
            )

        return None

    def _validate_format(
        self,
        rule: CMDBValidationRule,
        record: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """Validate field format."""
        field_name = rule.field_name
        value = record.get(field_name)

        if not value:
            return None

        expected_format = rule.rule_config.get("format", "")

        # Common format validations
        if expected_format == "ip_address":
            ip_pattern = r"^(?:(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(?:25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$"
            if not re.match(ip_pattern, str(value)):
                return ValidationResult(
                    passed=False,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    field_name=field_name,
                    message=f"Invalid IP address format in '{field_name}'",
                    expected_value="Valid IPv4 address",
                    actual_value=str(value),
                    auto_fix_available=False,
                )

        elif expected_format == "mac_address":
            mac_pattern = r"^([0-9A-Fa-f]{2}[:-]){5}([0-9A-Fa-f]{2})$"
            if not re.match(mac_pattern, str(value)):
                return ValidationResult(
                    passed=False,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    field_name=field_name,
                    message=f"Invalid MAC address format in '{field_name}'",
                    expected_value="Valid MAC address (XX:XX:XX:XX:XX:XX)",
                    actual_value=str(value),
                    auto_fix_available=False,
                )

        elif expected_format == "serial_number":
            if len(str(value)) < 3 or len(str(value)) > 50:
                return ValidationResult(
                    passed=False,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    field_name=field_name,
                    message=f"Invalid serial number length in '{field_name}'",
                    expected_value="3-50 characters",
                    actual_value=str(value),
                    auto_fix_available=False,
                )

        return None

    def _validate_regex(
        self,
        rule: CMDBValidationRule,
        record: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """Validate field against regex pattern."""
        field_name = rule.field_name
        value = record.get(field_name)

        if not value:
            return None

        pattern = rule.rule_config.get("pattern", "")
        if not pattern:
            return None

        try:
            if not re.match(pattern, str(value)):
                return ValidationResult(
                    passed=False,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    field_name=field_name,
                    message=f"Field '{field_name}' does not match required pattern",
                    expected_value=f"Pattern: {pattern}",
                    actual_value=str(value),
                    auto_fix_available=False,
                )
        except re.error as e:
            logger.warning(f"Invalid regex pattern in rule {rule.name}: {e}")

        return None

    def _validate_range(
        self,
        rule: CMDBValidationRule,
        record: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """Validate numeric field range."""
        field_name = rule.field_name
        value = record.get(field_name)

        if value is None:
            return None

        try:
            numeric_value = float(value)
            min_val = rule.rule_config.get("min")
            max_val = rule.rule_config.get("max")

            if min_val is not None and numeric_value < min_val:
                return ValidationResult(
                    passed=False,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    field_name=field_name,
                    message=f"Field '{field_name}' is below minimum value",
                    expected_value=f"Minimum: {min_val}",
                    actual_value=str(value),
                    auto_fix_available=False,
                )

            if max_val is not None and numeric_value > max_val:
                return ValidationResult(
                    passed=False,
                    rule_name=rule.name,
                    rule_type=rule.rule_type,
                    severity=rule.severity,
                    field_name=field_name,
                    message=f"Field '{field_name}' exceeds maximum value",
                    expected_value=f"Maximum: {max_val}",
                    actual_value=str(value),
                    auto_fix_available=False,
                )

        except (ValueError, TypeError):
            pass

        return None

    def _validate_reference(
        self,
        rule: CMDBValidationRule,
        record: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """Validate referential integrity (placeholder)."""
        # This would need async lookup of related records
        # For now, just check if the reference field has a value
        field_name = rule.field_name
        value = record.get(field_name)

        if not value and rule.rule_config.get("required", False):
            return ValidationResult(
                passed=False,
                rule_name=rule.name,
                rule_type=rule.rule_type,
                severity=rule.severity,
                field_name=field_name,
                message=f"Reference field '{field_name}' is missing",
                auto_fix_available=False,
            )

        return None

    def _validate_custom(
        self,
        rule: CMDBValidationRule,
        record: Dict[str, Any],
    ) -> Optional[ValidationResult]:
        """Apply custom validation rule."""
        # Custom rules use Python expressions
        # This is a simplified implementation
        expression = rule.rule_config.get("expression", "")
        if not expression:
            return None

        try:
            # Create a safe context for evaluation
            context = {"record": record, "value": record.get(rule.field_name)}

            # Very limited eval - in production, use a proper expression parser
            # For safety, we only support simple comparisons
            if "==" in expression or "!=" in expression or "in" in expression:
                result = eval(expression, {"__builtins__": {}}, context)
                if not result:
                    return ValidationResult(
                        passed=False,
                        rule_name=rule.name,
                        rule_type=rule.rule_type,
                        severity=rule.severity,
                        field_name=rule.field_name,
                        message=f"Custom validation failed: {rule.description or rule.name}",
                        auto_fix_available=False,
                    )
        except Exception as e:
            logger.warning(f"Custom rule {rule.name} evaluation failed: {e}")

        return None

    def calculate_quality_score(
        self,
        validation_results: List[RecordValidationResult],
    ) -> Dict[str, float]:
        """
        Calculate quality scores from validation results.

        Args:
            validation_results: List of validation results

        Returns:
            Dict with quality scores (0-100)
        """
        if not validation_results:
            return {
                "overall_score": 100.0,
                "completeness_score": 100.0,
                "accuracy_score": 100.0,
                "consistency_score": 100.0,
            }

        total_records = len(validation_results)
        _valid_records = sum(1 for r in validation_results if r.is_valid)  # noqa: F841
        _records_with_warnings = sum(1 for r in validation_results if r.warnings)  # noqa: F841

        # Count issues by type
        required_issues = 0
        format_issues = 0
        other_issues = 0

        for result in validation_results:
            for error in result.errors + result.warnings:
                if error.rule_type == "required":
                    required_issues += 1
                elif error.rule_type in ("format", "regex"):
                    format_issues += 1
                else:
                    other_issues += 1

        # Calculate scores
        completeness_score = 100.0 * (1 - required_issues / max(total_records, 1) / 5)
        accuracy_score = 100.0 * (1 - format_issues / max(total_records, 1) / 5)
        consistency_score = 100.0 * (1 - other_issues / max(total_records, 1) / 5)
        overall_score = (completeness_score + accuracy_score + consistency_score) / 3

        return {
            "overall_score": max(0, min(100, overall_score)),
            "completeness_score": max(0, min(100, completeness_score)),
            "accuracy_score": max(0, min(100, accuracy_score)),
            "consistency_score": max(0, min(100, consistency_score)),
        }
