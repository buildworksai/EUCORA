# RAG & Vector Storage Patterns

Comprehensive guide to Retrieval-Augmented Generation with pgvector and Django.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                           AI Agents                                  │
│   (Packaging, CAB Evidence, Risk Explainer, Deployment, Chatbot)    │
└────────────────────────────────┬────────────────────────────────────┘
                                 │ Query
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    Knowledge Retrieval Service                       │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │    Query     │  │  Embedding   │  │      Reranking            │  │
│  │    Parser    │  │  Generator   │  │      (optional)           │  │
│  └──────────────┘  └──────────────┘  └───────────────────────────┘  │
└────────────────────────────────┬────────────────────────────────────┘
                                 │
                                 ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    PostgreSQL + pgvector                             │
│  ┌───────────────────────────────────────────────────────────────┐  │
│  │                     knowledge_vectors                          │  │
│  │  id | source_type | content | embedding (vector) | metadata   │  │
│  └───────────────────────────────────────────────────────────────┘  │
│  ┌───────────────┐  ┌────────────────────────────────────────────┐  │
│  │  HNSW Index   │  │           Metadata Indexes                 │  │
│  └───────────────┘  └────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
                                 ▲
                                 │ Index
┌─────────────────────────────────────────────────────────────────────┐
│                      Embedding Pipeline                              │
│  ┌──────────────┐  ┌──────────────┐  ┌───────────────────────────┐  │
│  │   Chunking   │  │  Embedding   │  │     Storage               │  │
│  │   Service    │  │  Provider    │  │     Writer                │  │
│  └──────────────┘  └──────────────┘  └───────────────────────────┘  │
└─────────────────────────────────────────────────────────────────────┘
```

---

## pgvector Setup

### Database Configuration

```sql
-- Enable pgvector extension (requires PostgreSQL 14+)
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify installation
SELECT * FROM pg_extension WHERE extname = 'vector';
```

### Django Settings

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'eucora',
        'OPTIONS': {
            'options': '-c search_path=public,vector',
        },
    }
}

# Install pgvector-python
# pip install pgvector
```

---

## Data Models

### Embedding Configuration

```python
# apps/knowledge/models.py
from django.db import models
from apps.core.models import TimeStampedModel
from django.contrib.postgres.fields import ArrayField

class EmbeddingConfig(TimeStampedModel):
    """Configuration for embedding providers."""

    class Provider(models.TextChoices):
        OPENAI = "openai", "OpenAI"
        COHERE = "cohere", "Cohere"
        LOCAL = "local", "Local (Sentence Transformers)"
        AZURE = "azure", "Azure OpenAI"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    provider = models.CharField(max_length=32, choices=Provider.choices)
    model_name = models.CharField(max_length=128)
    dimensions = models.IntegerField()

    # API Configuration (encrypted in production)
    api_key = models.CharField(max_length=256, blank=True)
    api_endpoint = models.URLField(blank=True, null=True)

    # Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)

    # Rate limiting
    requests_per_minute = models.IntegerField(default=60)
    batch_size = models.IntegerField(default=100)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['is_default'],
                condition=models.Q(is_default=True),
                name='unique_default_embedding'
            )
        ]
```

### Knowledge Vector Model

```python
from pgvector.django import VectorField, HnswIndex

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

    # Source tracking
    source_type = models.CharField(max_length=64, choices=SourceType.choices, db_index=True)
    source_id = models.UUIDField(db_index=True)
    source_chunk_index = models.IntegerField(default=0)

    # Content
    content = models.TextField()
    content_hash = models.CharField(max_length=64, db_index=True)  # SHA-256

    # Vector embedding
    embedding = VectorField(dimensions=1536)  # Adjust per model
    embedding_model = models.CharField(max_length=64)

    # Metadata for filtering
    category = models.CharField(max_length=64, blank=True, db_index=True)
    tags = ArrayField(models.CharField(max_length=64), default=list)
    application = models.ForeignKey(
        'application_portfolio.Application',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )

    # Audit
    source_created_at = models.DateTimeField(null=True)
    correlation_id = models.UUIDField(default=uuid.uuid4)

    class Meta:
        indexes = [
            # HNSW index for fast similarity search
            HnswIndex(
                name='knowledge_embedding_hnsw_idx',
                fields=['embedding'],
                m=16,  # Max connections per layer
                ef_construction=64,  # Size of dynamic candidate list
                opclasses=['vector_cosine_ops'],
            ),
            models.Index(fields=['source_type', 'source_id']),
            models.Index(fields=['category']),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=['source_type', 'source_id', 'source_chunk_index'],
                name='unique_source_chunk'
            )
        ]
```

