# E7: Vector Storage (pgvector) — AI Knowledge Base

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Version**: 1.0
**Date**: 2026-01-30
**Status**: Draft for Implementation
**Priority**: P1-Critical
**Dependencies**: E2 (Storage Configuration)

---

## Overview

Implement vector storage using PostgreSQL's pgvector extension to power AI agent knowledge retrieval. This enables semantic search across policy documents, historical deployments, and operational knowledge with configurable embedding models (OpenAI, Cohere, or local models).

---

## Requirements

### Functional Requirements

1. **Vector Storage**
   - PostgreSQL with pgvector extension
   - Configurable embedding dimensions (384, 768, 1536, 3072)
   - HNSW indexing for fast similarity search
   - Metadata filtering combined with vector search

2. **Embedding Models**
   - OpenAI text-embedding-3-small/large
   - Cohere embed-v3
   - Local models (sentence-transformers)
   - Configurable per deployment

3. **Knowledge Sources**
   - Policy documents (from E1)
   - Deployment history and outcomes
   - CAB decisions and rationale
   - Incident reports and resolutions
   - Operational runbooks

4. **Retrieval API**
   - Semantic similarity search
   - Hybrid search (vector + keyword)
   - Filtered search by category/source
   - Reranking for relevance

---

## Architecture

### Component Diagram

```
┌─────────────────────────────────────────────────────────────────┐
│                        AI Agents                                 │
│   (Packaging, CAB Evidence, Risk Explainer, Deployment, etc.)   │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    Knowledge Retrieval Service                   │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │   Query     │  │  Embedding  │  │    Reranking            │  │
│  │   Parser    │  │  Generator  │  │    (optional)           │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└────────────────────────────┬────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector                         │
│  ┌─────────────────────────────────────────────────────────────┐│
│  │                    knowledge_vectors                         ││
│  │  id | source_type | source_id | content | embedding | meta  ││
│  └─────────────────────────────────────────────────────────────┘│
│  ┌─────────────┐  ┌─────────────────────────────────────────┐   │
│  │ HNSW Index  │  │        Metadata Indexes                 │   │
│  └─────────────┘  └─────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                             ▲
                             │
┌─────────────────────────────────────────────────────────────────┐
│                    Embedding Pipeline                            │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────────────────┐  │
│  │  Chunking   │  │  Embedding  │  │    Storage              │  │
│  │  Service    │  │  Provider   │  │    Writer               │  │
│  └─────────────┘  └─────────────┘  └─────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
```

---

## Data Model

### Database Schema

```sql
-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Embedding configuration table
CREATE TABLE embedding_config (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    provider VARCHAR(32) NOT NULL,  -- openai, cohere, local
    model_name VARCHAR(128) NOT NULL,
    dimensions INTEGER NOT NULL,
    is_active BOOLEAN DEFAULT TRUE,
    is_default BOOLEAN DEFAULT FALSE,
    api_endpoint VARCHAR(512),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Knowledge vectors table
CREATE TABLE knowledge_vectors (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Source identification
    source_type VARCHAR(64) NOT NULL,  -- policy_document, deployment, cab_decision, incident, runbook
    source_id UUID NOT NULL,
    source_chunk_index INTEGER DEFAULT 0,

    -- Content
    content TEXT NOT NULL,
    content_hash VARCHAR(64) NOT NULL,  -- SHA-256 for deduplication

    -- Vector embedding
    embedding vector(1536),  -- Adjust dimension based on model
    embedding_model VARCHAR(64) NOT NULL,

    -- Metadata for filtering
    category VARCHAR(64),
    tags TEXT[],
    application_id UUID,
    created_by UUID,

    -- Timestamps
    source_created_at TIMESTAMPTZ,
    embedded_at TIMESTAMPTZ DEFAULT NOW(),

    -- Correlation
    correlation_id UUID
);

-- HNSW index for fast similarity search
CREATE INDEX knowledge_vectors_embedding_idx
ON knowledge_vectors
USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Metadata indexes
CREATE INDEX knowledge_vectors_source_idx ON knowledge_vectors(source_type, source_id);
CREATE INDEX knowledge_vectors_category_idx ON knowledge_vectors(category);
CREATE INDEX knowledge_vectors_application_idx ON knowledge_vectors(application_id);
CREATE INDEX knowledge_vectors_content_hash_idx ON knowledge_vectors(content_hash);
```

### Django Models

