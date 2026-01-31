# E12: Documentation Agent

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P3-Medium
**Sprint**: 13-14 (Weeks 25-28)
**Dependencies**: E1 (Document Management), E7 (pgvector), E8 (AI Workflows)
**ALM L2 Category**: Knowledge Management, Test Management

---

## Overview

The Documentation Agent automatically generates comprehensive documentation from GitHub repositories or local codebases. It uses a multi-stage workflow to intelligently analyze code structure, identifies key abstractions, modular patterns, and explains relationships across components for comprehension.

### Key Benefits

- Automates regression testing documentation
- Builds comprehensive technical documentation for KT purposes
- Improves operational efficiency
- Ensures compliance to standards

### Data Sources

- Git repos
- Co-pilot tools
- MCP servers
- ServiceNow KB articles
- Vendor documentation
- External websites

---

## Requirements

### 1. Code Analysis Engine

**Supported Languages**:
- Python (Django apps)
- TypeScript/JavaScript (React)
- PowerShell
- SQL

**Analysis Capabilities**:
- Module/package structure
- Class hierarchies
- Function signatures
- API endpoints
- Database models
- Dependencies

### 2. Documentation Generation

**Output Types**:
- API documentation (OpenAPI/Swagger)
- Module documentation (README.md)
- Architecture diagrams (Mermaid)
- Runbooks
- Test documentation
- Compliance evidence

### 3. Knowledge Synthesis

**Integration Points**:
- Link to relevant KB articles
- Cross-reference vendor docs
- Connect to policy documents (E1)
- Index in vector store (E7)

### 4. Quality & Compliance

**Standards**:
- Follows EUCORA documentation standards
- Generates ADRs for architectural decisions
- Produces compliance evidence packs
- Maintains version history

---

## Data Model

### Django Models

```python
# apps/documentation_agent/models.py

class CodeRepository(TimeStampedModel):
    """Configured code repositories for documentation."""
    name = models.CharField(max_length=255)
    repo_type = models.CharField(max_length=20)  # github, gitlab, local
    url = models.URLField(null=True)
    local_path = models.CharField(max_length=500, null=True)
    default_branch = models.CharField(max_length=100, default='main')
    auth_config = models.JSONField(null=True)
    last_analyzed = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

class CodeAnalysis(TimeStampedModel, CorrelationIdModel):
    """Analysis run on a repository."""
    repository = models.ForeignKey(CodeRepository, on_delete=models.CASCADE)
    commit_sha = models.CharField(max_length=40)
    branch = models.CharField(max_length=100)
    status = models.CharField(max_length=20)  # pending, running, completed, failed
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    summary = models.JSONField(null=True)  # modules, classes, functions counts
    errors = models.JSONField(default=list)

class DocumentedModule(TimeStampedModel):
    """Analyzed and documented code module."""
    analysis = models.ForeignKey(CodeAnalysis, on_delete=models.CASCADE)
    module_path = models.CharField(max_length=500)
    module_type = models.CharField(max_length=50)  # package, module, class, function
    name = models.CharField(max_length=255)
    docstring = models.TextField(null=True)
    generated_doc = models.TextField(null=True)
    signature = models.TextField(null=True)
    dependencies = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)

class GeneratedDocument(TimeStampedModel, CorrelationIdModel):
    """Generated documentation artifacts."""
    analysis = models.ForeignKey(CodeAnalysis, on_delete=models.CASCADE)
    doc_type = models.CharField(max_length=50)  # api, readme, architecture, runbook, adr
    title = models.CharField(max_length=255)
    content = models.TextField()
    format = models.CharField(max_length=20)  # markdown, openapi, mermaid
    target_path = models.CharField(max_length=500, null=True)
    status = models.CharField(max_length=20)  # draft, review, published
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    published_at = models.DateTimeField(null=True)

class DocumentationTemplate(TimeStampedModel):
    """Templates for documentation generation."""
    name = models.CharField(max_length=255)
    doc_type = models.CharField(max_length=50)
    template_content = models.TextField()
    variables = models.JSONField(default=list)
    is_active = models.BooleanField(default=True)
```

---

## Agent Workflow Definition

```json
{
  "name": "documentation_generation_workflow",
  "agent_type": "documentation",
  "risk_level": "R1",
  "steps": [
    {
      "name": "fetch_repository",
      "description": "Clone or pull latest from repository",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "analyze_structure",
      "description": "Analyze code structure and dependencies",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "extract_docstrings",
      "description": "Extract existing documentation and comments",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "identify_patterns",
      "description": "Identify architectural patterns and abstractions",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "generate_documentation",
      "description": "Generate documentation using templates and LLM",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "review_quality",
      "description": "Review generated documentation quality",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "publish_documentation",
      "description": "Publish documentation to target location",
      "risk_level": "R2",
      "requires_approval": true,
      "approval_context": "Review generated documentation before publishing"
    },
    {
      "name": "index_in_knowledge_base",
      "description": "Index documentation in vector store for RAG",
      "risk_level": "R1",
      "requires_approval": false
    }
  ],
  "policy_requirements": [
    "documentation_standards"
  ]
}
```