---

## Embedding Providers

### Base Provider Interface

```python
# apps/knowledge/embeddings/base.py
from abc import ABC, abstractmethod
from typing import List
import hashlib

class EmbeddingProvider(ABC):
    """Abstract base for embedding providers."""

    @abstractmethod
    async def embed(self, text: str) -> List[float]:
        """Generate embedding for single text."""
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

    def hash_content(self, text: str) -> str:
        """Generate SHA-256 hash of content."""
        return hashlib.sha256(text.encode()).hexdigest()
```

### OpenAI Provider

```python
# apps/knowledge/embeddings/openai.py
import openai
from .base import EmbeddingProvider

class OpenAIEmbeddingProvider(EmbeddingProvider):
    """OpenAI embedding provider."""

    MODEL_DIMENSIONS = {
        "text-embedding-3-small": 1536,
        "text-embedding-3-large": 3072,
        "text-embedding-ada-002": 1536,
    }

    def __init__(
        self,
        api_key: str,
        model: str = "text-embedding-3-small",
        dimensions: int | None = None,
    ):
        self.client = openai.AsyncOpenAI(api_key=api_key)
        self._model = model
        self._dimensions = dimensions or self.MODEL_DIMENSIONS.get(model, 1536)

    async def embed(self, text: str) -> List[float]:
        response = await self.client.embeddings.create(
            input=text,
            model=self._model,
            dimensions=self._dimensions,
        )
        return response.data[0].embedding

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        # OpenAI supports up to 2048 texts per batch
        response = await self.client.embeddings.create(
            input=texts,
            model=self._model,
            dimensions=self._dimensions,
        )
        # Sort by index to maintain order
        sorted_data = sorted(response.data, key=lambda x: x.index)
        return [item.embedding for item in sorted_data]

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model
```

### Local Provider (Sentence Transformers)

```python
# apps/knowledge/embeddings/local.py
from sentence_transformers import SentenceTransformer
from .base import EmbeddingProvider
import asyncio

class LocalEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformers provider (no API calls)."""

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        self._model_name = model
        self._model = SentenceTransformer(model)
        self._dimensions = self._model.get_sentence_embedding_dimension()

    async def embed(self, text: str) -> List[float]:
        # Run in thread pool to avoid blocking
        loop = asyncio.get_event_loop()
        embedding = await loop.run_in_executor(
            None,
            lambda: self._model.encode(text, convert_to_numpy=True)
        )
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            lambda: self._model.encode(texts, convert_to_numpy=True)
        )
        return embeddings.tolist()

    @property
    def dimensions(self) -> int:
        return self._dimensions

    @property
    def model_name(self) -> str:
        return self._model_name
```

### Provider Factory

```python
# apps/knowledge/embeddings/factory.py
from typing import Dict
from .base import EmbeddingProvider
from .openai import OpenAIEmbeddingProvider
from .local import LocalEmbeddingProvider
from ..models import EmbeddingConfig

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
        self._default_provider: EmbeddingProvider | None = None

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
            return OpenAIEmbeddingProvider(
                api_key=config.api_key,
                model=config.model_name,
                dimensions=config.dimensions,
            )
        elif config.provider == EmbeddingConfig.Provider.LOCAL:
            return LocalEmbeddingProvider(model=config.model_name)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    def _get_provider(self, provider_id: str | None = None) -> EmbeddingProvider:
        if provider_id and provider_id in self._providers:
            return self._providers[provider_id]
        if self._default_provider:
            return self._default_provider
        raise ValueError("No embedding provider configured")

    async def embed(self, text: str, provider_id: str | None = None) -> List[float]:
        provider = self._get_provider(provider_id)
        return await provider.embed(text)

    async def embed_batch(
        self,
        texts: List[str],
        provider_id: str | None = None,
    ) -> List[List[float]]:
        provider = self._get_provider(provider_id)
        return await provider.embed_batch(texts)

    @property
    def default_model_name(self) -> str:
        if self._default_provider:
            return self._default_provider.model_name
        raise ValueError("No default provider configured")
```

---

## Text Chunking

### Semantic Chunker

