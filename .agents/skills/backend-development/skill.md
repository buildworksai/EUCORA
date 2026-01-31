---
name: backend-development
description: Full-stack backend development with Python, Django, PostgreSQL, migrations, PowerShell automation, and RAG/vector storage patterns. Use when building backend APIs, database models, migrations, automation scripts, or AI knowledge retrieval features.
status: ✅ Working
last-validated: 2026-01-30
---

# Backend Development Skill

Complete development patterns for Python/Django backends with PostgreSQL, PowerShell automation, and RAG/vector storage.

---

## Quick Reference

| Topic | Key Points |
|-------|------------|
| Python | Type hints required, Black formatting, docstrings mandatory |
| Django | Inherit `TimeStampedModel` + `CorrelationIdModel`, use `DemoQuerySet` |
| Migrations | Never modify existing, create new migrations for changes |
| PostgreSQL | Use indexes, constraints, `select_related()` for performance |
| PowerShell | `Set-StrictMode -Version Latest`, structured logging, correlation IDs |
| RAG/Vectors | pgvector extension, HNSW indexing, chunking + embeddings |

---

## Python Standards

### File Header Template

```python
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI

"""
Module docstring describing purpose.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from django.http import HttpRequest
```

### Type Hints (MANDATORY)

```python
# ✅ CORRECT - All functions have type hints
def calculate_risk_score(
    factors: list[RiskFactor],
    weights: dict[str, float],
) -> float:
    """Calculate weighted risk score from factors."""
    return sum(f.value * weights.get(f.name, 0.0) for f in factors)

# ❌ FORBIDDEN - Missing type hints
def calculate_risk_score(factors, weights):
    return sum(f.value * weights.get(f.name, 0.0) for f in factors)
```

### Common Patterns

```python
# Constants at module level
MAX_RETRIES = 3
DEFAULT_TIMEOUT = 30

# Use dataclasses for data containers
from dataclasses import dataclass

@dataclass
class RiskAssessment:
    score: float
    factors: list[str]
    threshold: float = 50.0

    @property
    def requires_cab(self) -> bool:
        return self.score > self.threshold

# Use enums for choices
from enum import Enum

class DeploymentStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
```

For detailed patterns, see [python-patterns.md](python-patterns.md).

---

## Django Patterns

### Model Inheritance (MANDATORY)

All models MUST inherit from base classes in `apps/core/models.py`:

```python
from apps.core.models import TimeStampedModel, CorrelationIdModel, DemoQuerySet

class Deployment(TimeStampedModel, CorrelationIdModel):
    """Deployment record with audit trail."""

    name = models.CharField(max_length=255)
    status = models.CharField(max_length=32, choices=DeploymentStatus.choices)
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)
    is_demo = models.BooleanField(default=False, db_index=True)

    objects = DemoQuerySet.as_manager()

    class Meta:
        indexes = [
            models.Index(fields=["status", "created_at"]),
        ]
```

### ViewSet Pattern

```python
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

class DeploymentViewSet(viewsets.ModelViewSet):
    queryset = Deployment.objects.select_related("application", "owner")
    permission_classes = [IsAuthenticated]

    def get_serializer_class(self):
        if self.action == "list":
            return DeploymentListSerializer
        if self.action == "create":
            return DeploymentCreateSerializer
        return DeploymentSerializer

    def get_queryset(self):
        qs = super().get_queryset()
        # Apply demo filter
        qs = apply_demo_filter(qs, self.request)
        # Apply query param filters
        status = self.request.query_params.get("status")
        if status:
            qs = qs.filter(status=status)
        return qs
```

### Function-Based Views

```python
from django.db import transaction
from rest_framework.decorators import api_view, permission_classes, throttle_classes

@api_view(["POST"])
@throttle_classes([StrictRateThrottle])
@permission_classes([IsAuthenticated])
@transaction.atomic
def approve_deployment(request: HttpRequest, correlation_id: str) -> Response:
    """Approve a pending deployment."""
    deployment = get_object_or_404(
        apply_demo_filter(Deployment.objects.all(), request),
        correlation_id=correlation_id,
    )
    deployment.status = DeploymentStatus.APPROVED
    deployment.approved_by = request.user
    deployment.approved_at = timezone.now()
    deployment.save()

    return Response(DeploymentSerializer(deployment).data)
```

For complete Django patterns, see [django-patterns.md](django-patterns.md).

---

## Database Migrations

### Critical Rules

| Rule | Action |
|------|--------|
| Never modify existing migrations | Create new migration for changes |
| Always specify dependencies | List all required app migrations |
| Add indexes in migrations | Include in `operations` list |
| Test migrations both ways | Run `migrate` and `migrate --reverse` |

