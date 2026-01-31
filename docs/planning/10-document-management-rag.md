# E1: Document Management & RAG Pipeline

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Version**: 1.0
**Date**: 2026-01-30
**Status**: Draft for Implementation
**Priority**: P1-Critical
**Dependencies**: E7 (pgvector)

---

## Overview

Enable administrators to upload policy documents (PDF, DOCX, HTML) that AI agents use as context when performing operations. Documents are vectorized and stored in pgvector for semantic retrieval (RAG - Retrieval Augmented Generation).

---

## Requirements

### Functional Requirements

1. **Document Upload**
   - Drag-and-drop interface for file upload
   - Supported formats: PDF, DOCX, DOC, HTML, TXT, MD
   - Maximum file size: 50MB per document
   - Batch upload support (up to 20 files)

2. **Document Categorization**
   - **Compliance Policies**: Regulatory requirements, audit standards
   - **Security Policies**: PKI, vulnerability thresholds, access controls
   - **Operational Policies**: SLA definitions, escalation procedures
   - **Governance Policies**: CAB rules, approval workflows, ring criteria
   - **Application Policies**: Packaging standards, detection rules
   - **Custom Categories**: Admin-defined categories

3. **Document Management**
   - Version history with immutable audit trail
   - Document status: Draft, Active, Deprecated, Archived
   - Tagging and metadata (author, effective date, review date)
   - Full-text search within documents
   - Bulk operations (archive, delete, re-categorize)

4. **RAG Integration**
   - Automatic chunking with semantic boundaries
   - Vector embedding generation (configurable model)
   - Similarity search for AI agent context retrieval
   - Source citation in AI responses

---

## Data Model

### Backend Models (Django)

```python
# backend/apps/policy_documents/models.py

class DocumentCategory(TimeStampedModel):
    """Policy document categories."""

    class CategoryType(models.TextChoices):
        COMPLIANCE = "compliance", "Compliance Policies"
        SECURITY = "security", "Security Policies"
        OPERATIONAL = "operational", "Operational Policies"
        GOVERNANCE = "governance", "Governance Policies"
        APPLICATION = "application", "Application Policies"
        CUSTOM = "custom", "Custom Category"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=128, unique=True)
    category_type = models.CharField(max_length=32, choices=CategoryType.choices)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=64, blank=True)  # Lucide icon name
    color = models.CharField(max_length=32, blank=True)  # Tailwind color class
    is_system = models.BooleanField(default=False)  # Cannot be deleted
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)


class PolicyDocument(TimeStampedModel, CorrelationIdModel):
    """Uploaded policy documents for RAG."""

    class DocumentStatus(models.TextChoices):
        DRAFT = "draft", "Draft"
        PROCESSING = "processing", "Processing"
        ACTIVE = "active", "Active"
        DEPRECATED = "deprecated", "Deprecated"
        ARCHIVED = "archived", "Archived"
        FAILED = "failed", "Processing Failed"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Metadata
    title = models.CharField(max_length=256)
    description = models.TextField(blank=True)
    category = models.ForeignKey(DocumentCategory, on_delete=models.PROTECT)
    tags = models.JSONField(default=list)  # ["intune", "windows", "packaging"]

    # File storage
    file_name = models.CharField(max_length=256)
    file_type = models.CharField(max_length=32)  # pdf, docx, html, txt, md
    file_size = models.BigIntegerField()
    storage_path = models.CharField(max_length=512)  # Path in object storage
    content_hash = models.CharField(max_length=64)  # SHA-256

    # Processing status
    status = models.CharField(max_length=32, choices=DocumentStatus.choices, default=DocumentStatus.DRAFT)
    processing_error = models.TextField(blank=True)
    chunk_count = models.IntegerField(default=0)

    # Versioning
    version = models.IntegerField(default=1)
    parent_document = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True)

    # Governance
    effective_date = models.DateField(null=True, blank=True)
    review_date = models.DateField(null=True, blank=True)
    author = models.CharField(max_length=256, blank=True)

    # Audit
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["category", "status"]),
            models.Index(fields=["status", "created_at"]),
            models.Index(fields=["content_hash"]),
        ]


class DocumentChunk(TimeStampedModel):
    """Chunked document content for vector storage."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    document = models.ForeignKey(PolicyDocument, on_delete=models.CASCADE, related_name="chunks")

    # Chunk content
    chunk_index = models.IntegerField()
    content = models.TextField()
    content_hash = models.CharField(max_length=64)

    # Metadata for retrieval
    heading = models.CharField(max_length=256, blank=True)  # Section heading if available
    page_number = models.IntegerField(null=True, blank=True)
    start_char = models.IntegerField()
    end_char = models.IntegerField()

    # Vector embedding (stored in pgvector)
    embedding = VectorField(dimensions=1536, null=True)  # OpenAI ada-002 dimensions
    embedding_model = models.CharField(max_length=64, blank=True)

    class Meta:
        ordering = ["document", "chunk_index"]
        indexes = [
            models.Index(fields=["document", "chunk_index"]),
        ]
```