```python
# backend/apps/knowledge/models.py

from pgvector.django import VectorField, HnswIndex

class EmbeddingConfig(TimeStampedModel):
    """Configuration for embedding providers."""

    class Provider(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        COHERE = "cohere", "Cohere"
        LOCAL = "local", "Local (Sentence Transformers)"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    provider = models.CharField(max_length=32, choices=Provider.choices)
    model_name = models.CharField(max_length=128)
    dimensions = models.IntegerField()

    # API Configuration
    api_key = EncryptedCharField(max_length=256, blank=True)
    api_endpoint = models.URLField(blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_embedding_config'
            )
        ]


class KnowledgeVector(TimeStampedModel):
    """Vector embeddings for knowledge retrieval."""

    class SourceType(models.TextChoices):
        POLICY_DOCUMENT = "policy_document", "Policy Document"
        DEPLOYMENT = "deployment", "Deployment Record"
        CAB_DECISION = "cab_decision", "CAB Decision"
        INCIDENT = "incident", "Incident Report"
        RUNBOOK = "runbook", "Operational Runbook"
        APPLICATION = "application", "Application Metadata"
        VULNERABILITY = "vulnerability", "Vulnerability Record"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Source
    source_type = models.CharField(max_length=64, choices=SourceType.choices)
    source_id = models.UUIDField()
    source_chunk_index = models.IntegerField(default=0)

    # Content
    content = models.TextField()
    content_hash = models.CharField(max_length=64, db_index=True)

    # Vector
    embedding = VectorField(dimensions=1536)  # Default OpenAI dimensions
    embedding_model = models.CharField(max_length=64)

    # Metadata
    category = models.CharField(max_length=64, blank=True)
    tags = models.JSONField(default=list)
    application = models.ForeignKey(
        'application_portfolio.Application',
        on_delete=models.SET_NULL,
        null=True, blank=True
    )

    # Audit
    source_created_at = models.DateTimeField(null=True, blank=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        indexes = [
            HnswIndex(
                name='knowledge_embedding_hnsw_idx',
                fields=['embedding'],
                m=16,
                ef_construction=64,
                opclasses=['vector_cosine_ops'],
            ),
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['category']),
            models.Index(fields=['application']),
        ]
```

---

## Embedding Service

### Provider Interface

```python
# backend/apps/knowledge/embeddings/base.py

from abc import ABC, abstractmethod
from typing import List

class EmbeddingProvider(ABC):
    """Base class for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        pass

    @abstractmethod
    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        pass

    @property
    @abstractmethod
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        pass

    @property
    @abstractmethod
    def model_name(self) -> str:
        """Return model name."""
        pass
```

### OpenAI Provider

```python
# backend/apps/knowledge/embeddings/openai.py

import openai
from .base import EmbeddingProvider

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(self, api_key: str, model: str = "text-embedding-3-small"):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimensions = self.MODEL_DIMENSIONS.get(model, 1536)

    async def embed(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            input=text,
            model=self._model,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # OpenAI supports batch embedding
        response = await self.client.embeddings.create(
            input=texts,
            model=self._model,
        )
        return [item.embedding for item in response.data]

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model
```

### Cohere Provider

```python
# backend/apps/knowledge/embeddings/cohere.py

import cohere
from .base import EmbeddingProvider

class CohereEmbeddingProvider(EmbeddingProvider):
    """Cohere embedding provider."""

    def __init__(self, api_key: str, model: str = "embed-english-v3.0"):
        self.client = cohere.AsyncClient(api_key=api_key)
        self._model = model
        self._dimensions = 1024  # Cohere v3 default

    async def embed(self, text: str) -> List[float]:
        response = await self.client.embed(
            texts=[text],
            model=self._model,
            input_type="search_document",
        )
        return response.embeddings[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        response = await self.client.embed(
            texts=texts,
            model=self._model,
            input_type="search_document",
        )
        return response.embeddings
```

### Local Provider (Sentence Transformers)

```python
# backend/apps/knowledge/embeddings/local.py

from sentence_transformers import SentenceTransformer
from .base import EmbeddingProvider

class LocalEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformers provider."""

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        self._model_name = model
        self._model = SentenceTransformer(model)
        self._dimensions = self._model.get_sentence_embedding_dimension()

    async def embed(self, text: str) -> List[float]:
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()
```

### Embedding Service Factory