```python
# apps/knowledge/chunking/semantic.py
from dataclasses import dataclass
from typing import List
import re

@dataclass
class Chunk:
    content: str
    index: int
    start_char: int
    end_char: int
    metadata: dict

class SemanticChunker:
    """Chunk text semantically by paragraphs and sections."""

    def __init__(
        self,
        chunk_size: int = 800,
        chunk_overlap: int = 100,
        min_chunk_size: int = 100,
    ):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.min_chunk_size = min_chunk_size

    def chunk(self, text: str, metadata: dict = None) -> List[Chunk]:
        """Split text into semantic chunks with overlap."""
        metadata = metadata or {}
        chunks = []

        # Split by paragraphs first
        paragraphs = re.split(r'\n\n+', text)

        current_chunk = ""
        current_start = 0
        chunk_index = 0
        char_position = 0

        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue

            # If adding paragraph exceeds chunk size
            if len(current_chunk) + len(paragraph) > self.chunk_size:
                # Save current chunk if it meets minimum size
                if len(current_chunk) >= self.min_chunk_size:
                    chunks.append(Chunk(
                        content=current_chunk.strip(),
                        index=chunk_index,
                        start_char=current_start,
                        end_char=char_position,
                        metadata=metadata,
                    ))
                    chunk_index += 1

                # Start new chunk with overlap
                overlap_text = self._get_overlap(current_chunk)
                current_chunk = overlap_text + paragraph
                current_start = char_position - len(overlap_text)
            else:
                if current_chunk:
                    current_chunk += "\n\n"
                current_chunk += paragraph

            char_position += len(paragraph) + 2  # +2 for paragraph breaks

        # Don't forget the last chunk
        if len(current_chunk) >= self.min_chunk_size:
            chunks.append(Chunk(
                content=current_chunk.strip(),
                index=chunk_index,
                start_char=current_start,
                end_char=char_position,
                metadata=metadata,
            ))

        return chunks

    def _get_overlap(self, text: str) -> str:
        """Get overlap text from end of chunk."""
        if len(text) <= self.chunk_overlap:
            return text

        # Try to find sentence boundary for clean overlap
        overlap_text = text[-self.chunk_overlap:]
        sentence_start = overlap_text.find('. ')
        if sentence_start > 0:
            return overlap_text[sentence_start + 2:]

        return overlap_text
```

---

## Indexing Pipeline

### Document Indexer

```python
# apps/knowledge/indexing/pipeline.py
from typing import List
import hashlib
from ..models import KnowledgeVector
from ..embeddings.factory import EmbeddingService
from ..chunking.semantic import SemanticChunker

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
        document_id: str,
        content: str,
        source_type: str,
        category: str = "",
        tags: List[str] = None,
        application_id: str = None,
    ) -> int:
        """Index a document with chunking."""
        tags = tags or []

        # Chunk content
        chunks = self.chunker.chunk(content)

        if not chunks:
            return 0

        # Generate embeddings in batch
        embeddings = await self.embedding_service.embed_batch(
            [chunk.content for chunk in chunks]
        )

        # Create vector records
        vectors = []
        for chunk, embedding in zip(chunks, embeddings):
            content_hash = hashlib.sha256(chunk.content.encode()).hexdigest()

            vectors.append(KnowledgeVector(
                source_type=source_type,
                source_id=document_id,
                source_chunk_index=chunk.index,
                content=chunk.content,
                content_hash=content_hash,
                embedding=embedding,
                embedding_model=self.embedding_service.default_model_name,
                category=category,
                tags=tags,
                application_id=application_id,
            ))

        # Bulk insert (handles duplicates via constraint)
        await KnowledgeVector.objects.abulk_create(
            vectors,
            update_conflicts=True,
            update_fields=['content', 'content_hash', 'embedding', 'updated_at'],
            unique_fields=['source_type', 'source_id', 'source_chunk_index'],
        )

        return len(vectors)

    async def index_deployment(self, deployment) -> int:
        """Index deployment record for historical knowledge."""
        content = f"""
        Deployment: {deployment.application.name} v{deployment.version}
        Status: {deployment.status}
        Risk Score: {deployment.risk_score}
        Target Ring: {deployment.get_target_ring_display()}
        Success Rate: {deployment.success_rate}%

        Summary: {deployment.summary or 'No summary'}
        Outcome: {deployment.outcome or 'No outcome recorded'}
        Lessons Learned: {deployment.lessons_learned or 'None recorded'}
        """.strip()

        return await self.index_document(
            document_id=str(deployment.id),
            content=content,
            source_type=KnowledgeVector.SourceType.DEPLOYMENT,
            application_id=str(deployment.application_id),
        )

    async def remove_from_index(
        self,
        source_type: str,
        source_id: str,
    ) -> int:
        """Remove all vectors for a source."""
        result = await KnowledgeVector.objects.filter(
            source_type=source_type,
            source_id=source_id,
        ).adelete()
        return result[0]  # Number deleted
```

