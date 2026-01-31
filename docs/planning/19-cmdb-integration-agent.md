# E10: CMDB Integration Agent

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P2-High
**Sprint**: 11-12 (Weeks 21-24)
**Dependencies**: E7 (pgvector), E8 (AI Workflows)
**ALM L2 Category**: Service Configuration Management

---

## Overview

The CMDB Data Maintenance & Validation Agent keeps CMDB fields (including AMS-specific ones) up to date by auto-ingesting data from discovery tools, monitoring systems, and deployment pipelines. It flags missing or inconsistent data for review.

### Key Benefits

- Reduces manual CMDB entry
- Improves data quality and audit readiness
- Frees humans from repetitive update tasks

### Data Sources

- ServiceNow Discovery
- SCCM
- Intune
- Deployment pipelines
- Monitoring systems

---

## Requirements

### 1. CMDB Connection Configuration

**Admin Settings**:
- ServiceNow CMDB connection (instance URL, credentials, table mappings)
- Field mapping configuration (source → CMDB attribute)
- Sync schedule (hourly, daily, on-demand)
- Validation rules configuration

### 2. Data Ingestion

**Sources**:
- ServiceNow Discovery patterns
- SCCM hardware/software inventory
- Intune device compliance
- Deployment events from Control Plane
- Monitoring alerts (status changes)

**Processing**:
- Normalize data across sources
- Deduplicate records
- Detect conflicts between sources
- Apply business rules for precedence

### 3. Validation Engine

**Rules**:
- Required field completeness
- Data type validation
- Referential integrity (CI relationships)
- Business logic rules (e.g., status transitions)
- AMS-specific field requirements

**Outputs**:
- Validation reports
- Data quality scores
- Exception lists for review

### 4. Agent Workflows

**R1 Operations (Autonomous)**:
- Read CMDB data
- Compare with source systems
- Generate discrepancy reports

**R2 Operations (Approval Required)**:
- Update existing CI attributes
- Add missing relationships
- Correct data quality issues

**R3 Operations (Mandatory Approval)**:
- Create new CIs
- Delete/retire CIs
- Bulk updates

---

## Data Model

### Django Models

```python
# apps/cmdb_integration/models.py

class CMDBConnection(TimeStampedModel):
    """ServiceNow CMDB connection configuration."""
    name = models.CharField(max_length=255)
    instance_url = models.URLField()
    auth_type = models.CharField(max_length=50)  # basic, oauth, api_key
    credentials = models.JSONField()  # encrypted
    is_active = models.BooleanField(default=True)
    last_sync = models.DateTimeField(null=True)

class CMDBTableMapping(TimeStampedModel):
    """Mapping between source and CMDB tables."""
    connection = models.ForeignKey(CMDBConnection, on_delete=models.CASCADE)
    source_type = models.CharField(max_length=50)  # sccm, intune, discovery
    source_table = models.CharField(max_length=255)
    cmdb_table = models.CharField(max_length=255)
    field_mappings = models.JSONField()
    sync_enabled = models.BooleanField(default=True)

class CMDBValidationRule(TimeStampedModel):
    """Validation rules for CMDB data."""
    name = models.CharField(max_length=255)
    cmdb_table = models.CharField(max_length=255)
    rule_type = models.CharField(max_length=50)  # required, format, reference, custom
    rule_config = models.JSONField()
    severity = models.CharField(max_length=20)  # error, warning, info
    is_active = models.BooleanField(default=True)

class CMDBSyncRecord(TimeStampedModel, CorrelationIdModel):
    """Record of CMDB sync operations."""
    connection = models.ForeignKey(CMDBConnection, on_delete=models.CASCADE)
    sync_type = models.CharField(max_length=50)  # full, incremental, targeted
    status = models.CharField(max_length=20)  # pending, running, completed, failed
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    records_processed = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    errors = models.JSONField(default=list)

class CMDBDiscrepancy(TimeStampedModel):
    """Detected discrepancies between sources and CMDB."""
    sync_record = models.ForeignKey(CMDBSyncRecord, on_delete=models.CASCADE)
    ci_sys_id = models.CharField(max_length=100)
    ci_name = models.CharField(max_length=255)
    discrepancy_type = models.CharField(max_length=50)  # missing, mismatch, orphan
    field_name = models.CharField(max_length=255)
    source_value = models.TextField(null=True)
    cmdb_value = models.TextField(null=True)
    recommended_action = models.CharField(max_length=50)
    status = models.CharField(max_length=20)  # pending, approved, rejected, applied
    resolved_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL)
    resolved_at = models.DateTimeField(null=True)
```

---

## Agent Workflow Definition

