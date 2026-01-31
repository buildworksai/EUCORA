# E21: KB & Triage Agent

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P1-Critical
**Sprint**: 17-18 (Weeks 33-36)
**Dependencies**: E1 (Document Management), E7 (pgvector), E8 (AI Workflows)
**ALM L2 Category**: Incident Management, Problem Management

---

## Overview

The KB & Triage Agent provides contextual information for frontline desktop support resources. Its power is to synthesize large swathes of enterprise IT knowledge (both from the IT organization and vendor knowledge repositories) and provide pinpoint step-by-step instructions on how to resolve an issue.

### Key Benefits

- Reduces manual ticket creation
- Ensures consistency in categorization/prioritization
- Provides real-time reporting and early visibility to recurring issues
- Step-by-step resolution guidance
- Knowledge synthesis from multiple sources

### Data Sources

- KB articles
- SOPs (Standard Operating Procedures)
- Vendor Docs
- Compliance bulletins
- Past incidents
- ServiceNow

---

## Requirements

### 1. AI-Assisted Ticket Triage

**Capabilities**:
- Automatic categorization
- Priority recommendation
- Assignment suggestion
- Duplicate detection
- Escalation prediction

**Inputs**:
- Incident description
- Caller information
- Affected service
- Symptoms

**Outputs**:
- Category and subcategory
- Priority and urgency
- Suggested assignment group
- Related tickets
- Resolution suggestions

### 2. Knowledge Synthesis

**Sources**:
- Internal KB articles
- Vendor documentation
- SOPs and runbooks
- Past incident resolutions
- Compliance bulletins
- Community forums

**Capabilities**:
- Semantic search across sources
- Relevance ranking
- Step-by-step extraction
- Confidence scoring

### 3. Resolution Guidance

**Features**:
- Step-by-step instructions
- Decision tree navigation
- Script suggestions
- Escalation triggers
- Evidence collection

### 4. Pattern Detection

**Detection Types**:
- Recurring issues
- Trending problems
- Correlation with changes
- Impact assessment

---

## Data Model

### Django Models

```python
# apps/kb_triage/models.py

class KnowledgeSource(TimeStampedModel):
    """Configured knowledge source."""
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50)  # servicenow_kb, confluence, sharepoint, vendor, custom
    connection_config = models.JSONField()
    sync_schedule = models.CharField(max_length=50)
    last_sync = models.DateTimeField(null=True)
    article_count = models.IntegerField(default=0)
    is_active = models.BooleanField(default=True)

class KnowledgeArticle(TimeStampedModel):
    """Indexed knowledge article."""
    source = models.ForeignKey(KnowledgeSource, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=255)
    title = models.CharField(max_length=500)
    content = models.TextField()
    category = models.CharField(max_length=255, null=True)
    tags = models.JSONField(default=list)
    url = models.URLField(null=True)
    author = models.CharField(max_length=255, null=True)
    published_date = models.DateTimeField(null=True)
    last_updated = models.DateTimeField(null=True)
    view_count = models.IntegerField(default=0)
    helpful_count = models.IntegerField(default=0)

    # Embedding for semantic search
    embedding = models.JSONField(null=True)

class TriageRequest(TimeStampedModel, CorrelationIdModel):
    """Ticket triage request."""
    servicenow_number = models.CharField(max_length=50, null=True)
    caller_name = models.CharField(max_length=255)
    caller_email = models.EmailField(null=True)
    affected_service = models.CharField(max_length=255, null=True)
    short_description = models.CharField(max_length=500)
    description = models.TextField()
    symptoms = models.JSONField(default=list)

    # Triage Results
    suggested_category = models.CharField(max_length=255, null=True)
    suggested_subcategory = models.CharField(max_length=255, null=True)
    suggested_priority = models.CharField(max_length=20, null=True)
    suggested_assignment_group = models.CharField(max_length=255, null=True)
    confidence_score = models.FloatField(null=True)
    reasoning = models.TextField(null=True)

    # Status
    status = models.CharField(max_length=20)  # pending, triaged, escalated, resolved
    triage_time_ms = models.IntegerField(null=True)

class TriageSuggestion(TimeStampedModel):
    """Resolution suggestion for triage request."""
    triage_request = models.ForeignKey(TriageRequest, on_delete=models.CASCADE)
    suggestion_type = models.CharField(max_length=50)  # article, script, escalation, workaround
    title = models.CharField(max_length=500)
    content = models.TextField()
    source_article = models.ForeignKey(KnowledgeArticle, null=True, on_delete=models.SET_NULL)
    relevance_score = models.FloatField()
    was_helpful = models.BooleanField(null=True)
    feedback = models.TextField(null=True)

class ResolutionStep(TimeStampedModel):
    """Step-by-step resolution guidance."""
    triage_request = models.ForeignKey(TriageRequest, on_delete=models.CASCADE)
    step_number = models.IntegerField()
    instruction = models.TextField()
    expected_outcome = models.TextField(null=True)
    script = models.TextField(null=True)
    script_type = models.CharField(max_length=20, null=True)
    requires_approval = models.BooleanField(default=False)
    status = models.CharField(max_length=20)  # pending, completed, skipped, failed
    completed_at = models.DateTimeField(null=True)
    notes = models.TextField(null=True)

class IncidentPattern(TimeStampedModel, CorrelationIdModel):
    """Detected incident pattern."""
    name = models.CharField(max_length=255)
    pattern_type = models.CharField(max_length=50)  # recurring, trending, correlated
    description = models.TextField()
    category = models.CharField(max_length=255)
    occurrence_count = models.IntegerField()
    affected_users = models.IntegerField()
    first_detected = models.DateTimeField()
    last_detected = models.DateTimeField()
    related_change = models.CharField(max_length=100, null=True)
    status = models.CharField(max_length=20)  # active, investigating, resolved
    root_cause = models.TextField(null=True)
    resolution = models.TextField(null=True)

class TriageFeedback(TimeStampedModel):
    """Feedback on triage accuracy."""
    triage_request = models.ForeignKey(TriageRequest, on_delete=models.CASCADE)
    feedback_type = models.CharField(max_length=50)  # category, priority, assignment, resolution
    was_accurate = models.BooleanField()
    correct_value = models.CharField(max_length=255, null=True)
    comments = models.TextField(null=True)
    submitted_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True)
```