---

## Knowledge Retrieval

### Semantic Search Service

```python
# apps/knowledge/retrieval/service.py
from dataclasses import dataclass
from typing import List, Optional
from pgvector.django import CosineDistance
from ..models import KnowledgeVector
from ..embeddings.factory import EmbeddingService

@dataclass
class RetrievedKnowledge:
    id: str
    content: str
    source_type: str
    source_id: str
    similarity: float
    category: str
    metadata: dict

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

        # Generate query embedding
        query_embedding = await self.embedding_service.embed(query)

        # Build query with filters
        qs = KnowledgeVector.objects.all()

        if source_types:
            qs = qs.filter(source_type__in=source_types)
        if categories:
            qs = qs.filter(category__in=categories)
        if application_id:
            qs = qs.filter(application_id=application_id)

        # Vector similarity search with cosine distance
        results = await qs.annotate(
            similarity=1 - CosineDistance('embedding', query_embedding)
        ).filter(
            similarity__gte=min_similarity
        ).order_by(
            '-similarity'
        )[:top_k].aall()

        return [
            RetrievedKnowledge(
                id=str(r.id),
                content=r.content,
                source_type=r.source_type,
                source_id=str(r.source_id),
                similarity=float(r.similarity),
                category=r.category,
                metadata={
                    'source_created_at': r.source_created_at.isoformat() if r.source_created_at else None,
                    'tags': r.tags,
                    'chunk_index': r.source_chunk_index,
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
        top_k = kwargs.get('top_k', 10)
        keyword_qs = KnowledgeVector.objects.filter(
            content__icontains=query
        )

        if kwargs.get('source_types'):
            keyword_qs = keyword_qs.filter(source_type__in=kwargs['source_types'])

        keyword_results = await keyword_qs[:top_k].aall()

        # Merge and rerank
        return self._merge_results(vector_results, keyword_results, keyword_weight)

    def _merge_results(
        self,
        vector_results: List[RetrievedKnowledge],
        keyword_results,
        keyword_weight: float,
    ) -> List[RetrievedKnowledge]:
        """Merge vector and keyword results with RRF."""
        scores = {}

        # Score vector results (higher rank = lower position)
        for i, result in enumerate(vector_results):
            rrf_score = 1 / (60 + i)  # RRF with k=60
            scores[result.id] = {
                'result': result,
                'score': rrf_score * (1 - keyword_weight),
            }

        # Add keyword results
        for i, kw_result in enumerate(keyword_results):
            result_id = str(kw_result.id)
            rrf_score = 1 / (60 + i)

            if result_id in scores:
                scores[result_id]['score'] += rrf_score * keyword_weight
            else:
                scores[result_id] = {
                    'result': RetrievedKnowledge(
                        id=result_id,
                        content=kw_result.content,
                        source_type=kw_result.source_type,
                        source_id=str(kw_result.source_id),
                        similarity=0.0,
                        category=kw_result.category,
                        metadata={'keyword_match': True},
                    ),
                    'score': rrf_score * keyword_weight,
                }

        # Sort by combined score
        sorted_results = sorted(
            scores.values(),
            key=lambda x: x['score'],
            reverse=True,
        )

        return [item['result'] for item in sorted_results]
```

---

## API Endpoints

### Views