---

## API Endpoints

```
# Repositories
GET/POST /api/documentation/repositories/
GET/PUT/DELETE /api/documentation/repositories/{id}/
POST /api/documentation/repositories/{id}/analyze/

# Analyses
GET /api/documentation/analyses/
GET /api/documentation/analyses/{id}/
GET /api/documentation/analyses/{id}/modules/

# Generated Documents
GET /api/documentation/documents/
GET /api/documentation/documents/{id}/
POST /api/documentation/documents/{id}/review/
POST /api/documentation/documents/{id}/publish/

# Templates
GET/POST /api/documentation/templates/
GET/PUT/DELETE /api/documentation/templates/{id}/

# Generation
POST /api/documentation/generate/
POST /api/documentation/generate/api-docs/
POST /api/documentation/generate/runbook/
POST /api/documentation/generate/adr/
```

---

## Frontend Components

### 1. Documentation Dashboard

```
AI Agents > Documentation
├── Repositories
│   ├── Configured repos
│   ├── Add repository
│   └── Analysis history
├── Generated Documents
│   ├── Recent documents
│   ├── Pending review
│   └── Published
├── Templates
│   ├── API documentation
│   ├── Module README
│   ├── Runbook
│   └── ADR
└── Quick Actions
    ├── Analyze repository
    ├── Generate API docs
    └── Generate runbook
```

### 2. Analysis Results

```
Analysis #123 - backend/apps/rbac
├── Summary
│   ├── Modules: 5
│   ├── Classes: 12
│   ├── Functions: 45
│   └── Endpoints: 8
├── Module Tree
│   ├── models.py
│   ├── serializers.py
│   ├── views.py
│   └── ...
├── Dependencies Graph (Mermaid)
├── Generated Documents
│   ├── README.md (draft)
│   ├── API.md (draft)
│   └── ARCHITECTURE.md (draft)
└── Actions
    ├── Regenerate
    ├── Review & Publish
    └── Export
```

### 3. Document Editor

```
Document: RBAC API Documentation
├── Preview pane (markdown rendered)
├── Edit pane (raw markdown)
├── Variables used
├── Linked modules
├── Actions
│   ├── Regenerate section
│   ├── Save draft
│   ├── Request review
│   └── Publish
└── Version history
```

---

## Code Analysis Patterns

### Python/Django Analysis

```python
class DjangoCodeAnalyzer:
    """Analyzes Django applications."""

    def analyze_models(self, module_path: str) -> list[ModelInfo]:
        """Extract model definitions with fields and relationships."""

    def analyze_views(self, module_path: str) -> list[ViewInfo]:
        """Extract view/viewset definitions with endpoints."""

    def analyze_serializers(self, module_path: str) -> list[SerializerInfo]:
        """Extract serializer definitions with fields."""

    def extract_api_endpoints(self, urls_path: str) -> list[EndpointInfo]:
        """Extract API endpoints from URL configuration."""
```

### TypeScript/React Analysis

```python
class ReactCodeAnalyzer:
    """Analyzes React/TypeScript applications."""

    def analyze_components(self, dir_path: str) -> list[ComponentInfo]:
        """Extract React component definitions."""

    def analyze_hooks(self, dir_path: str) -> list[HookInfo]:
        """Extract custom hooks."""

    def analyze_types(self, dir_path: str) -> list[TypeInfo]:
        """Extract TypeScript type definitions."""

    def extract_routes(self, app_path: str) -> list[RouteInfo]:
        """Extract route definitions."""
```

---

## Documentation Templates

### API Documentation Template

```markdown
# ${module_name} API

## Overview
${module_description}

## Endpoints

${for endpoint in endpoints}
### ${endpoint.method} ${endpoint.path}

${endpoint.description}

**Request:**
${endpoint.request_schema}

**Response:**
${endpoint.response_schema}

**Example:**
\`\`\`json
${endpoint.example}
\`\`\`

${endfor}

## Models

${for model in models}
### ${model.name}

${model.description}

| Field | Type | Description |
|-------|------|-------------|
${for field in model.fields}
| ${field.name} | ${field.type} | ${field.description} |
${endfor}

${endfor}
```

---

## Acceptance Criteria

- [ ] Repository configuration working
- [ ] Python/Django code analysis
- [ ] TypeScript/React code analysis
- [ ] API documentation generation
- [ ] README generation
- [ ] Architecture diagram generation
- [ ] Document review workflow
- [ ] Publishing to target locations
- [ ] Knowledge base indexing
- [ ] ≥90% test coverage
