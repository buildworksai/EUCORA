# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine models for risk assessment and ABAC.
"""
import json

from django.db import models

from apps.core.models import TimeStampedModel


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
