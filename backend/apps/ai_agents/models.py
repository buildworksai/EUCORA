# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
AI Agents models for EUCORA.

All AI recommendations require human approval before execution.
Immutable audit trail for all AI interactions.
"""
from django.db import models
from django.contrib.auth.models import User
from apps.core.models import TimeStampedModel
from apps.core.encryption import EncryptedCharField
import uuid


class AIModelProvider(TimeStampedModel):
    """
    Model Provider Configuration.
    API keys stored encrypted in vault (referenced by key_vault_ref).
    For development: api_key_dev stores key directly (DO NOT USE IN PRODUCTION).
    """
    class ProviderType(models.TextChoices):
        OPENAI = 'openai', 'OpenAI'
        ANTHROPIC = 'anthropic', 'Anthropic'
        GROQ = 'groq', 'Groq'
        HUGGINGFACE = 'huggingface', 'HuggingFace'
        AZURE_OPENAI = 'azure_openai', 'Azure OpenAI'
        GOOGLE_GEMINI = 'google_gemini', 'Google Gemini'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider_type = models.CharField(max_length=32, choices=ProviderType.choices)
    display_name = models.CharField(max_length=128)
    key_vault_ref = models.CharField(max_length=256, blank=True)  # Reference to vault secret
    # DEV ONLY: Encrypted API key storage (for development/demo purposes only)
    # In production, use key_vault_ref with proper secrets management
    # Data is encrypted at rest using AES-128 Fernet encryption
    api_key_dev = EncryptedCharField(max_length=2048, blank=True, help_text="DEV ONLY: Encrypted API key storage")
    model_name = models.CharField(max_length=128)  # e.g., gpt-4o, claude-3-opus
    endpoint_url = models.URLField(blank=True, null=True)  # For Azure/self-hosted
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)
    max_tokens = models.IntegerField(default=4096)
    temperature = models.FloatField(default=0.7)
    
    class Meta:
        verbose_name = 'AI Model Provider'
        verbose_name_plural = 'AI Model Providers'
        unique_together = ['provider_type', 'model_name']
        indexes = [
            models.Index(fields=['provider_type', 'is_active']),
            models.Index(fields=['is_default']),
        ]
    
    def __str__(self):
        return f"{self.display_name} ({self.model_name})"


class AIAgentType(models.TextChoices):
    AMANI_ASSISTANT = 'amani', 'Ask Amani (General Assistant)'
    PACKAGING_AGENT = 'packaging', 'Packaging Assistant'
    CAB_EVIDENCE = 'cab_evidence', 'CAB Evidence Generator'
    RISK_EXPLAINER = 'risk_explainer', 'Risk Score Explainer'
    DEPLOYMENT_ADVISOR = 'deployment', 'Deployment Advisor'
    COMPLIANCE_ANALYZER = 'compliance', 'Compliance Analyzer'
    INCIDENT_RESPONDER = 'incident', 'Incident Responder'


class AIConversation(TimeStampedModel):
    """
    Tracks all AI conversations for audit trail.
    Immutable once created.
    """
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_conversations')
    agent_type = models.CharField(max_length=32, choices=AIAgentType.choices)
    provider = models.ForeignKey(AIModelProvider, on_delete=models.SET_NULL, null=True, blank=True)
    context_type = models.CharField(max_length=64, blank=True)  # e.g., 'deployment_intent', 'cab_approval'
    context_id = models.CharField(max_length=128, blank=True)   # e.g., deployment intent ID
    title = models.CharField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        verbose_name = 'AI Conversation'
        verbose_name_plural = 'AI Conversations'
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['agent_type', 'is_active']),
            models.Index(fields=['context_type', 'context_id']),
        ]
    
    def __str__(self):
        return f"{self.agent_type} - {self.title or 'Untitled'} ({self.user.username})"


class AIMessage(TimeStampedModel):
    """
    Individual messages in a conversation (immutable audit trail).
    """
    class Role(models.TextChoices):
        USER = 'user', 'User'
        ASSISTANT = 'assistant', 'Assistant'
        SYSTEM = 'system', 'System'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name='messages')
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    token_count = models.IntegerField(default=0)
    model_used = models.CharField(max_length=64, blank=True)
    # For tracking AI-generated recommendations that require human action
    requires_human_action = models.BooleanField(default=False)
    action_taken = models.BooleanField(default=False)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='ai_actions')
    action_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'AI Message'
        verbose_name_plural = 'AI Messages'
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['conversation', 'created_at']),
            models.Index(fields=['requires_human_action', 'action_taken']),
        ]
    
    def __str__(self):
        return f"{self.role} - {self.content[:50]}..."


class AIAgentTask(TimeStampedModel):
    """
    Tracks AI-assisted tasks (packaging, evidence generation, etc.).
    All tasks require human approval before execution.
    """
    class TaskStatus(models.TextChoices):
        PENDING = 'pending', 'Pending'
        IN_PROGRESS = 'in_progress', 'In Progress'
        AWAITING_APPROVAL = 'awaiting_approval', 'Awaiting Human Approval'
        REVISION_REQUESTED = 'revision_requested', 'Revision Requested'
        APPROVED = 'approved', 'Approved'
        REJECTED = 'rejected', 'Rejected'
        EXECUTING = 'executing', 'Executing'
        COMPLETED = 'completed', 'Completed'
        FAILED = 'failed', 'Failed'
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_type = models.CharField(max_length=32, choices=AIAgentType.choices)
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ai_tasks')
    approved_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='approved_ai_tasks')
    conversation = models.ForeignKey(AIConversation, on_delete=models.SET_NULL, null=True, blank=True)
    
    title = models.CharField(max_length=256)
    description = models.TextField()
    task_type = models.CharField(max_length=64)  # e.g., 'generate_evidence_pack', 'analyze_risk'
    input_data = models.JSONField(default=dict)
    output_data = models.JSONField(default=dict)
    
    status = models.CharField(max_length=32, choices=TaskStatus.choices, default=TaskStatus.PENDING)
    
    # Audit linkage
    correlation_id = models.UUIDField(default=uuid.uuid4)
    deployment_intent_id = models.UUIDField(null=True, blank=True)
    evidence_pack_id = models.UUIDField(null=True, blank=True)
    
    class Meta:
        verbose_name = 'AI Agent Task'
        verbose_name_plural = 'AI Agent Tasks'
        indexes = [
            models.Index(fields=['initiated_by', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['agent_type', 'status']),
            models.Index(fields=['correlation_id']),
        ]
    
    def __str__(self):
        return f"{self.agent_type} - {self.title} ({self.status})"

