# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine models for risk assessment and ABAC.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import CorrelationIdModel, TimeStampedModel


class RiskModel(TimeStampedModel):
    """
    Versioned risk scoring model.

    Defines risk factors, weights, and CAB approval threshold.
    """

    version = models.CharField(max_length=10, unique=True, help_text="Risk model version (e.g., v1.0)")
    factors = models.JSONField(help_text="List of risk factors with weights and rubrics")
    threshold = models.IntegerField(default=50, help_text="CAB approval threshold (0-100)")
    is_active = models.BooleanField(default=False, help_text="Active risk model (only one can be active)")
    description = models.TextField(blank=True, help_text="Description of changes in this version")

    class Meta:
        ordering = ["-version"]
        verbose_name = "Risk Model"
        verbose_name_plural = "Risk Models"

    def __str__(self):
        return f'Risk Model {self.version} ({"Active" if self.is_active else "Inactive"})'

    def save(self, *args, **kwargs):
        """Ensure only one active risk model."""
        if self.is_active:
            # Deactivate all other risk models
            RiskModel.objects.filter(is_active=True).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)


class RiskAssessment(TimeStampedModel):
    """
    Risk assessment result for a deployment intent.

    Stores calculated risk score and factor breakdown.
    """

    deployment_intent_id = models.UUIDField(help_text="Deployment intent correlation ID")
    risk_model_version = models.CharField(max_length=10, help_text="Risk model version used")
    risk_score = models.IntegerField(help_text="Calculated risk score (0-100)")
    factor_scores = models.JSONField(help_text="Detailed breakdown per factor")
    requires_cab_approval = models.BooleanField(help_text="Whether CAB approval is required")

    class Meta:
        indexes = [
            models.Index(fields=["risk_score"]),
            models.Index(fields=["deployment_intent_id"]),
        ]
        verbose_name = "Risk Assessment"
        verbose_name_plural = "Risk Assessments"

    def __str__(self):
        return f"Risk Assessment {self.deployment_intent_id} - Score: {self.risk_score}"


class ApplicationPolicy(TimeStampedModel, CorrelationIdModel):
    """
    Deployment policies for applications.

    Links policies to applications with platform scope and version targeting.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, help_text="Policy name")
    description = models.TextField(blank=True, help_text="Policy description")

    # Target
    application = models.ForeignKey(
        "application_portfolio.Application",
        on_delete=models.CASCADE,
        related_name="policies",
        help_text="Target application",
    )
    application_version = models.ForeignKey(
        "application_portfolio.ApplicationVersion",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="policies",
        help_text="Apply to specific version only (null = all versions)",
    )

    # Scope
    platform = models.CharField(
        max_length=32,
        help_text="Target platform (windows, macos, linux, ios, android)",
    )

    # Policy Status
    is_active = models.BooleanField(default=True, help_text="Whether policy is active")
    is_default = models.BooleanField(default=False, help_text="Default policy for app/platform")

    # Audit
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_policies",
        help_text="User who created the policy",
    )

    class Meta:
        unique_together = [["application", "application_version", "platform"]]
        ordering = ["application", "platform", "-created_at"]
        indexes = [
            models.Index(fields=["application", "platform"]),
            models.Index(fields=["is_active"]),
        ]
        verbose_name = "Application Policy"
        verbose_name_plural = "Application Policies"

    def __str__(self):
        version_str = f" v{self.application_version.version}" if self.application_version else ""
        return f"{self.application.name}{version_str} - {self.platform} ({self.name})"

    def get_settings_dict(self) -> dict:
        """Get all settings as a nested dictionary."""
        result = {}
        for setting in self.settings.all():
            category = setting.category
            if category not in result:
                result[category] = {}
            result[category][setting.setting_key] = setting.setting_value
        return result


class PolicySetting(TimeStampedModel):
    """
    Individual policy settings.

    Stores key-value pairs for policy configuration, organized by category.
    """

    class SettingCategory(models.TextChoices):
        INSTALLATION = "installation", "Installation"
        UNINSTALL = "uninstall", "Uninstall"
        UPDATE = "update", "Update"
        CONFIGURATION = "configuration", "Configuration"
        RESTART = "restart", "Device Restart"
        DEPENDENCY = "dependency", "Dependencies"
        COMPLIANCE = "compliance", "Compliance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    policy = models.ForeignKey(
        ApplicationPolicy,
        on_delete=models.CASCADE,
        related_name="settings",
        help_text="Parent policy",
    )

    category = models.CharField(
        max_length=32,
        choices=SettingCategory.choices,
        help_text="Setting category",
    )
    setting_key = models.CharField(max_length=64, help_text="Setting key")
    setting_value = models.JSONField(help_text="Setting value (flexible JSON)")

    # Execution plane mapping
    intune_mapping = models.JSONField(default=dict, blank=True, help_text="Intune-specific mapping")
    jamf_mapping = models.JSONField(default=dict, blank=True, help_text="Jamf Pro-specific mapping")
    sccm_mapping = models.JSONField(default=dict, blank=True, help_text="SCCM-specific mapping")

    class Meta:
        unique_together = [["policy", "category", "setting_key"]]
        ordering = ["policy", "category", "setting_key"]
        indexes = [
            models.Index(fields=["policy", "category"]),
        ]
        verbose_name = "Policy Setting"
        verbose_name_plural = "Policy Settings"

    def __str__(self):
        return f"{self.policy.name} - {self.category}.{self.setting_key}"


class PolicyTemplate(TimeStampedModel):
    """
    Reusable policy templates.

    Pre-configured policy templates for common deployment scenarios.
    """

    class TemplateType(models.TextChoices):
        STANDARD = "standard", "Standard Application"
        SECURITY = "security", "Security-Critical"
        PRODUCTIVITY = "productivity", "Productivity Suite"
        BROWSER = "browser", "Web Browser"
        DEVELOPMENT = "development", "Development Tool"
        ENTERPRISE = "enterprise", "Enterprise Required"
        OPTIONAL = "optional", "Optional/Self-Service"
        CUSTOM = "custom", "Custom Template"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=128, help_text="Template name")
    template_type = models.CharField(
        max_length=32,
        choices=TemplateType.choices,
        help_text="Template type",
    )
    description = models.TextField(help_text="Template description")

    # Template settings (JSON blob)
    settings = models.JSONField(default=dict, help_text="Pre-configured settings dictionary")

    # Metadata
    is_system = models.BooleanField(default=False, help_text="Whether this is a system template (read-only)")
    platform = models.CharField(
        max_length=32,
        blank=True,
        help_text="Platform-specific template (empty = all platforms)",
    )

    class Meta:
        ordering = ["template_type", "name"]
        indexes = [
            models.Index(fields=["template_type"]),
            models.Index(fields=["is_system"]),
        ]
        verbose_name = "Policy Template"
        verbose_name_plural = "Policy Templates"

    def __str__(self):
        platform_str = f" ({self.platform})" if self.platform else ""
        return f"{self.name}{platform_str} ({self.get_template_type_display()})"
