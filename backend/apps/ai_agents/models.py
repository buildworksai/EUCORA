# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
AI Agents models for EUCORA.

All AI recommendations require human approval before execution.
Immutable audit trail for all AI interactions.
"""
import uuid

from django.contrib.auth.models import User
from django.db import models

from apps.core.encryption import EncryptedCharField
from apps.core.models import TimeStampedModel


class AIModelProvider(TimeStampedModel):
    """
    Model Provider Configuration.
    API keys stored encrypted in vault (referenced by key_vault_ref).
    For development: api_key_dev stores key directly (DO NOT USE IN PRODUCTION).
    """

    class ProviderType(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        ANTHROPIC = "anthropic", "Anthropic"
        GROQ = "groq", "Groq"
        HUGGINGFACE = "huggingface", "HuggingFace"
        AZURE_OPENAI = "azure_openai", "Azure OpenAI"
        GOOGLE_GEMINI = "google_gemini", "Google Gemini"

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
        verbose_name = "AI Model Provider"
        verbose_name_plural = "AI Model Providers"
        unique_together = ["provider_type", "model_name"]
        indexes = [
            models.Index(fields=["provider_type", "is_active"]),
            models.Index(fields=["is_default"]),
        ]

    def __str__(self):
        return f"{self.display_name} ({self.model_name})"


class AIAgentType(models.TextChoices):
    AMANI_ASSISTANT = "amani", "Ask Amani (General Assistant)"
    PACKAGING_AGENT = "packaging", "Packaging Assistant"
    CAB_EVIDENCE = "cab_evidence", "CAB Evidence Generator"
    RISK_EXPLAINER = "risk_explainer", "Risk Score Explainer"
    DEPLOYMENT_ADVISOR = "deployment", "Deployment Advisor"
    COMPLIANCE_ANALYZER = "compliance", "Compliance Analyzer"
    INCIDENT_RESPONDER = "incident", "Incident Responder"


class AIConversation(TimeStampedModel):
    """
    Tracks all AI conversations for audit trail.
    Immutable once created.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_conversations")
    agent_type = models.CharField(max_length=32, choices=AIAgentType.choices)
    provider = models.ForeignKey(AIModelProvider, on_delete=models.SET_NULL, null=True, blank=True)
    context_type = models.CharField(max_length=64, blank=True)  # e.g., 'deployment_intent', 'cab_approval'
    context_id = models.CharField(max_length=128, blank=True)  # e.g., deployment intent ID
    title = models.CharField(max_length=256, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        verbose_name = "AI Conversation"
        verbose_name_plural = "AI Conversations"
        indexes = [
            models.Index(fields=["user", "created_at"]),
            models.Index(fields=["agent_type", "is_active"]),
            models.Index(fields=["context_type", "context_id"]),
        ]

    def __str__(self):
        return f"{self.agent_type} - {self.title or 'Untitled'} ({self.user.username})"


class AIMessage(TimeStampedModel):
    """
    Individual messages in a conversation (immutable audit trail).
    """

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    conversation = models.ForeignKey(AIConversation, on_delete=models.CASCADE, related_name="messages")
    role = models.CharField(max_length=16, choices=Role.choices)
    content = models.TextField()
    token_count = models.IntegerField(default=0)
    model_used = models.CharField(max_length=64, blank=True)
    # For tracking AI-generated recommendations that require human action
    requires_human_action = models.BooleanField(default=False)
    action_taken = models.BooleanField(default=False)
    action_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name="ai_actions")
    action_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "AI Message"
        verbose_name_plural = "AI Messages"
        ordering = ["created_at"]
        indexes = [
            models.Index(fields=["conversation", "created_at"]),
            models.Index(fields=["requires_human_action", "action_taken"]),
        ]

    def __str__(self):
        return f"{self.role} - {self.content[:50]}..."