```json
{
  "name": "cmdb_maintenance_workflow",
  "agent_type": "cmdb_maintenance",
  "risk_level": "R2",
  "steps": [
    {
      "name": "collect_source_data",
      "description": "Collect data from all configured sources",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "compare_with_cmdb",
      "description": "Compare source data with current CMDB state",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "identify_discrepancies",
      "description": "Identify and categorize all discrepancies",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "validate_changes",
      "description": "Validate proposed changes against business rules",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "apply_updates",
      "description": "Apply approved updates to CMDB",
      "risk_level": "R2",
      "requires_approval": true,
      "approval_context": "Review discrepancy list and confirm updates"
    },
    {
      "name": "generate_report",
      "description": "Generate sync report with quality metrics",
      "risk_level": "R1",
      "requires_approval": false
    }
  ],
  "policy_requirements": [
    "cmdb_update_policy",
    "data_quality_standards"
  ]
}
```

---

## API Endpoints

```
# Connection Management
GET/POST /api/cmdb/connections/
GET/PUT/DELETE /api/cmdb/connections/{id}/
POST /api/cmdb/connections/{id}/test/

# Table Mappings
GET/POST /api/cmdb/mappings/
GET/PUT/DELETE /api/cmdb/mappings/{id}/

# Validation Rules
GET/POST /api/cmdb/validation-rules/
GET/PUT/DELETE /api/cmdb/validation-rules/{id}/

# Sync Operations
POST /api/cmdb/sync/
GET /api/cmdb/sync/{id}/
GET /api/cmdb/sync/{id}/discrepancies/

# Discrepancy Management
GET /api/cmdb/discrepancies/
POST /api/cmdb/discrepancies/{id}/approve/
POST /api/cmdb/discrepancies/{id}/reject/
POST /api/cmdb/discrepancies/bulk-approve/

# Reports
GET /api/cmdb/reports/quality-score/
GET /api/cmdb/reports/sync-history/
```

---

## Frontend Components

### 1. CMDB Integration Settings (Admin)

```
Settings > Integrations > CMDB
├── Connection Configuration
│   ├── ServiceNow instance URL
│   ├── Authentication setup
│   └── Connection test
├── Table Mappings
│   ├── Source selection (SCCM, Intune, Discovery)
│   ├── Field mapping editor
│   └── Sync schedule
└── Validation Rules
    ├── Rule list
    ├── Rule editor
    └── Test rule
```

### 2. CMDB Agent Dashboard

```
AI Agents > CMDB Maintenance
├── Quality Score Gauge
├── Recent Sync History
├── Discrepancy Queue
│   ├── Pending count by type
│   ├── Quick approve/reject
│   └── Bulk actions
├── Data Quality Trends
└── Start Sync Button
```

### 3. Discrepancy Review Interface

```
Discrepancies List
├── Filters (type, severity, table, date)
├── Discrepancy Cards
│   ├── CI name and sys_id
│   ├── Field with mismatch
│   ├── Source value vs CMDB value
│   ├── Recommended action
│   └── Approve/Reject buttons
└── Bulk Selection & Actions
```

---

## ServiceNow Integration

### Table API Client

```python
class ServiceNowCMDBClient:
    """Client for ServiceNow CMDB Table API."""

    def __init__(self, instance_url: str, auth: dict):
        self.instance_url = instance_url
        self.session = self._create_session(auth)

    async def get_ci(self, table: str, sys_id: str) -> dict:
        """Get a single CI by sys_id."""

    async def query_cis(self, table: str, query: str, limit: int = 1000) -> list[dict]:
        """Query CIs with encoded query string."""

    async def create_ci(self, table: str, data: dict) -> dict:
        """Create a new CI."""

    async def update_ci(self, table: str, sys_id: str, data: dict) -> dict:
        """Update an existing CI."""

    async def get_relationships(self, ci_sys_id: str) -> list[dict]:
        """Get CI relationships."""
```

### Common CMDB Tables

| Table | Description |
|-------|-------------|
| cmdb_ci_computer | Computers/Servers |
| cmdb_ci_pc_hardware | Desktops/Laptops |
| cmdb_ci_server | Servers |
| cmdb_ci_app_server | Application Servers |
| cmdb_ci_appl | Applications |
| cmdb_ci_service | Business Services |
| cmdb_rel_ci | CI Relationships |

---

## Acceptance Criteria

- [ ] ServiceNow CMDB connection configurable
- [ ] Field mappings for SCCM, Intune, Discovery
- [ ] Validation rules engine functional
- [ ] Discrepancy detection accurate
- [ ] Approval workflow for R2/R3 operations
- [ ] Data quality scoring implemented
- [ ] Audit trail for all CMDB changes
- [ ] ≥90% test coverage
