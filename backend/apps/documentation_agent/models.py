# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Documentation Agent models for E12 enhancement.

Implements code repository configuration, analysis tracking, module documentation,
and generated document management.
"""
import uuid

from django.conf import settings
from django.db import models

from apps.core.models import CorrelationIdModel, TimeStampedModel


class CodeRepository(TimeStampedModel):
    """
    Configured code repositories for documentation generation.

    Supports GitHub, GitLab, and local filesystem repositories.
    """

    class RepoType(models.TextChoices):
        GITHUB = "github", "GitHub"
        GITLAB = "gitlab", "GitLab"
        LOCAL = "local", "Local Filesystem"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Display name for this repository")
    repo_type = models.CharField(max_length=20, choices=RepoType.choices, default=RepoType.LOCAL)
    url = models.URLField(null=True, blank=True, help_text="Repository URL (for GitHub/GitLab)")
    local_path = models.CharField(max_length=500, null=True, blank=True, help_text="Local filesystem path")
    default_branch = models.CharField(max_length=100, default="main")
    auth_config = models.JSONField(
        default=dict,
        null=True,
        blank=True,
        help_text="Authentication configuration (token, credentials)",
    )
    last_analyzed = models.DateTimeField(null=True, blank=True)
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Code Repository"
        verbose_name_plural = "Code Repositories"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["is_active", "repo_type"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.repo_type})"


class CodeAnalysis(TimeStampedModel, CorrelationIdModel):
    """
    Analysis run on a repository.

    Tracks code analysis execution with correlation ID for audit trail.
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        RUNNING = "running", "Running"
        COMPLETED = "completed", "Completed"
        FAILED = "failed", "Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    repository = models.ForeignKey(CodeRepository, on_delete=models.CASCADE, related_name="analyses")
    commit_sha = models.CharField(max_length=40, blank=True, help_text="Git commit SHA")
    branch = models.CharField(max_length=100, default="main")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    started_at = models.DateTimeField(null=True, blank=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    summary = models.JSONField(
        null=True,
        blank=True,
        default=dict,
        help_text="Analysis summary: modules, classes, functions counts",
    )
    errors = models.JSONField(default=list, blank=True, help_text="Analysis errors")

    class Meta:
        verbose_name = "Code Analysis"
        verbose_name_plural = "Code Analyses"
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["repository", "status"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["status", "started_at"]),
        ]

    def __str__(self) -> str:
        return f"{self.repository.name} - {self.status} ({self.branch})"


class DocumentedModule(TimeStampedModel):
    """
    Analyzed and documented code module.

    Stores extracted information about modules, classes, functions, etc.
    """

    class ModuleType(models.TextChoices):
        PACKAGE = "package", "Package/Module"
        CLASS = "class", "Class"
        FUNCTION = "function", "Function/Method"
        ENDPOINT = "endpoint", "API Endpoint"
        COMPONENT = "component", "React Component"
        HOOK = "hook", "React Hook"
        TYPE = "type", "TypeScript Type"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(CodeAnalysis, on_delete=models.CASCADE, related_name="modules")
    module_path = models.CharField(max_length=500, help_text="File path relative to repo root")
    module_type = models.CharField(max_length=50, choices=ModuleType.choices)
    name = models.CharField(max_length=255, help_text="Module/class/function name")
    docstring = models.TextField(null=True, blank=True, help_text="Extracted docstring")
    generated_doc = models.TextField(null=True, blank=True, help_text="Generated documentation")
    signature = models.TextField(null=True, blank=True, help_text="Function/class signature")
    dependencies = models.JSONField(default=list, blank=True, help_text="List of dependencies")
    metadata = models.JSONField(default=dict, blank=True, help_text="Additional metadata")

    class Meta:
        verbose_name = "Documented Module"
        verbose_name_plural = "Documented Modules"
        ordering = ["module_path", "name"]
        indexes = [
            models.Index(fields=["analysis", "module_type"]),
            models.Index(fields=["module_path"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.module_type})"


class GeneratedDocument(TimeStampedModel, CorrelationIdModel):
    """
    Generated documentation artifacts.

    Tracks generated documentation with correlation ID for audit trail.
    """

    class DocType(models.TextChoices):
        API = "api", "API Documentation"
        README = "readme", "README"
        ARCHITECTURE = "architecture", "Architecture Diagram"
        RUNBOOK = "runbook", "Runbook"
        ADR = "adr", "Architecture Decision Record"
        TEST = "test", "Test Documentation"

    class DocFormat(models.TextChoices):
        MARKDOWN = "markdown", "Markdown"
        OPENAPI = "openapi", "OpenAPI/Swagger"
        MERMAID = "mermaid", "Mermaid Diagram"

    class DocStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        REVIEW = "review", "Under Review"
        PUBLISHED = "published", "Published"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    analysis = models.ForeignKey(CodeAnalysis, on_delete=models.CASCADE, related_name="documents")
    doc_type = models.CharField(max_length=50, choices=DocType.choices)
    title = models.CharField(max_length=255)
    content = models.TextField(help_text="Document content")
    format = models.CharField(max_length=20, choices=DocFormat.choices, default=DocFormat.MARKDOWN)
    target_path = models.CharField(max_length=500, null=True, blank=True, help_text="Target file path for publishing")
    status = models.CharField(max_length=20, choices=DocStatus.choices, default=DocStatus.DRAFT)
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name="reviewed_documents",
    )
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "Generated Document"
        verbose_name_plural = "Generated Documents"
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["analysis", "doc_type"]),
            models.Index(fields=["correlation_id"]),
            models.Index(fields=["status", "doc_type"]),
        ]

    def __str__(self) -> str:
        return f"{self.title} ({self.doc_type})"


class DocumentationTemplate(TimeStampedModel):
    """
    Templates for documentation generation.

    Stores reusable templates for different document types.
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=255, help_text="Template name")
    doc_type = models.CharField(
        max_length=50,
        choices=GeneratedDocument.DocType.choices,
        help_text="Document type this template applies to",
    )
    template_content = models.TextField(help_text="Template content with variable placeholders")
    variables = models.JSONField(default=list, blank=True, help_text="List of available variables")
    is_active = models.BooleanField(default=True, db_index=True)

    class Meta:
        verbose_name = "Documentation Template"
        verbose_name_plural = "Documentation Templates"
        ordering = ["doc_type", "name"]
        indexes = [
            models.Index(fields=["doc_type", "is_active"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self) -> str:
        return f"{self.name} ({self.doc_type})"