```python
# backend/apps/knowledge/embeddings/factory.py

class EmbeddingService:
    """Factory and manager for embedding providers."""

    _instance: 'EmbeddingService' = None

    @classmethod
    def get_instance(cls) -> 'EmbeddingService':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._providers: Dict[str, EmbeddingProvider] = {}
        self._default_provider: EmbeddingProvider = None

    async def initialize(self):
        """Load embedding configurations from database."""
        configs = await EmbeddingConfig.objects.filter(is_active=True).aall()

        for config in configs:
            provider = self._create_provider(config)
            self._providers[str(config.id)] = provider

            if config.is_default:
                self._default_provider = provider

    def _create_provider(self, config: EmbeddingConfig) -> EmbeddingProvider:
        if config.provider == EmbeddingConfig.Provider.OPENAI:
            return OpenAIEmbeddingProvider(config.api_key, config.model_name)
        elif config.provider == EmbeddingConfig.Provider.COHERE:
            return CohereEmbeddingProvider(config.api_key, config.model_name)
        elif config.provider == EmbeddingConfig.Provider.LOCAL:
            return LocalEmbeddingProvider(config.model_name)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    async def embed(self, text: str, provider_id: str = None) -> List[float]:
        provider = self._get_provider(provider_id)
        return await provider.embed(text)

    async def embed_batch(self, texts: List[str], provider_id: str = None) -> List[List[float]]:
        provider = self._get_provider(provider_id)
        return await provider.embed_batch(texts)
```

---

## Knowledge Indexing

### Indexing Pipeline

```python
# backend/apps/knowledge/indexing/pipeline.py

class KnowledgeIndexingPipeline:
    """Pipeline for indexing content into vector storage."""

    def __init__(
        self,
        embedding_service: EmbeddingService,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
    ):
        self.embedding_service = embedding_service
        self.chunker = SemanticChunker(chunk_size, chunk_overlap)

    async def index_document(
        self,
        document: PolicyDocument,
    ) -> int:
        """Index a policy document."""
        # 1. Extract text
        text = await extract_text(document)

        # 2. Chunk content
        chunks = self.chunker.chunk(text)

        # 3. Generate embeddings
        embeddings = await self.embedding_service.embed_batch(
            [chunk.content for chunk in chunks]
        )

        # 4. Store vectors
        vectors = []
        for i, (chunk, embedding) in enumerate(zip(chunks, embeddings)):
            vectors.append(KnowledgeVector(
                source_type=KnowledgeVector.SourceType.POLICY_DOCUMENT,
                source_id=document.id,
                source_chunk_index=i,
                content=chunk.content,
                content_hash=hash_content(chunk.content),
                embedding=embedding,
                embedding_model=self.embedding_service.default_model_name,
                category=document.category.category_type,
                tags=document.tags,
                source_created_at=document.created_at,
            ))

        await KnowledgeVector.objects.abulk_create(vectors)
        return len(vectors)

    async def index_deployment(self, deployment: DeploymentIntent) -> int:
        """Index deployment record for historical knowledge."""
        # Create searchable summary
        content = f"""
        Deployment: {deployment.application.name} v{deployment.version}
        Status: {deployment.status}
        Risk Score: {deployment.risk_score}
        Target Ring: {deployment.target_ring}
        Success Rate: {deployment.success_rate}%

        Summary: {deployment.summary}
        Outcome: {deployment.outcome}
        Lessons Learned: {deployment.lessons_learned}
        """

        embedding = await self.embedding_service.embed(content)

        await KnowledgeVector.objects.acreate(
            source_type=KnowledgeVector.SourceType.DEPLOYMENT,
            source_id=deployment.id,
            content=content,
            content_hash=hash_content(content),
            embedding=embedding,
            embedding_model=self.embedding_service.default_model_name,
            application=deployment.application,
            source_created_at=deployment.created_at,
        )
        return 1
```

---

## Knowledge Retrieval

### Retrieval Service

```python
# backend/apps/knowledge/retrieval/service.py

from pgvector.django import CosineDistance

class KnowledgeRetrievalService:
    """Service for semantic knowledge retrieval."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def search(
        self,
        query: str,
        source_types: List[str] = None,
        categories: List[str] = None,
        application_id: str = None,
        top_k: int = 10,
        min_similarity: float = 0.7,
    ) -> List[RetrievedKnowledge]:
        """Semantic search for relevant knowledge."""

        # 1. Generate query embedding
        query_embedding = await self.embedding_service.embed(query)

        # 2. Build query
        qs = KnowledgeVector.objects.all()

        if source_types:
            qs = qs.filter(source_type__in=source_types)
        if categories:
            qs = qs.filter(category__in=categories)
        if application_id:
            qs = qs.filter(application_id=application_id)

        # 3. Vector similarity search
        results = await qs.annotate(
            similarity=1 - CosineDistance('embedding', query_embedding)
        ).filter(
            similarity__gte=min_similarity
        ).order_by(
            '-similarity'
        )[:top_k].aall()

        # 4. Format results
        return [
            RetrievedKnowledge(
                id=str(r.id),
                content=r.content,
                source_type=r.source_type,
                source_id=str(r.source_id),
                similarity=r.similarity,
                category=r.category,
                metadata={
                    'source_created_at': r.source_created_at,
                    'tags': r.tags,
                }
            )
            for r in results
        ]

    async def hybrid_search(
        self,
        query: str,
        keyword_weight: float = 0.3,
        **kwargs,
    ) -> List[RetrievedKnowledge]:
        """Combined vector + keyword search."""

        # Vector search
        vector_results = await self.search(query, **kwargs)

        # Keyword search
        keyword_results = await KnowledgeVector.objects.filter(
            content__icontains=query
        )[:kwargs.get('top_k', 10)].aall()

        # Combine and rerank
        combined = self._merge_results(
            vector_results,
            keyword_results,
            keyword_weight
        )

        return combined
```

