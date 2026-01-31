# E13: Automation Opportunity Advisor Agent

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P3-Medium
**Sprint**: 13-14 (Weeks 25-28)
**Dependencies**: E7 (pgvector), E8 (AI Workflows), E10 (CMDB)
**ALM L2 Category**: CSI (Continual Service Improvement)

---

## Overview

The Automation Opportunity Advisor Agent detects repetitive, manual, or error-prone tasks in IT operations and recommends automation candidates with ROI estimates. It identifies hidden automation opportunities and reduces costs and manual toil.

### Key Benefits

- Identifies hidden automation opportunities
- Reduces costs and manual toil
- Provides ROI-based prioritization
- Enables data-driven automation investments

### Data Sources

- ServiceNow (incidents, requests, changes)
- Deployment history
- User activity logs
- Process execution times

---

## Requirements

### 1. Task Pattern Analysis

**Data Collection**:
- Incident tickets (categories, resolution times, repetition)
- Service requests (frequency, manual steps)
- Change requests (manual vs automated)
- Deployment tasks (time spent, failure rates)

**Pattern Detection**:
- Repetitive task identification
- Manual bottleneck detection
- Error-prone process identification
- Time-consuming operations

### 2. Automation Scoring

**Factors**:
- Frequency of occurrence
- Time spent per occurrence
- Error rate
- Complexity of automation
- Potential ROI

**Scoring Formula**:
```
AutomationScore = (Frequency × TimePerOccurrence × ErrorRate) / AutomationComplexity
ROI = (AnnualTimeSaved × HourlyCost) - AutomationDevelopmentCost
```

### 3. Recommendation Engine

**Outputs**:
- Ranked automation candidates
- ROI estimates per candidate
- Implementation complexity assessment
- Suggested automation approaches
- Resource requirements

### 4. Integration

**Connections**:
- ServiceNow for ticket data
- EUCORA deployment history
- AI workflow execution logs
- User session analytics

---

## Data Model

### Django Models

```python
# apps/automation_advisor/models.py

class TaskPattern(TimeStampedModel):
    """Detected task patterns from operational data."""
    name = models.CharField(max_length=255)
    pattern_type = models.CharField(max_length=50)  # repetitive, manual, error_prone
    source = models.CharField(max_length=50)  # servicenow, eucora, logs
    source_query = models.JSONField()
    occurrence_count = models.IntegerField(default=0)
    avg_duration_minutes = models.FloatField(default=0)
    error_rate = models.FloatField(default=0)
    last_detected = models.DateTimeField()
    is_active = models.BooleanField(default=True)

class AutomationCandidate(TimeStampedModel, CorrelationIdModel):
    """Identified automation opportunity."""
    pattern = models.ForeignKey(TaskPattern, on_delete=models.CASCADE)
    title = models.CharField(max_length=255)
    description = models.TextField()
    current_process = models.TextField()
    proposed_automation = models.TextField()

    # Scoring
    frequency_score = models.FloatField()
    time_impact_score = models.FloatField()
    error_reduction_score = models.FloatField()
    complexity_score = models.FloatField()
    overall_score = models.FloatField()

    # ROI
    annual_occurrences = models.IntegerField()
    time_saved_per_occurrence = models.FloatField()  # hours
    estimated_annual_savings = models.DecimalField(max_digits=12, decimal_places=2)
    development_cost_estimate = models.DecimalField(max_digits=12, decimal_places=2)
    payback_period_months = models.FloatField()

    # Status
    status = models.CharField(max_length=20)  # identified, reviewed, approved, implemented, rejected
    reviewed_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    reviewed_at = models.DateTimeField(null=True)
    implementation_notes = models.TextField(null=True)

class AutomationAnalysis(TimeStampedModel, CorrelationIdModel):
    """Analysis run for automation opportunities."""
    name = models.CharField(max_length=255)
    date_range_start = models.DateField()
    date_range_end = models.DateField()
    sources_analyzed = models.JSONField()
    status = models.CharField(max_length=20)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    patterns_detected = models.IntegerField(default=0)
    candidates_generated = models.IntegerField(default=0)

class ROIConfiguration(TimeStampedModel):
    """Configuration for ROI calculations."""
    name = models.CharField(max_length=255)
    hourly_labor_cost = models.DecimalField(max_digits=10, decimal_places=2)
    development_hourly_rate = models.DecimalField(max_digits=10, decimal_places=2)
    complexity_multipliers = models.JSONField()  # low: 8h, medium: 40h, high: 160h
    is_default = models.BooleanField(default=False)
```

---

## Agent Workflow Definition