---

## Agent Workflow Definition

```json
{
  "name": "kb_triage_workflow",
  "agent_type": "kb_triage",
  "risk_level": "R1",
  "steps": [
    {
      "name": "parse_incident",
      "description": "Parse incident description and extract key information",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "search_knowledge",
      "description": "Search knowledge base for relevant articles",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "categorize_incident",
      "description": "Determine category and subcategory",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "assess_priority",
      "description": "Assess priority and urgency",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "check_duplicates",
      "description": "Check for duplicate or related incidents",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "generate_resolution",
      "description": "Generate step-by-step resolution guidance",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "suggest_assignment",
      "description": "Suggest assignment group",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "detect_patterns",
      "description": "Check for incident patterns",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "present_triage",
      "description": "Present triage results to agent",
      "risk_level": "R1",
      "requires_approval": false
    }
  ],
  "policy_requirements": [
    "incident_management_policy"
  ]
}
```

---

## Triage Algorithm

```python
class TicketTriageEngine:
    """AI-powered ticket triage engine."""

    def __init__(self, knowledge_service: KnowledgeRetrievalService):
        self.knowledge = knowledge_service

    async def triage(self, request: TriageRequest) -> TriageResult:
        """Perform AI-assisted ticket triage."""

        # 1. Extract key information
        entities = await self.extract_entities(request.description)

        # 2. Search knowledge base
        kb_results = await self.knowledge.semantic_search(
            query=request.short_description,
            filters={'type': ['kb_article', 'sop', 'past_incident']},
            limit=10
        )

        # 3. Determine category
        category, subcategory, confidence = await self.categorize(
            description=request.description,
            entities=entities,
            kb_context=kb_results
        )

        # 4. Assess priority
        priority = await self.assess_priority(
            description=request.description,
            category=category,
            affected_service=request.affected_service
        )

        # 5. Check for duplicates
        duplicates = await self.find_duplicates(
            description=request.description,
            category=category,
            timeframe_hours=72
        )

        # 6. Generate resolution steps
        resolution_steps = await self.generate_resolution(
            description=request.description,
            kb_results=kb_results,
            category=category
        )

        # 7. Suggest assignment
        assignment = await self.suggest_assignment(
            category=category,
            priority=priority,
            resolution_complexity=len(resolution_steps)
        )

        return TriageResult(
            category=category,
            subcategory=subcategory,
            priority=priority,
            assignment=assignment,
            duplicates=duplicates,
            resolution_steps=resolution_steps,
            kb_articles=kb_results,
            confidence=confidence
        )

    async def categorize(
        self,
        description: str,
        entities: dict,
        kb_context: list
    ) -> tuple[str, str, float]:
        """Categorize incident using LLM."""
        prompt = f"""
        Categorize this IT incident:

        Description: {description}
        Entities: {entities}

        Similar KB articles:
        {self._format_kb_context(kb_context)}

        Return JSON:
        {{
            "category": "string",
            "subcategory": "string",
            "confidence": 0.0-1.0,
            "reasoning": "string"
        }}
        """

        response = await self.llm.generate(prompt)
        return response['category'], response['subcategory'], response['confidence']
```

