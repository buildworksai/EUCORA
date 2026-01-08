# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CAB Workflow models for approval workflows.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel, DemoQuerySet
from apps.deployment_intents.models import DeploymentIntent


class CABApproval(TimeStampedModel):
    """
    CAB approval record for deployment intent.
    """
    class Decision(models.TextChoices):
        PENDING = 'PENDING', 'Pending'
        APPROVED = 'APPROVED', 'Approved'
        REJECTED = 'REJECTED', 'Rejected'
        CONDITIONAL = 'CONDITIONAL', 'Conditional'
    
    deployment_intent = models.OneToOneField(DeploymentIntent, on_delete=models.CASCADE, related_name='cab_approval')
    decision = models.CharField(max_length=20, choices=Decision.choices, default=Decision.PENDING)
    approver = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='cab_approvals')
    comments = models.TextField(blank=True, help_text='Approval/rejection comments')
    conditions = models.JSONField(default=list, help_text='Conditional approval conditions')
    submitted_at = models.DateTimeField(auto_now_add=True)
    reviewed_at = models.DateTimeField(null=True, blank=True)
    external_change_request_id = models.CharField(
        max_length=255,
        null=True,
        blank=True,
        help_text='External change request ID (ServiceNow CR, Jira issue key, etc.)'
    )
    is_demo = models.BooleanField(default=False, db_index=True, help_text='Whether this is demo data')

    objects = DemoQuerySet.as_manager()
    
    class Meta:
        verbose_name = 'CAB Approval'
        verbose_name_plural = 'CAB Approvals'
    
    def __str__(self):
        return f'CAB Approval for {self.deployment_intent.app_name} - {self.decision}'