---

## API Endpoints

```python
# backend/apps/knowledge/urls.py

# Configuration
GET    /api/v1/knowledge/config/                    # Get embedding config
PUT    /api/v1/knowledge/config/                    # Update config
POST   /api/v1/knowledge/config/test/               # Test embedding provider

# Indexing
POST   /api/v1/knowledge/index/document/{id}/       # Index document
POST   /api/v1/knowledge/index/deployment/{id}/     # Index deployment
POST   /api/v1/knowledge/index/bulk/                # Bulk indexing
DELETE /api/v1/knowledge/index/source/{type}/{id}/  # Remove from index

# Search
POST   /api/v1/knowledge/search/                    # Semantic search
POST   /api/v1/knowledge/search/hybrid/             # Hybrid search

# Stats
GET    /api/v1/knowledge/stats/                     # Index statistics
```

---

## Admin Configuration UI

```tsx
// frontend/src/routes/settings/KnowledgeConfigTab.tsx

export function KnowledgeConfigTab() {
  return (
    <div className="space-y-6">
      <Card className="glass">
        <CardHeader>
          <CardTitle>Embedding Configuration</CardTitle>
          <CardDescription>
            Configure the embedding model for AI knowledge retrieval
          </CardDescription>
        </CardHeader>
        <CardContent>
          <Form onSubmit={handleSave}>
            <Select name="provider" label="Provider">
              <SelectItem value="openai">OpenAI</SelectItem>
              <SelectItem value="cohere">Cohere</SelectItem>
              <SelectItem value="local">Local (Sentence Transformers)</SelectItem>
            </Select>

            {provider === 'openai' && (
              <>
                <Input name="api_key" type="password" label="API Key" />
                <Select name="model" label="Model">
                  <SelectItem value="text-embedding-3-small">text-embedding-3-small (1536 dims)</SelectItem>
                  <SelectItem value="text-embedding-3-large">text-embedding-3-large (3072 dims)</SelectItem>
                </Select>
              </>
            )}

            {provider === 'cohere' && (
              <>
                <Input name="api_key" type="password" label="API Key" />
                <Select name="model" label="Model">
                  <SelectItem value="embed-english-v3.0">embed-english-v3.0</SelectItem>
                  <SelectItem value="embed-multilingual-v3.0">embed-multilingual-v3.0</SelectItem>
                </Select>
              </>
            )}

            {provider === 'local' && (
              <Select name="model" label="Model">
                <SelectItem value="all-MiniLM-L6-v2">all-MiniLM-L6-v2 (384 dims, fast)</SelectItem>
                <SelectItem value="all-mpnet-base-v2">all-mpnet-base-v2 (768 dims, balanced)</SelectItem>
              </Select>
            )}

            <Button type="submit">Save Configuration</Button>
          </Form>
        </CardContent>
      </Card>

      <Card className="glass">
        <CardHeader>
          <CardTitle>Knowledge Index Statistics</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-4 gap-4">
            <StatCard label="Total Vectors" value={stats?.total_vectors} />
            <StatCard label="Policy Documents" value={stats?.policy_documents} />
            <StatCard label="Deployments" value={stats?.deployments} />
            <StatCard label="Last Indexed" value={stats?.last_indexed} />
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## Deliverables

1. `backend/apps/knowledge/` Django app with pgvector integration
2. Embedding provider implementations (OpenAI, Cohere, local)
3. Knowledge indexing pipeline
4. Semantic search API
5. Admin configuration UI for embedding settings
6. Celery tasks for background indexing
7. Migration for pgvector extension and tables
8. API documentation in `docs/api/knowledge-api.yaml`