class AIAgentTask(TimeStampedModel):
    """
    Tracks AI-assisted tasks (packaging, evidence generation, etc.).
    All tasks require human approval before execution.
    """

    class TaskStatus(models.TextChoices):
        PENDING = "pending", "Pending"
        IN_PROGRESS = "in_progress", "In Progress"
        AWAITING_APPROVAL = "awaiting_approval", "Awaiting Human Approval"
        REVISION_REQUESTED = "revision_requested", "Revision Requested"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        EXECUTING = "executing", "Executing"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    agent_type = models.CharField(max_length=32, choices=AIAgentType.choices)
    initiated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ai_tasks")
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_ai_tasks"
    )
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
        verbose_name = "AI Agent Task"
        verbose_name_plural = "AI Agent Tasks"
        indexes = [
            models.Index(fields=["initiated_by", "created_at"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["agent_type", "status"]),
            models.Index(fields=["correlation_id"]),
        ]

    def __str__(self):
        return f"{self.agent_type} - {self.title} ({self.status})"


# =============================================================================
# P7: AI Governance Models (Model Registry, Execution Audit, Drift Detection)
# =============================================================================


class AIModel(TimeStampedModel):
    """
    Registry of AI models with lineage tracking.

    All models must be registered before use. Tracks versioning,
    validation status, and deployment history for governance.
    """

    class ModelStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        VALIDATED = "validated", "Validated"
        DEPLOYED = "deployed", "Deployed"
        DEPRECATED = "deprecated", "Deprecated"
        RETIRED = "retired", "Retired"

    class RiskLevel(models.TextChoices):
        R1_LOW = "R1", "R1 - Low (Auto-execute allowed)"
        R2_MEDIUM = "R2", "R2 - Medium (Policy-dependent approval)"
        R3_HIGH = "R3", "R3 - High (Mandatory human approval)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model_id = models.CharField(max_length=100, unique=True, db_index=True)
    model_type = models.CharField(max_length=50)  # classification, recommendation, extraction, etc.
    version = models.CharField(max_length=50)
    display_name = models.CharField(max_length=256)
    description = models.TextField(blank=True)

    # Status and lifecycle
    status = models.CharField(max_length=20, choices=ModelStatus.choices, default=ModelStatus.DRAFT)
    risk_level = models.CharField(max_length=10, choices=RiskLevel.choices, default=RiskLevel.R2_MEDIUM)

    # Lineage tracking
    dataset_version = models.CharField(max_length=100, blank=True)
    training_params = models.JSONField(default=dict, blank=True)
    validation_report = models.JSONField(default=dict, blank=True)
    parent_model = models.ForeignKey(
        "self", on_delete=models.SET_NULL, null=True, blank=True, related_name="derived_models"
    )

    # Deployment tracking
    deployed_at = models.DateTimeField(null=True, blank=True)
    deployed_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="deployed_ai_models"
    )
    deployment_notes = models.TextField(blank=True)

    # Performance baselines
    baseline_accuracy = models.FloatField(null=True, blank=True)
    baseline_confidence_mean = models.FloatField(null=True, blank=True)
    baseline_latency_ms = models.FloatField(null=True, blank=True)

    # Audit
    created_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="created_ai_models"
    )

    class Meta:
        verbose_name = "AI Model"
        verbose_name_plural = "AI Models"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["model_id", "version"]),
            models.Index(fields=["status", "risk_level"]),
            models.Index(fields=["model_type", "status"]),
        ]

    def __str__(self):
        return f"{self.display_name} v{self.version} ({self.status})"


