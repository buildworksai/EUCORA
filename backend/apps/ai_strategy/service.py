# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
AI Strategy service - main integration point.
"""
from typing import Any, Dict, Optional

from decouple import config

from apps.core.structured_logging import StructuredLogger

from .guardrails import OutputValidator, PIISanitizer
from .prompts import registry as prompt_registry
from .providers import AzureOpenAIProvider, LLMProvider, MockLLMProvider, OpenAIProvider


class AIStrategyService:
    """
    Main AI service integrating providers, prompts, and guardrails.
    """

    def __init__(self, provider: Optional[LLMProvider] = None):
        """
        Initialize AI service.

        Args:
            provider: LLM provider (auto-detected if None)
        """
        self.provider = provider or self._get_default_provider()
        self.pii_sanitizer = PIISanitizer()
        self.output_validator = OutputValidator()
        self.logger = StructuredLogger(__name__)

    def _get_default_provider(self) -> LLMProvider:
        """Get default provider based on configuration."""
        provider_type = config("AI_PROVIDER", default="mock")

        if provider_type == "openai":
            return OpenAIProvider()
        elif provider_type == "azure_openai":
            return AzureOpenAIProvider()
        else:
            # Default to mock for testing/air-gapped
            return MockLLMProvider()

    def classify_incident(
        self,
        title: str,
        description: str,
        affected_systems: str = "",
        error_messages: str = "",
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Classify incident severity using AI.

        Args:
            title: Incident title
            description: Incident description
            affected_systems: Affected systems
            error_messages: Error messages
            correlation_id: Correlation ID for tracking

        Returns:
            Classification result with severity, confidence, reasoning
        """
        # Sanitize PII from inputs
        title_clean, _ = self.pii_sanitizer.sanitize(title)
        description_clean, pii_detected = self.pii_sanitizer.sanitize(description)
        error_clean, _ = self.pii_sanitizer.sanitize(error_messages)

        if pii_detected:
            self.logger.warning(
                "PII detected and sanitized in incident classification",
                extra={"pii_types": pii_detected, "correlation_id": correlation_id},
            )

        # Get prompt template
        template = prompt_registry.get("incident_classification", "v1")
        messages = template.format(
            title=title_clean,
            description=description_clean,
            affected_systems=affected_systems,
            error_messages=error_clean,
        )

        # Generate completion
        completion = self.provider.complete(messages, temperature=0.3)

        # Validate output
        validation = self.output_validator.validate(completion.content, use_case="incident_classification")

        if not validation.is_valid:
            self.logger.error(
                "AI output validation failed", extra={"issues": validation.issues, "correlation_id": correlation_id}
            )

        return {
            "classification": validation.sanitized_output,
            "confidence": completion.confidence,
            "model": completion.model,
            "provider": completion.provider,
            "validation_passed": validation.is_valid,
            "validation_issues": validation.issues,
            "pii_detected": pii_detected,
            "evidence": {
                "input_sanitized": bool(pii_detected),
                "tokens_used": completion.tokens_used,
                "correlation_id": correlation_id,
            },
        }

    def suggest_remediation(
        self,
        issue_description: str,
        platform: str,
        current_state: str = "",
        desired_state: str = "",
        constraints: str = "",
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Suggest remediation steps using AI.

        Args:
            issue_description: Issue description
            platform: Platform (windows, linux, macos)
            current_state: Current system state
            desired_state: Desired system state
            constraints: Constraints (permissions, downtime, etc.)
            correlation_id: Correlation ID for tracking

        Returns:
            Remediation suggestion with steps, rollback, risk
        """
        # Sanitize inputs
        issue_clean, pii_detected = self.pii_sanitizer.sanitize(issue_description)
        current_clean, _ = self.pii_sanitizer.sanitize(current_state)

        # Get prompt
        template = prompt_registry.get("remediation_suggestion", "v1")
        messages = template.format(
            issue_description=issue_clean,
            platform=platform,
            current_state=current_clean,
            desired_state=desired_state,
            constraints=constraints,
        )

        # Generate completion
        completion = self.provider.complete(messages, temperature=0.5)

        # Validate
        validation = self.output_validator.validate(completion.content, use_case="remediation")

        return {
            "remediation": validation.sanitized_output,
            "confidence": completion.confidence,
            "model": completion.model,
            "provider": completion.provider,
            "validation_passed": validation.is_valid,
            "validation_issues": validation.issues,
            "pii_detected": pii_detected,
            "evidence": {
                "input_sanitized": bool(pii_detected),
                "tokens_used": completion.tokens_used,
                "correlation_id": correlation_id,
            },
        }

    def assess_deployment_risk(
        self,
        package_name: str,
        package_version: str,
        platform: str,
        target_scope: str,
        privilege_level: str,
        scan_summary: Dict[str, int],
        correlation_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """
        Assess deployment risk using AI.

        Args:
            package_name: Package name
            package_version: Package version
            platform: Platform
            target_scope: Target scope
            privilege_level: Privilege level
            scan_summary: Vulnerability scan summary
            correlation_id: Correlation ID

        Returns:
            Risk assessment with score, factors, recommendations
        """
        # Get prompt
        template = prompt_registry.get("deployment_risk_assessment", "v1")
        messages = template.format(
            package_name=package_name,
            package_version=package_version,
            platform=platform,
            target_scope=target_scope,
            privilege_level=privilege_level,
            scan_summary=scan_summary,
            dependencies="",
            history="",
        )

        # Generate completion
        completion = self.provider.complete(messages, temperature=0.3)

        # Validate
        validation = self.output_validator.validate(completion.content)

        return {
            "risk_assessment": validation.sanitized_output,
            "confidence": completion.confidence,
            "model": completion.model,
            "provider": completion.provider,
            "validation_passed": validation.is_valid,
            "evidence": {"tokens_used": completion.tokens_used, "correlation_id": correlation_id},
        }

    def health_check(self) -> Dict[str, Any]:
        """
        Check AI service health.

        Returns:
            Health status
        """
        provider_healthy = self.provider.health_check()

        return {
            "provider": self.provider.get_provider_name(),
            "model": self.provider.get_model_name(),
            "healthy": provider_healthy,
            "guardrails": {"pii_sanitizer": True, "output_validator": True},
        }