---

## API Endpoints

```python
# backend/apps/policy_documents/urls.py

# Document Categories
GET    /api/v1/policy-documents/categories/              # List categories
POST   /api/v1/policy-documents/categories/              # Create category (admin)
PUT    /api/v1/policy-documents/categories/{id}/         # Update category
DELETE /api/v1/policy-documents/categories/{id}/         # Delete (if no documents)

# Documents
GET    /api/v1/policy-documents/                         # List documents (filterable)
POST   /api/v1/policy-documents/upload/                  # Upload document(s)
GET    /api/v1/policy-documents/{id}/                    # Get document details
PUT    /api/v1/policy-documents/{id}/                    # Update metadata
DELETE /api/v1/policy-documents/{id}/                    # Delete document
POST   /api/v1/policy-documents/{id}/reprocess/          # Reprocess document
GET    /api/v1/policy-documents/{id}/download/           # Download original file
GET    /api/v1/policy-documents/{id}/chunks/             # List chunks
GET    /api/v1/policy-documents/{id}/versions/           # Version history

# Search
POST   /api/v1/policy-documents/search/                  # Full-text search
POST   /api/v1/policy-documents/semantic-search/         # Vector similarity search

# Bulk Operations
POST   /api/v1/policy-documents/bulk-archive/            # Archive multiple
POST   /api/v1/policy-documents/bulk-delete/             # Delete multiple
POST   /api/v1/policy-documents/bulk-categorize/         # Re-categorize multiple
```

---

## Frontend Components

### Admin Document Library Page

```
/admin/policy-documents
├── Header
│   ├── Title: "Policy Document Library"
│   ├── Stats: Total documents, Active, Processing
│   └── Upload Button (opens upload dialog)
├── Filters
│   ├── Category dropdown (multi-select)
│   ├── Status dropdown
│   ├── Date range picker
│   └── Search input
├── Category Tabs
│   ├── All Documents
│   ├── Compliance
│   ├── Security
│   ├── Operational
│   ├── Governance
│   ├── Application
│   └── Custom (if any)
├── Document Grid/List (toggle view)
│   ├── Document Card
│   │   ├── Icon (based on file type)
│   │   ├── Title
│   │   ├── Category badge
│   │   ├── Status badge
│   │   ├── Upload date
│   │   ├── Tags
│   │   └── Actions (View, Edit, Delete, Download)
│   └── Empty State
└── Pagination
```

### Upload Dialog Component

```tsx
// frontend/src/components/documents/DocumentUploadDialog.tsx

interface Props {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onUploadComplete: () => void;
}

Features:
- Drag-and-drop zone with visual feedback
- File type validation (PDF, DOCX, HTML, TXT, MD)
- File size validation (max 50MB)
- Category selection (required)
- Tags input (optional)
- Metadata form (title, description, effective date)
- Upload progress indicator
- Error handling with retry option
```

### Document Detail Dialog

```tsx
// frontend/src/components/documents/DocumentDetailDialog.tsx

Tabs:
1. Overview
   - Title, description, category
   - Status with processing info
   - Metadata (author, dates, size)
   - Download button

2. Content Preview
   - Rendered document preview (PDF viewer, HTML render)
   - Chunk visualization (show chunks with highlights)

3. RAG Usage
   - Recent AI queries that used this document
   - Chunk retrieval frequency
   - Relevance scores

4. Version History
   - Timeline of versions
   - Diff viewer (if text-based)
   - Restore previous version

5. Audit Trail
   - Creation, updates, access log
```

---

## Document Processing Pipeline

### Processing Flow

```
1. Upload Received
   └── Validate file type and size

2. Store Original
   └── Upload to object storage (MinIO/S3/Blob)
   └── Generate content hash

3. Extract Text
   ├── PDF: PyMuPDF (fitz) or pdfplumber
   ├── DOCX: python-docx
   ├── HTML: BeautifulSoup
   └── TXT/MD: Direct read

4. Chunk Content
   └── Semantic chunking (respect paragraph/section boundaries)
   └── Target chunk size: 500-1000 tokens
   └── Overlap: 50-100 tokens

5. Generate Embeddings
   └── Call embedding API (configurable model)
   └── Store vectors in pgvector

6. Mark Complete
   └── Update document status to "active"
```

