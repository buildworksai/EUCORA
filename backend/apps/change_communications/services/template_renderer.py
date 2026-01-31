# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Template Renderer for Change Communications.

Provides variable substitution and rendering for communication templates.
"""
import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, Optional

from ..models import ChangeRecord, CommunicationTemplate

logger = logging.getLogger(__name__)


@dataclass
class RenderedTemplate:
    """Result of rendering a template."""

    subject: str
    body: str
    variables_used: list[str]


class TemplateRenderer:
    """
    Renders communication templates with variable substitution.

    Supports:
    - ${variable_name} syntax
    - Nested object access: ${change.number}
    - Default values: ${variable|default}
    """

    # Standard variables available for all templates
    STANDARD_VARIABLES = [
        "change_number",
        "change_type",
        "short_description",
        "description",
        "risk_level",
        "impact",
        "planned_start",
        "planned_end",
        "state",
        "application_name",
        "version",
        "device_count",
        "contact_email",
    ]

    # Regex for variable substitution
    VARIABLE_PATTERN = re.compile(r"\$\{([^}|]+)(?:\|([^}]*))?\}")

    def __init__(self, change_record: Optional[ChangeRecord] = None):
        """
        Initialize renderer.

        Args:
            change_record: Optional change record for context
        """
        self.change_record = change_record
        self._context: Dict[str, Any] = {}

    def build_context(
        self,
        change_record: Optional[ChangeRecord] = None,
        extra_context: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Build context dictionary from change record and extras.

        Args:
            change_record: Change record to extract context from
            extra_context: Additional context variables

        Returns:
            Context dictionary for template rendering
        """
        record = change_record or self.change_record
        context = {}

        if record:
            context.update(
                {
                    "change_number": record.servicenow_number,
                    "change_type": record.change_type,
                    "short_description": record.short_description,
                    "description": record.description,
                    "risk_level": record.risk_level,
                    "impact": record.impact,
                    "planned_start": record.planned_start.strftime("%Y-%m-%d %H:%M") if record.planned_start else "",
                    "planned_end": record.planned_end.strftime("%Y-%m-%d %H:%M") if record.planned_end else "",
                    "state": record.get_state_display() if hasattr(record, "get_state_display") else record.state,
                }
            )

            # Add deployment intent context if available
            if record.deployment_intent:
                intent = record.deployment_intent
                context.update(
                    {
                        "application_name": getattr(intent, "application_name", ""),
                        "version": getattr(intent, "version", ""),
                        "device_count": getattr(intent, "target_device_count", 0),
                    }
                )

            # Add owner context
            if record.requested_by:
                context["contact_email"] = record.requested_by.email

        if extra_context:
            context.update(extra_context)

        self._context = context
        return context

    def render(
        self,
        template: CommunicationTemplate,
        context: Optional[Dict[str, Any]] = None,
    ) -> RenderedTemplate:
        """
        Render a template with the provided context.

        Args:
            template: Template to render
            context: Context dictionary (uses self._context if not provided)

        Returns:
            RenderedTemplate with subject and body
        """
        ctx = context or self._context
        variables_used = []

        def replace_variable(match: re.Match) -> str:
            variable_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""

            variables_used.append(variable_name)

            # Handle nested access (e.g., change.number)
            value = self._get_nested_value(ctx, variable_name)

            if value is None or value == "":
                return default_value

            return str(value)

        subject = self.VARIABLE_PATTERN.sub(replace_variable, template.subject_template)
        body = self.VARIABLE_PATTERN.sub(replace_variable, template.body_template)

        return RenderedTemplate(
            subject=subject,
            body=body,
            variables_used=list(set(variables_used)),
        )

    def _get_nested_value(self, context: Dict[str, Any], key: str) -> Any:
        """Get value from nested dictionary using dot notation."""
        parts = key.split(".")
        value = context

        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            else:
                return None

            if value is None:
                return None

        return value

    def render_string(
        self,
        template_string: str,
        context: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Render a raw template string.

        Args:
            template_string: String with ${variable} placeholders
            context: Context dictionary

        Returns:
            Rendered string
        """
        ctx = context or self._context

        def replace_variable(match: re.Match) -> str:
            variable_name = match.group(1)
            default_value = match.group(2) if match.group(2) else ""
            value = self._get_nested_value(ctx, variable_name)
            return str(value) if value else default_value

        return self.VARIABLE_PATTERN.sub(replace_variable, template_string)

    def preview(
        self,
        template: CommunicationTemplate,
        sample_context: Optional[Dict[str, Any]] = None,
    ) -> RenderedTemplate:
        """
        Preview a template with sample data.

        Args:
            template: Template to preview
            sample_context: Sample context (generates defaults if not provided)

        Returns:
            RenderedTemplate with sample content
        """
        if not sample_context:
            sample_context = {
                "change_number": "CHG0012345",
                "change_type": "Normal",
                "short_description": "Sample Application Update",
                "description": "This is a sample change description.",
                "risk_level": "Low",
                "impact": "Low",
                "planned_start": "2026-02-01 09:00",
                "planned_end": "2026-02-01 12:00",
                "state": "Scheduled",
                "application_name": "Sample App",
                "version": "2.0.0",
                "device_count": "1,234",
                "contact_email": "admin@example.com",
            }

        return self.render(template, sample_context)

    @staticmethod
    def get_available_variables() -> list[Dict[str, str]]:
        """Get list of available template variables with descriptions."""
        return [
            {"name": "change_number", "description": "ServiceNow change number (CHGxxxxxxx)"},
            {"name": "change_type", "description": "Type of change (Standard, Normal, Emergency)"},
            {"name": "short_description", "description": "Brief change description"},
            {"name": "description", "description": "Full change description"},
            {"name": "risk_level", "description": "Risk assessment level"},
            {"name": "impact", "description": "Impact assessment"},
            {"name": "planned_start", "description": "Planned start date/time"},
            {"name": "planned_end", "description": "Planned end date/time"},
            {"name": "state", "description": "Current change state"},
            {"name": "application_name", "description": "Name of application being deployed"},
            {"name": "version", "description": "Application version"},
            {"name": "device_count", "description": "Number of affected devices"},
            {"name": "contact_email", "description": "Contact email for questions"},
        ]
