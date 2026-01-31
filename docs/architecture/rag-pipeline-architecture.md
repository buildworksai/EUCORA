# RAG Pipeline Architecture

**Version**: 1.0
**Status**: Design
**Last Updated**: 2026-01-31

---

## Overview

The RAG (Retrieval-Augmented Generation) Pipeline Architecture defines how EUCORA ingests, processes, stores, and retrieves documents for AI-powered agents. The pipeline supports semantic search, knowledge base integration, and AI-assisted decision making.

## Architecture Components

### 1. Document Ingestion

Documents are ingested from multiple sources:
- **ServiceNow KB**: Knowledge base articles
- **Confluence**: Documentation pages
- **SharePoint**: Policy documents and guides
- **Code Repositories**: README files, API docs, code comments
- **Vendor Documentation**: External documentation sources

### 2. Document Processing

Documents undergo processing pipeline:
- **Text Extraction**: Extract text from various formats (PDF, DOCX, HTML, Markdown)
- **Chunking**: Split documents into manageable chunks
- **Metadata Extraction**: Extract title, author, date, category, tags
- **Language Detection**: Detect document language

### 3. Vector Embedding

Documents are converted to vector embeddings:
- **Embedding Model**: OpenAI text-embedding-ada-002 or Azure OpenAI embeddings
- **Chunk Embedding**: Each chunk is embedded separately
- **Metadata Embedding**: Metadata is included in embedding context

### 4. Vector Storage

Embeddings are stored in PostgreSQL with pgvector extension:
- **Vector Index**: HNSW index for fast similarity search
- **Metadata Storage**: Document metadata stored alongside vectors
- **Versioning**: Support for document versioning

### 5. Semantic Search

Semantic search enables natural language queries:
- **Query Embedding**: User queries are embedded
- **Similarity Search**: Find similar documents using vector similarity
- **Ranking**: Results ranked by relevance score
- **Filtering**: Filter by metadata (source, category, date)

---

## RAG Pipeline Flow

```mermaid
graph TB
    subgraph "Document Sources"
        ServiceNowKB[ServiceNow KB]
        Confluence[Confluence]
        SharePoint[SharePoint]
        CodeRepos[Code Repositories]
        VendorDocs[Vendor Docs]
    end

    subgraph "Ingestion Layer"
        DocumentIngester[Document Ingester]
        FormatParser[Format Parser]
        TextExtractor[Text Extractor]
    end

    subgraph "Processing Layer"
        Chunker[Document Chunker]
        MetadataExtractor[Metadata Extractor]
        LanguageDetector[Language Detector]
    end

    subgraph "Embedding Layer"
        EmbeddingModel[Embedding Model]
        ChunkEmbedder[Chunk Embedder]
    end

    subgraph "Storage Layer"
        VectorDB[(PostgreSQL + pgvector)]
        MetadataDB[(PostgreSQL)]
    end

    subgraph "Query Layer"
        QueryEmbedder[Query Embedder]
        SimilaritySearch[Similarity Search]
        ResultRanker[Result Ranker]
    end

    ServiceNowKB --> DocumentIngester
    Confluence --> DocumentIngester
    SharePoint --> DocumentIngester
    CodeRepos --> DocumentIngester
    VendorDocs --> DocumentIngester

    DocumentIngester --> FormatParser
    FormatParser --> TextExtractor
    TextExtractor --> Chunker
    Chunker --> MetadataExtractor
    MetadataExtractor --> LanguageDetector
    LanguageDetector --> ChunkEmbedder
    ChunkEmbedder --> EmbeddingModel
    EmbeddingModel --> VectorDB
    MetadataExtractor --> MetadataDB

    QueryEmbedder --> EmbeddingModel
    EmbeddingModel --> SimilaritySearch
    SimilaritySearch --> VectorDB
    SimilaritySearch --> MetadataDB
    SimilaritySearch --> ResultRanker
```

---

## Document Ingestion Process

```mermaid
sequenceDiagram
    participant SourceSystem
    participant DocumentIngester
    participant FormatParser
    participant Chunker
    participant Embedder
    participant VectorDB

    SourceSystem->>DocumentIngester: New/Updated Document
    DocumentIngester->>FormatParser: Parse Document
    FormatParser->>FormatParser: Extract Text
    FormatParser->>Chunker: Chunk Text
    Chunker->>Chunker: Create Chunks (500-1000 tokens)
    Chunker->>Embedder: Generate Embeddings
    Embedder->>Embedder: Create Vector Embeddings
    Embedder->>VectorDB: Store Vectors + Metadata
    VectorDB->>DocumentIngester: Confirmation
```

