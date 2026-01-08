# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Deployment Intent models and state machine.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel, CorrelationIdModel, DemoQuerySet


class DeploymentIntent(TimeStampedModel, CorrelationIdModel):
    """
    Deployment intent with state machine.
    
    State transitions:
    PENDING → AWAITING_CAB (if high risk) → APPROVED → DEPLOYING → COMPLETED
    PENDING → APPROVED (if low risk) → DEPLOYING → COMPLETED
    Any state → FAILED or ROLLED_BACK
    """
    class Status(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        AWAITING_CAB = 'AWAITING_CAB', 'Awaiting CAB Approval'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        DEPLOYING = 'DEPLOYING', 'Deploying'
        COMPLETED = 'COMPLETED', 'Completed'
        FAILED = 'FAILED', 'Failed'
        ROLLED_BACK = 'ROLLED_BACK', 'Rolled Back'
    
    class Ring(models.TextChoices):
        LAB = 'LAB', 'Lab'
        CANARY = 'CANARY', 'Canary'
        PILOT = 'PILOT', 'Pilot'
        DEPARTMENT = 'DEPARTMENT', 'Department'
        GLOBAL = 'GLOBAL', 'Global'
    
    app_name = models.CharField(max_length=255, help_text='Application name')
    version = models.CharField(max_length=50, help_text='Application version')
    target_ring = models.CharField(max_length=20, choices=Ring.choices, help_text='Target deployment ring')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING, help_text='Deployment status')
    
    # Evidence pack reference
    evidence_pack_id = models.UUIDField(help_text='Evidence pack correlation ID')
    
    # Risk assessment
    risk_score = models.IntegerField(null=True, blank=True, help_text='Calculated risk score (0-100)')
    requires_cab_approval = models.BooleanField(default=False, help_text='Whether CAB approval is required')
    
    # Submitter
    submitter = models.ForeignKey(User, on_delete=models.CASCADE, related_name='deployment_intents', help_text='User who submitted the deployment')
    is_demo = models.BooleanField(default=False, db_index=True, help_text='Whether this is demo data')

    objects = DemoQuerySet.as_manager()
    
    class Meta:
        indexes = [
            models.Index(fields=['status', 'target_ring']),
            models.Index(fields=['correlation_id']),
            models.Index(fields=['app_name', 'version']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Deployment Intent'
        verbose_name_plural = 'Deployment Intents'
    
    def __str__(self):
        return f'{self.app_name} {self.version} → {self.target_ring} ({self.status})'


class RingDeployment(TimeStampedModel):
    """
    Tracks deployment progress within a specific ring.
    """
    deployment_intent = models.ForeignKey(DeploymentIntent, on_delete=models.CASCADE, related_name='ring_deployments')
    ring = models.CharField(max_length=20, choices=DeploymentIntent.Ring.choices)
    
    # Execution plane tracking
    connector_type = models.CharField(max_length=20, help_text='Connector type (intune, jamf, sccm, landscape, ansible)')
    connector_object_id = models.CharField(max_length=255, null=True, blank=True, help_text='Platform-specific object ID')
    
    # Metrics
    success_count = models.IntegerField(default=0, help_text='Number of successful deployments')
    failure_count = models.IntegerField(default=0, help_text='Number of failed deployments')
    success_rate = models.FloatField(default=0.0, help_text='Success rate (0.0 - 1.0)')
    
    # Promotion status
    promoted_at = models.DateTimeField(null=True, blank=True, help_text='When promoted to next ring')
    promotion_gate_passed = models.BooleanField(default=False, help_text='Whether promotion gate criteria met')
    is_demo = models.BooleanField(default=False, db_index=True, help_text='Whether this is demo data')

    objects = DemoQuerySet.as_manager()
    
    class Meta:
        indexes = [
            models.Index(fields=['deployment_intent', 'ring']),
        ]
        verbose_name = 'Ring Deployment'
        verbose_name_plural = 'Ring Deployments'
    
    def __str__(self):
        return f'{self.deployment_intent.app_name} - {self.ring} ({self.success_rate:.1%})'