class AgentExecution(TimeStampedModel):
    """
    Audit trail for agent executions.

    Every AI agent execution is logged here with full input/output
    capture for governance, debugging, and drift detection.
    """

    class ApprovalStatus(models.TextChoices):
        NOT_REQUIRED = "not_required", "Not Required"
        PENDING = "pending", "Pending Approval"
        APPROVED = "approved", "Approved"
        REJECTED = "rejected", "Rejected"
        AUTO_APPROVED = "auto_approved", "Auto-Approved (R1)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    correlation_id = models.UUIDField(default=uuid.uuid4, db_index=True)

    # Agent and model
    agent_type = models.CharField(max_length=100, db_index=True)
    model = models.ForeignKey(AIModel, on_delete=models.SET_NULL, null=True, blank=True, related_name="executions")

    # Input tracking (hashed for comparison, summary for audit)
    input_hash = models.CharField(max_length=64, db_index=True)  # SHA-256 of input
    input_summary = models.JSONField(default=dict)  # Sanitized summary (no PII)

    # Output tracking
    output = models.JSONField(default=dict)
    confidence = models.FloatField(null=True, blank=True)
    latency_ms = models.FloatField(null=True, blank=True)

    # Risk and approval
    risk_level = models.CharField(max_length=10, default="R2")
    approval_required = models.BooleanField(default=False)
    approval_status = models.CharField(
        max_length=20, choices=ApprovalStatus.choices, default=ApprovalStatus.NOT_REQUIRED
    )
    approved_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="approved_executions"
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    rejection_reason = models.TextField(blank=True)

    # Execution status
    executed = models.BooleanField(default=False)
    executed_at = models.DateTimeField(null=True, blank=True)
    execution_result = models.JSONField(null=True, blank=True)
    execution_error = models.TextField(blank=True)

    # User context
    initiated_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="agent_executions"
    )

    class Meta:
        verbose_name = "Agent Execution"
        verbose_name_plural = "Agent Executions"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["agent_type", "created_at"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["approval_status", "created_at"]),
            models.Index(fields=["executed", "created_at"]),
            models.Index(fields=["input_hash"]),
        ]

    def __str__(self):
        return f"{self.agent_type} - {self.correlation_id} ({self.approval_status})"


class ModelDriftMetric(TimeStampedModel):
    """
    Tracks model performance drift over time.

    Used by the drift detection pipeline to identify when models
    are degrading and may need retraining or replacement.
    """

    class MetricType(models.TextChoices):
        ACCURACY = "accuracy", "Accuracy"
        CONFIDENCE_MEAN = "confidence_mean", "Mean Confidence"
        CONFIDENCE_STD = "confidence_std", "Confidence Std Dev"
        OVERRIDE_RATE = "override_rate", "Human Override Rate"
        LATENCY_P50 = "latency_p50", "Latency P50"
        LATENCY_P95 = "latency_p95", "Latency P95"
        ERROR_RATE = "error_rate", "Error Rate"
        INPUT_DRIFT = "input_drift", "Input Distribution Drift"
        OUTPUT_DRIFT = "output_drift", "Output Distribution Drift"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    model = models.ForeignKey(AIModel, on_delete=models.CASCADE, related_name="drift_metrics")

    metric_type = models.CharField(max_length=50, choices=MetricType.choices)
    value = models.FloatField()
    threshold = models.FloatField()  # Alert threshold for this metric
    baseline_value = models.FloatField(null=True, blank=True)

    # Alert status
    is_alert = models.BooleanField(default=False)
    alert_acknowledged = models.BooleanField(default=False)
    alert_acknowledged_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True, related_name="acknowledged_drift_alerts"
    )
    alert_acknowledged_at = models.DateTimeField(null=True, blank=True)

    # Time window
    window_start = models.DateTimeField()
    window_end = models.DateTimeField()
    sample_count = models.IntegerField(default=0)

    recorded_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Model Drift Metric"
        verbose_name_plural = "Model Drift Metrics"
        ordering = ["-recorded_at"]
        indexes = [
            models.Index(fields=["model", "metric_type", "recorded_at"]),
            models.Index(fields=["is_alert", "alert_acknowledged"]),
            models.Index(fields=["recorded_at"]),
        ]

    def __str__(self):
        alert_str = " [ALERT]" if self.is_alert else ""
        return f"{self.model.model_id} - {self.metric_type}: {self.value}{alert_str}"