### Chunking Strategy

```python
# backend/apps/policy_documents/services/chunking.py

class SemanticChunker:
    """Chunk documents while respecting semantic boundaries."""

    def __init__(
        self,
        target_chunk_size: int = 800,  # tokens
        max_chunk_size: int = 1200,
        overlap_size: int = 100,
    ):
        self.target_chunk_size = target_chunk_size
        self.max_chunk_size = max_chunk_size
        self.overlap_size = overlap_size

    def chunk(self, text: str, headings: list[str] = None) -> list[Chunk]:
        """
        Chunk text while:
        1. Respecting heading boundaries
        2. Keeping paragraphs together when possible
        3. Adding overlap for context continuity
        """
        pass
```

---

## RAG Integration for AI Agents

### Context Retrieval Service

```python
# backend/apps/policy_documents/services/rag.py

class PolicyContextRetriever:
    """Retrieve relevant policy context for AI agent operations."""

    def __init__(self, embedding_service: EmbeddingService):
        self.embedding_service = embedding_service

    async def get_context(
        self,
        query: str,
        categories: list[str] = None,
        top_k: int = 5,
        min_similarity: float = 0.7,
    ) -> list[RetrievedChunk]:
        """
        Retrieve most relevant policy chunks for a query.

        Returns:
            List of chunks with content, source document, and similarity score.
        """
        # 1. Generate query embedding
        query_embedding = await self.embedding_service.embed(query)

        # 2. Vector similarity search in pgvector
        chunks = await DocumentChunk.objects.filter(
            document__status="active",
            document__category__category_type__in=categories if categories else ALL_CATEGORIES,
        ).order_by(
            CosineDistance("embedding", query_embedding)
        )[:top_k]

        # 3. Filter by minimum similarity
        # 4. Return with source attribution
        pass

    def format_context(self, chunks: list[RetrievedChunk]) -> str:
        """Format chunks into context string for LLM prompt."""
        context_parts = []
        for chunk in chunks:
            context_parts.append(f"""
--- Policy: {chunk.document.title} ({chunk.document.category.name}) ---
{chunk.content}
---
            """)
        return "\n".join(context_parts)
```

### Agent Integration

```python
# In AI agent execution

async def execute_with_policy_context(
    agent_type: str,
    operation: str,
    input_data: dict,
) -> AgentResult:
    """Execute agent operation with relevant policy context."""

    # 1. Build context query from operation
    context_query = f"{agent_type} operation: {operation}"

    # 2. Retrieve relevant policies
    retriever = PolicyContextRetriever(embedding_service)
    chunks = await retriever.get_context(
        query=context_query,
        categories=get_relevant_categories(agent_type),
        top_k=5,
    )

    # 3. Format context for prompt
    policy_context = retriever.format_context(chunks)

    # 4. Include in agent prompt
    prompt = f"""
You are executing a {agent_type} operation.

RELEVANT POLICIES:
{policy_context}

OPERATION DETAILS:
{operation}

INPUT:
{json.dumps(input_data, indent=2)}

Follow the policies above when making decisions. Cite specific policies when relevant.
"""

    # 5. Execute with LLM
    # 6. Return result with policy citations
```

---

## Security Considerations

1. **Access Control**: Only admins can upload/manage documents
2. **Content Validation**: Scan uploads for malware before processing
3. **Data Isolation**: Documents scoped to tenant (future multi-tenant)
4. **Audit Trail**: All document operations logged with correlation IDs
5. **Encryption**: Documents encrypted at rest in object storage

---

## Testing Requirements

1. **Unit Tests**
   - Document upload validation
   - Chunking algorithm
   - Embedding generation
   - Search functionality

2. **Integration Tests**
   - Full upload → process → search flow
   - AI agent context retrieval
   - Storage provider integration

3. **Performance Tests**
   - Large document processing (50MB PDFs)
   - Concurrent uploads
   - Search latency with 10K+ documents

---

## Deliverables

1. `backend/apps/policy_documents/` Django app
2. `frontend/src/routes/admin/PolicyDocuments.tsx` page
3. `frontend/src/components/documents/` component library
4. API documentation in `docs/api/policy-documents-api.yaml`
5. Admin user guide in `docs/runbooks/policy-document-management.md`