### Migration Commands

```bash
# Create migration after model changes
python manage.py makemigrations app_name

# Show migration SQL without applying
python manage.py sqlmigrate app_name 0002

# Apply migrations
python manage.py migrate

# Reverse to specific migration
python manage.py migrate app_name 0001
```

### Migration Template

```python
# migrations/0002_add_risk_score.py
from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ("deployments", "0001_initial"),
    ]

    operations = [
        migrations.AddField(
            model_name="deployment",
            name="risk_score",
            field=models.DecimalField(
                max_digits=5,
                decimal_places=2,
                default=0.0,
            ),
        ),
        migrations.AddIndex(
            model_name="deployment",
            index=models.Index(
                fields=["risk_score"],
                name="depl_risk_score_idx",
            ),
        ),
    ]
```

For migration patterns, see [migration-patterns.md](migration-patterns.md).

---

## PostgreSQL Patterns

### Query Optimization

```python
# ✅ Use select_related for ForeignKey
qs = Deployment.objects.select_related("application", "owner")

# ✅ Use prefetch_related for ManyToMany/reverse FK
qs = Application.objects.prefetch_related("versions", "deployments")

# ✅ Use only() to limit fields
qs = Deployment.objects.only("id", "name", "status")

# ✅ Use values() for aggregations
from django.db.models import Count, Avg

stats = Deployment.objects.values("status").annotate(
    count=Count("id"),
    avg_risk=Avg("risk_score"),
)
```

### Index Strategy

```python
class Meta:
    indexes = [
        # Single column for equality lookups
        models.Index(fields=["status"]),
        # Composite for common query patterns
        models.Index(fields=["status", "created_at"]),
        # Partial index for specific conditions
        models.Index(
            fields=["risk_score"],
            condition=models.Q(status="pending"),
            name="pending_risk_idx",
        ),
    ]
```

### Constraints

```python
class Meta:
    constraints = [
        models.CheckConstraint(
            check=models.Q(risk_score__gte=0) & models.Q(risk_score__lte=100),
            name="valid_risk_score",
        ),
        models.UniqueConstraint(
            fields=["application", "version"],
            name="unique_app_version",
        ),
    ]
```

---

## PowerShell Standards

### Script Header Template

```powershell
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
<#
.SYNOPSIS
    Brief description of script purpose.
.DESCRIPTION
    Detailed description with use cases.
.PARAMETER CorrelationId
    Unique ID for audit trail (required for all operations).
.EXAMPLE
    .\Deploy-Package.ps1 -PackagePath "C:\packages\app.intunewin" -CorrelationId "abc-123"
#>
[CmdletBinding(SupportsShouldProcess)]
param(
    [Parameter(Mandatory = $true)]
    [ValidateNotNullOrEmpty()]
    [string]$PackagePath,

    [Parameter(Mandatory = $true)]
    [ValidatePattern('^[a-f0-9-]{36}$')]
    [string]$CorrelationId
)

Set-StrictMode -Version Latest
$ErrorActionPreference = 'Stop'
```

### Structured Logging

```powershell
function Write-StructuredLog {
    [CmdletBinding()]
    param(
        [Parameter(Mandatory)]
        [string]$Message,

        [ValidateSet('Debug', 'Info', 'Warning', 'Error', 'Critical')]
        [string]$Level = 'Info',

        [string]$CorrelationId,

        [hashtable]$Metadata = @{}
    )

    $logEntry = @{
        timestamp = (Get-Date -Format "o")
        level = $Level
        message = $Message
        correlation_id = $CorrelationId
        metadata = $Metadata
    } | ConvertTo-Json -Compress

    Write-Host $logEntry
}
```

### Error Handling with Classification

```powershell
try {
    $result = Invoke-ConnectorRequest -Uri $uri -Method "POST" -Body $body
}
catch {
    $errorClass = switch -Regex ($_.Exception.Message) {
        '429|503|504' { 'TRANSIENT' }
        '401|403' { 'POLICY_VIOLATION' }
        default { 'PERMANENT' }
    }

    Write-StructuredLog -Message "Request failed" -Level Error -CorrelationId $CorrelationId -Metadata @{
        error_class = $errorClass
        error_message = $_.Exception.Message
    }

    if ($errorClass -eq 'TRANSIENT') {
        # Retry with backoff
        Invoke-RetryWithBackoff -ScriptBlock { Invoke-ConnectorRequest @params }
    }
    else {
        throw
    }
}
```

For complete PowerShell patterns, see [powershell-patterns.md](powershell-patterns.md).

---

## RAG & Vector Storage

### Architecture Overview