---

## API Endpoints

```
# Knowledge Sources
GET/POST /api/kb-triage/sources/
POST /api/kb-triage/sources/{id}/sync/

# Knowledge Articles
GET /api/kb-triage/articles/
POST /api/kb-triage/articles/search/

# Triage
POST /api/kb-triage/triage/
GET /api/kb-triage/triage/{id}/
GET /api/kb-triage/triage/{id}/suggestions/
GET /api/kb-triage/triage/{id}/resolution-steps/
POST /api/kb-triage/triage/{id}/feedback/

# Patterns
GET /api/kb-triage/patterns/
GET /api/kb-triage/patterns/{id}/
POST /api/kb-triage/patterns/{id}/investigate/

# Analytics
GET /api/kb-triage/analytics/accuracy/
GET /api/kb-triage/analytics/categories/
GET /api/kb-triage/analytics/patterns/
```

---

## Frontend Components

### 1. KB & Triage Dashboard

```
AI Agents > KB & Triage
├── Triage Queue
│   ├── Pending triage
│   ├── Recently triaged
│   └── Quick triage input
├── Knowledge Search
│   ├── Semantic search bar
│   ├── Results with relevance
│   └── Article preview
├── Pattern Detection
│   ├── Active patterns
│   ├── Trending issues
│   └── Correlation alerts
├── Analytics
│   ├── Triage accuracy
│   ├── Category distribution
│   ├── Resolution time
│   └── KB effectiveness
└── Knowledge Sources
    ├── Configured sources
    ├── Sync status
    └── Article counts
```

### 2. Triage Interface

```
Triage: INC0012345 - Outlook not syncing
├── Incident Details
│   ├── Caller: John Smith
│   ├── Description: Outlook emails not syncing...
│   └── Affected service: Email
├── AI Triage Results
│   ├── Category: Email > Synchronization
│   ├── Priority: Medium
│   ├── Assignment: Email Support
│   └── Confidence: 94%
├── Related Knowledge
│   ├── KB0001234: Outlook sync troubleshooting
│   ├── KB0002345: Exchange connectivity issues
│   └── View more
├── Resolution Steps
│   ├── 1. Check network connectivity
│   ├── 2. Verify Exchange server status
│   ├── 3. Clear Outlook cache
│   ├── 4. Repair Office installation
│   └── 5. Escalate if unresolved
├── Related Incidents
│   ├── INC0012340 (similar, resolved)
│   ├── INC0012341 (duplicate?)
│   └── Pattern detected: 5 similar today
└── Actions
    ├── Accept triage
    ├── Modify and accept
    ├── Execute resolution
    └── Escalate
```

### 3. Knowledge Search

```
Knowledge Search
├── Search Bar
│   ├── Natural language query
│   ├── Filters (source, category, date)
│   └── Search button
├── Results
│   ├── Article cards
│   │   ├── Title
│   │   ├── Relevance score
│   │   ├── Source badge
│   │   ├── Snippet
│   │   └── View article
│   └── Pagination
└── Article Preview
    ├── Full content
    ├── Related articles
    ├── Was this helpful?
    └── Use for triage
```

---

## Acceptance Criteria

- [ ] Knowledge source integration (ServiceNow KB, Confluence)
- [ ] Semantic search across sources
- [ ] Automatic categorization
- [ ] Priority assessment
- [ ] Duplicate detection
- [ ] Step-by-step resolution generation
- [ ] Assignment suggestion
- [ ] Pattern detection
- [ ] Feedback loop for accuracy improvement
- [ ] Real-time triage UI
- [ ] ≥90% test coverage