```python
# apps/knowledge/views.py
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from .retrieval.service import KnowledgeRetrievalService
from .indexing.pipeline import KnowledgeIndexingPipeline
from .embeddings.factory import EmbeddingService

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def search_knowledge(request):
    """
    Semantic search endpoint.

    POST /api/v1/knowledge/search/
    {
        "query": "How do we handle failed deployments?",
        "source_types": ["deployment", "runbook"],
        "top_k": 5,
        "min_similarity": 0.7
    }
    """
    query = request.data.get('query')
    if not query:
        return Response(
            {'error': 'query is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    service = KnowledgeRetrievalService(EmbeddingService.get_instance())

    results = await service.search(
        query=query,
        source_types=request.data.get('source_types'),
        categories=request.data.get('categories'),
        application_id=request.data.get('application_id'),
        top_k=request.data.get('top_k', 10),
        min_similarity=request.data.get('min_similarity', 0.7),
    )

    return Response({
        'query': query,
        'results': [
            {
                'id': r.id,
                'content': r.content,
                'source_type': r.source_type,
                'source_id': r.source_id,
                'similarity': r.similarity,
                'category': r.category,
                'metadata': r.metadata,
            }
            for r in results
        ],
        'count': len(results),
    })

@api_view(['POST'])
@permission_classes([IsAuthenticated])
async def index_document(request, document_id: str):
    """
    Index a document.

    POST /api/v1/knowledge/index/document/{document_id}/
    """
    from apps.documents.models import PolicyDocument

    document = await PolicyDocument.objects.aget(id=document_id)

    pipeline = KnowledgeIndexingPipeline(EmbeddingService.get_instance())

    chunks_indexed = await pipeline.index_document(
        document_id=str(document.id),
        content=document.content,
        source_type='policy_document',
        category=document.category,
        tags=document.tags,
    )

    return Response({
        'document_id': str(document.id),
        'chunks_indexed': chunks_indexed,
        'status': 'indexed',
    })
```

---

## Celery Tasks for Background Indexing

```python
# apps/knowledge/tasks.py
from celery import shared_task
from asgiref.sync import async_to_sync

@shared_task(bind=True, max_retries=3)
def index_document_task(self, document_id: str, source_type: str):
    """Background task for document indexing."""
    from .indexing.pipeline import KnowledgeIndexingPipeline
    from .embeddings.factory import EmbeddingService

    try:
        service = EmbeddingService.get_instance()
        async_to_sync(service.initialize)()

        pipeline = KnowledgeIndexingPipeline(service)

        # Get document based on source type
        if source_type == 'policy_document':
            from apps.documents.models import PolicyDocument
            doc = PolicyDocument.objects.get(id=document_id)
            chunks = async_to_sync(pipeline.index_document)(
                document_id=str(doc.id),
                content=doc.content,
                source_type=source_type,
            )

        return {'status': 'indexed', 'chunks': chunks}

    except Exception as e:
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))

@shared_task
def reindex_all_knowledge():
    """Reindex all knowledge sources."""
    from apps.documents.models import PolicyDocument
    from apps.deployments.models import Deployment

    # Queue document indexing
    for doc in PolicyDocument.objects.all():
        index_document_task.delay(str(doc.id), 'policy_document')

    # Queue deployment indexing
    for deployment in Deployment.objects.filter(status='completed'):
        index_document_task.delay(str(deployment.id), 'deployment')
```

---

## Best Practices

### Embedding Model Selection

| Model | Dimensions | Speed | Quality | Cost |
|-------|-----------|-------|---------|------|
| text-embedding-3-small | 1536 | Fast | Good | Low |
| text-embedding-3-large | 3072 | Medium | Best | High |
| all-MiniLM-L6-v2 | 384 | Fastest | Fair | Free |
| all-mpnet-base-v2 | 768 | Fast | Good | Free |

### Chunking Guidelines

- **Chunk size**: 400-1000 characters for most use cases
- **Overlap**: 10-20% of chunk size
- **Semantic boundaries**: Split on paragraphs, sections, not mid-sentence

### Index Tuning

```sql
-- HNSW parameters for production
-- m: connections per layer (16-64, higher = better recall, more memory)
-- ef_construction: build-time search width (64-200)

CREATE INDEX CONCURRENTLY knowledge_hnsw_idx
ON knowledge_vectors
USING hnsw (embedding vector_cosine_ops)
WITH (m = 24, ef_construction = 100);

-- Set search-time ef parameter
SET hnsw.ef_search = 100;  -- Higher = better recall, slower
```

### Query Optimization

```python
# Good: Filter before vector search
results = await qs.filter(
    source_type='deployment',
    category='critical',
).annotate(
    similarity=1 - CosineDistance('embedding', query_embedding)
).filter(similarity__gte=0.7)[:10].aall()

# Bad: Filter after fetching all results
results = await qs.annotate(
    similarity=1 - CosineDistance('embedding', query_embedding)
)[:1000].aall()
results = [r for r in results if r.source_type == 'deployment']
```