```json
{
  "name": "automation_advisor_workflow",
  "agent_type": "automation_advisor",
  "risk_level": "R1",
  "steps": [
    {
      "name": "collect_operational_data",
      "description": "Collect incident, request, and change data",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "analyze_patterns",
      "description": "Detect repetitive, manual, and error-prone patterns",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "score_candidates",
      "description": "Score automation candidates by impact and complexity",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "calculate_roi",
      "description": "Calculate ROI for each candidate",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "generate_recommendations",
      "description": "Generate ranked recommendations with approaches",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "publish_report",
      "description": "Publish automation opportunity report",
      "risk_level": "R1",
      "requires_approval": false
    }
  ],
  "policy_requirements": [
    "automation_policy",
    "roi_thresholds"
  ]
}
```

---

## API Endpoints

```
# Analyses
POST /api/automation-advisor/analyze/
GET /api/automation-advisor/analyses/
GET /api/automation-advisor/analyses/{id}/

# Patterns
GET /api/automation-advisor/patterns/
GET /api/automation-advisor/patterns/{id}/

# Candidates
GET /api/automation-advisor/candidates/
GET /api/automation-advisor/candidates/{id}/
POST /api/automation-advisor/candidates/{id}/review/
POST /api/automation-advisor/candidates/{id}/approve/
POST /api/automation-advisor/candidates/{id}/reject/

# Configuration
GET/PUT /api/automation-advisor/roi-config/

# Reports
GET /api/automation-advisor/reports/summary/
GET /api/automation-advisor/reports/export/
```

---

## Frontend Components

### 1. Automation Advisor Dashboard

```
AI Agents > Automation Advisor
├── Summary Cards
│   ├── Total opportunities
│   ├── Potential annual savings
│   ├── Pending review
│   └── Implemented
├── Top Opportunities
│   ├── Ranked list by ROI
│   ├── Quick approve/reject
│   └── View details
├── Analysis History
│   ├── Recent analyses
│   └── Run new analysis
└── ROI Configuration
    ├── Labor costs
    ├── Development rates
    └── Complexity multipliers
```

### 2. Opportunity Detail

```
Automation Opportunity: Password Reset Automation
├── Header
│   ├── Score: 87/100
│   ├── Annual Savings: $45,000
│   ├── Payback: 3.2 months
│   └── Status: Under Review
├── Current Process
│   ├── Description
│   ├── Steps (manual)
│   ├── Average time: 15 min
│   └── Occurrences: 500/month
├── Proposed Automation
│   ├── Description
│   ├── Approach
│   ├── Complexity: Medium
│   └── Development estimate: 40 hours
├── ROI Breakdown
│   ├── Time saved per occurrence
│   ├── Annual occurrences
│   ├── Labor cost saved
│   ├── Development cost
│   └── Net annual benefit
├── Evidence
│   ├── Sample incidents
│   ├── Pattern data
│   └── Supporting metrics
└── Actions
    ├── Approve
    ├── Reject
    ├── Request more info
    └── Assign for implementation
```

### 3. Analysis Configuration

```
Run New Analysis
├── Date Range
├── Data Sources
│   ├── ☑️ ServiceNow incidents
│   ├── ☑️ ServiceNow requests
│   ├── ☑️ ServiceNow changes
│   ├── ☑️ EUCORA deployments
│   └── ☐ User activity logs
├── Pattern Types
│   ├── ☑️ Repetitive tasks
│   ├── ☑️ Manual processes
│   └── ☑️ Error-prone operations
├── Thresholds
│   ├── Minimum occurrences: 10
│   ├── Minimum ROI: $5,000
│   └── Maximum complexity: High
└── Run Analysis
```

---

## Pattern Detection Algorithms

### Repetitive Task Detection

```python
def detect_repetitive_tasks(incidents: list[dict], threshold: int = 10) -> list[TaskPattern]:
    """Detect tasks that occur repeatedly with similar characteristics."""

    # Group by category + short description similarity
    # Use embeddings for semantic grouping
    # Calculate occurrence frequency
    # Filter by threshold
```

### Manual Process Detection

```python
def detect_manual_processes(tickets: list[dict]) -> list[TaskPattern]:
    """Detect processes that require manual intervention."""

    # Look for keywords: "manually", "hand-off", "wait for"
    # Identify tickets with multiple reassignments
    # Find processes with long resolution times
    # Detect patterns in work notes
```

### Error-Prone Detection

```python
def detect_error_prone(changes: list[dict], deployments: list[dict]) -> list[TaskPattern]:
    """Detect processes with high error rates."""

    # Calculate failure rates by category
    # Identify rollback patterns
    # Find tickets reopened multiple times
    # Detect failed deployments by type
```

---

## Acceptance Criteria

- [ ] ServiceNow data integration
- [ ] Pattern detection algorithms
- [ ] Automation scoring model
- [ ] ROI calculation engine
- [ ] Recommendation generation
- [ ] Dashboard with rankings
- [ ] Review and approval workflow
- [ ] Export to CSV/PDF
- [ ] ≥90% test coverage