---

## Semantic Search Process

```mermaid
sequenceDiagram
    participant User
    participant QueryAPI
    participant QueryEmbedder
    participant VectorDB
    participant ResultRanker
    participant User

    User->>QueryAPI: Natural Language Query
    QueryAPI->>QueryEmbedder: Embed Query
    QueryEmbedder->>QueryEmbedder: Generate Query Vector
    QueryEmbedder->>VectorDB: Similarity Search
    VectorDB->>VectorDB: Find Top-K Similar Chunks
    VectorDB->>ResultRanker: Return Candidates
    ResultRanker->>ResultRanker: Rank by Relevance
    ResultRanker->>QueryAPI: Ranked Results
    QueryAPI->>User: Search Results
```

---

## Vector Storage Schema

### Document Table
```sql
CREATE TABLE documents (
    id UUID PRIMARY KEY,
    source_type VARCHAR(50),
    external_id VARCHAR(255),
    title VARCHAR(500),
    content TEXT,
    metadata JSONB,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Document Chunks Table
```sql
CREATE TABLE document_chunks (
    id UUID PRIMARY KEY,
    document_id UUID REFERENCES documents(id),
    chunk_index INTEGER,
    content TEXT,
    embedding vector(1536),  -- OpenAI ada-002 dimension
    metadata JSONB,
    created_at TIMESTAMP
);

CREATE INDEX ON document_chunks USING hnsw (embedding vector_cosine_ops);
```

---

## Integration with Agents

### KB & Triage Agent Integration

```mermaid
graph LR
    KBTriageAgent[KB Triage Agent] --> QueryAPI[Query API]
    QueryAPI --> VectorDB[(Vector DB)]
    VectorDB --> KBTriageAgent
    KBTriageAgent --> TriageResults[Triage Results]
```

**Use Cases**:
- Semantic search for ticket resolution
- Finding similar past incidents
- Retrieving relevant knowledge articles

### Documentation Agent Integration

```mermaid
graph LR
    DocAgent[Documentation Agent] --> IngestAPI[Ingestion API]
    IngestAPI --> VectorDB[(Vector DB)]
    DocAgent --> CodeAnalysis[Code Analysis]
    CodeAnalysis --> DocGeneration[Doc Generation]
    DocGeneration --> VectorDB
```

**Use Cases**:
- Indexing code documentation
- Generating API documentation
- Creating architecture documentation

### Planning Agent Integration

```mermaid
graph LR
    PlanningAgent[Planning Agent] --> QueryAPI[Query API]
    QueryAPI --> VectorDB[(Vector DB)]
    VectorDB --> PlanningAgent
    PlanningAgent --> PlanGeneration[Plan Generation]
```

**Use Cases**:
- Retrieving deployment best practices
- Finding similar deployment scenarios
- Accessing rollback procedures

---

## Performance Considerations

### Indexing Performance
- **Batch Processing**: Process documents in batches
- **Parallel Processing**: Parallelize embedding generation
- **Incremental Updates**: Only re-index changed documents

### Query Performance
- **Vector Index**: HNSW index for fast similarity search
- **Result Caching**: Cache frequent queries
- **Limit Results**: Return top-K results (default: 10)

### Scalability
- **Horizontal Scaling**: Scale embedding service independently
- **Database Sharding**: Shard by source or category if needed
- **CDN Caching**: Cache static document content

---

## Security and Compliance

### Access Control
- **Source-Level Access**: Control access by document source
- **Category-Level Access**: Control access by document category
- **RBAC Integration**: Integrate with EUCORA RBAC system

### Data Privacy
- **PII Detection**: Detect and redact PII from documents
- **Encryption**: Encrypt documents at rest
- **Audit Logging**: Log all document access

### Compliance
- **Retention Policies**: Enforce document retention policies
- **Data Classification**: Classify documents by sensitivity
- **Compliance Reporting**: Generate compliance reports

---

## Monitoring and Observability

### Metrics
- **Ingestion Rate**: Documents ingested per hour
- **Embedding Latency**: Time to generate embeddings
- **Query Latency**: Query response time
- **Index Size**: Number of vectors in index

### Alerts
- **Ingestion Failures**: Alert on ingestion errors
- **High Query Latency**: Alert on slow queries
- **Index Health**: Alert on index issues

---

## Related Documentation

- [AI Agents Architecture](ai-agents-architecture.md)
- [ALM Agents Architecture](alm-agents-architecture.md)
- [Planning Document: Document Management & RAG](../planning/01-document-management-rag.md)
- [Planning Document: Vector Storage](../planning/07-vector-storage-pgvector.md)