```
┌────────────────────────────────────────────────────┐
│                  AI Agents                          │
└───────────────────────┬────────────────────────────┘
                        ▼
┌────────────────────────────────────────────────────┐
│           Knowledge Retrieval Service               │
│  ┌─────────────┐ ┌─────────────┐ ┌──────────────┐  │
│  │   Query     │ │  Embedding  │ │  Reranking   │  │
│  │   Parser    │ │  Generator  │ │  (optional)  │  │
│  └─────────────┘ └─────────────┘ └──────────────┘  │
└───────────────────────┬────────────────────────────┘
                        ▼
┌────────────────────────────────────────────────────┐
│            PostgreSQL + pgvector                    │
│  ┌──────────────────────────────────────────────┐  │
│  │               knowledge_vectors               │  │
│  │  id | source_type | content | embedding      │  │
│  └──────────────────────────────────────────────┘  │
└────────────────────────────────────────────────────┘
```

### Vector Model (pgvector)

```python
from pgvector.django import VectorField, HnswIndex

class KnowledgeVector(TimeStampedModel, CorrelationIdModel):
    """Vector embeddings for knowledge retrieval."""

    class SourceType(models.TextChoices):
        POLICY_DOCUMENT = "policy_document"
        DEPLOYMENT = "deployment"
        CAB_DECISION = "cab_decision"
        INCIDENT = "incident"

    source_type = models.CharField(max_length=64, choices=SourceType.choices)
    source_id = models.UUIDField()
    content = models.TextField()
    content_hash = models.CharField(max_length=64, db_index=True)

    # Vector embedding (1536 dims for OpenAI, adjust per model)
    embedding = VectorField(dimensions=1536)
    embedding_model = models.CharField(max_length=64)

    # Metadata for filtering
    category = models.CharField(max_length=64, blank=True)
    tags = models.JSONField(default=list)

    class Meta:
        indexes = [
            HnswIndex(
                name='knowledge_hnsw_idx',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
        ]
```

### Embedding Provider Interface

```python
from abc import ABC, abstractmethod

class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> list[float]:
        """Generate embedding for text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: list[str]) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        pass
```

### Semantic Search

```python
from pgvector.django import CosineDistance

async def semantic_search(
    query: str,
    source_types: list[str] | None = None,
    top_k: int = 10,
    min_similarity: float = 0.7,
) -> list[dict]:
    """Search knowledge base by semantic similarity."""

    # Generate query embedding
    embedding = await embedding_service.embed(query)

    # Build queryset with filters
    qs = KnowledgeVector.objects.all()
    if source_types:
        qs = qs.filter(source_type__in=source_types)

    # Vector similarity search
    results = await qs.annotate(
        similarity=1 - CosineDistance('embedding', embedding)
    ).filter(
        similarity__gte=min_similarity
    ).order_by('-similarity')[:top_k].aall()

    return [
        {"content": r.content, "similarity": r.similarity, "source": r.source_type}
        for r in results
    ]
```

For complete RAG patterns, see [rag-patterns.md](rag-patterns.md).

---

## Checklists

### Before Writing Code

```
☐ Read relevant model files in apps/{app}/models.py
☐ Check if abstract base models exist (TimeStampedModel, CorrelationIdModel)
☐ Verify correlation_id pattern is followed
☐ Check for existing serializers to extend
```

### After Writing Code

```
☐ Run type checker: mypy apps/
☐ Run linter: flake8 apps/
☐ Run formatter: black apps/
☐ Run tests: pytest --cov
☐ Check migrations: python manage.py makemigrations --check
```

### PowerShell Scripts

```
☐ Includes SPDX header
☐ Uses Set-StrictMode -Version Latest
☐ Has correlation ID parameter
☐ Uses structured logging
☐ Classifies errors (TRANSIENT/PERMANENT/POLICY_VIOLATION)
```

---

## Anti-Patterns to Avoid

| ❌ FORBIDDEN | ✅ CORRECT |
|--------------|------------|
| Missing type hints | All functions have type hints |
| Modifying existing migrations | Create new migration for changes |
| Hardcoded credentials | Use vault/environment variables |
| Missing correlation IDs | All audit events include correlation_id |
| Raw SQL without parameterization | Use Django ORM or parameterized queries |
| `any` type in TypeScript | Use explicit types |
| Skipping SBOM/vuln scans | All artifacts scanned before publish |

---

## Additional Resources

- [python-patterns.md](python-patterns.md) - Advanced Python patterns
- [django-patterns.md](django-patterns.md) - Complete Django guide
- [migration-patterns.md](migration-patterns.md) - Migration strategies
- [powershell-patterns.md](powershell-patterns.md) - PowerShell automation
- [rag-patterns.md](rag-patterns.md) - RAG implementation guide
