# E14: Discovery Agent (Enhanced Portfolio)

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P2-High
**Sprint**: 11-12 (Weeks 21-24)
**Dependencies**: E3 (RBAC), E7 (pgvector)
**ALM L2 Category**: CSI (Continual Service Improvement)

---

## Overview

The Discovery Agent reads inputs from datasets (or via APIs) from application repository sources. It produces a report that details applications in the Enterprise IT landscape that are both managed and unmanaged, applications that are missing licenses, and applications that need mandatory upgrades and patches.

### Key Benefits

- Improved decision-making for lifecycle planning
- Operational efficiency through automated discovery
- Complete visibility into application landscape
- License compliance risk reduction

### Data Sources

- Spreadsheets (Excel imports)
- SCCM inventory
- Intune device reports
- CMDB
- Active Directory

---

## Requirements

### 1. Multi-Source Discovery

**Data Sources**:
- SCCM software inventory
- Intune installed apps
- Active Directory computer/user objects
- ServiceNow CMDB applications
- Excel/CSV imports (manual uploads)
- Network scanning results

**Discovery Types**:
- Software inventory
- Hardware inventory
- User-app associations
- License assignments

### 2. Application Normalization

**Challenges**:
- Same app with different names across sources
- Version format variations
- Publisher name variations
- Duplicate detection

**Normalization Engine**:
- Name matching algorithms
- Publisher normalization
- Version parsing and comparison
- Fingerprinting for deduplication

### 3. Gap Analysis

**Analysis Types**:
- Managed vs unmanaged applications
- Licensed vs unlicensed software
- Patched vs unpatched applications
- Compliant vs non-compliant devices

### 4. Reporting

**Report Types**:
- Application inventory report
- License gap report
- Patch compliance report
- Shadow IT report
- Risk assessment report

---

## Data Model

### Django Models

```python
# apps/discovery_agent/models.py

class DiscoverySource(TimeStampedModel):
    """Configured discovery data sources."""
    name = models.CharField(max_length=255)
    source_type = models.CharField(max_length=50)  # sccm, intune, ad, cmdb, spreadsheet
    connection_config = models.JSONField()
    sync_schedule = models.CharField(max_length=50)  # hourly, daily, weekly, manual
    last_sync = models.DateTimeField(null=True)
    is_active = models.BooleanField(default=True)

class DiscoveryRun(TimeStampedModel, CorrelationIdModel):
    """Record of discovery execution."""
    source = models.ForeignKey(DiscoverySource, on_delete=models.CASCADE)
    run_type = models.CharField(max_length=20)  # full, incremental
    status = models.CharField(max_length=20)
    started_at = models.DateTimeField()
    completed_at = models.DateTimeField(null=True)
    records_discovered = models.IntegerField(default=0)
    records_new = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    errors = models.JSONField(default=list)

class DiscoveredApplication(TimeStampedModel):
    """Raw discovered application from source."""
    discovery_run = models.ForeignKey(DiscoveryRun, on_delete=models.CASCADE)
    source_id = models.CharField(max_length=255)
    raw_name = models.CharField(max_length=500)
    raw_publisher = models.CharField(max_length=255, null=True)
    raw_version = models.CharField(max_length=100, null=True)
    install_date = models.DateField(null=True)
    install_count = models.IntegerField(default=1)
    source_metadata = models.JSONField(default=dict)

    # Normalization linkage
    normalized_app = models.ForeignKey('NormalizedApplication', null=True, on_delete=models.SET_NULL)
    normalization_confidence = models.FloatField(null=True)

class NormalizedApplication(TimeStampedModel):
    """Normalized/canonical application record."""
    name = models.CharField(max_length=255)
    publisher = models.CharField(max_length=255)
    category = models.CharField(max_length=100, null=True)
    application_type = models.CharField(max_length=50)  # desktop, web, mobile, saas

    # Status
    is_managed = models.BooleanField(default=False)
    is_approved = models.BooleanField(default=False)
    is_restricted = models.BooleanField(default=False)

    # Linkages
    portfolio_app = models.ForeignKey('application_portfolio.Application', null=True, on_delete=models.SET_NULL)
    license_sku = models.ForeignKey('license_management.SKU', null=True, on_delete=models.SET_NULL)

    # Fingerprint for deduplication
    fingerprint = models.CharField(max_length=64, unique=True)

class ApplicationVersion(TimeStampedModel):
    """Version of a normalized application."""
    application = models.ForeignKey(NormalizedApplication, on_delete=models.CASCADE)
    version = models.CharField(max_length=100)
    release_date = models.DateField(null=True)
    end_of_life = models.DateField(null=True)
    has_security_updates = models.BooleanField(default=True)
    is_current = models.BooleanField(default=False)
    install_count = models.IntegerField(default=0)

class LicenseGap(TimeStampedModel, CorrelationIdModel):
    """Identified license compliance gaps."""
    application = models.ForeignKey(NormalizedApplication, on_delete=models.CASCADE)
    gap_type = models.CharField(max_length=50)  # missing_license, over_deployment, under_licensed
    detected_installs = models.IntegerField()
    licensed_count = models.IntegerField()
    gap_count = models.IntegerField()
    risk_level = models.CharField(max_length=20)
    estimated_cost = models.DecimalField(max_digits=12, decimal_places=2, null=True)
    status = models.CharField(max_length=20)  # open, acknowledged, resolved

class PatchGap(TimeStampedModel, CorrelationIdModel):
    """Identified patch/update gaps."""
    application = models.ForeignKey(NormalizedApplication, on_delete=models.CASCADE)
    current_version = models.ForeignKey(ApplicationVersion, on_delete=models.CASCADE, related_name='patch_gaps_current')
    target_version = models.ForeignKey(ApplicationVersion, on_delete=models.CASCADE, related_name='patch_gaps_target')
    affected_devices = models.IntegerField()
    gap_type = models.CharField(max_length=50)  # security_patch, major_upgrade, eol_version
    severity = models.CharField(max_length=20)
    status = models.CharField(max_length=20)
```

---

## Agent Workflow Definition

```json
{
  "name": "discovery_workflow",
  "agent_type": "discovery",
  "risk_level": "R1",
  "steps": [
    {
      "name": "collect_from_sources",
      "description": "Collect application data from all configured sources",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "normalize_applications",
      "description": "Normalize discovered applications to canonical forms",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "detect_shadow_it",
      "description": "Identify unmanaged/unapproved applications",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "analyze_license_gaps",
      "description": "Compare installed apps against license entitlements",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "analyze_patch_gaps",
      "description": "Identify applications needing updates or patches",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "generate_reports",
      "description": "Generate discovery and gap analysis reports",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "recommend_actions",
      "description": "Recommend remediation actions for gaps",
      "risk_level": "R2",
      "requires_approval": true,
      "approval_context": "Review recommended actions before execution"
    }
  ],
  "policy_requirements": [
    "software_management_policy",
    "license_compliance_policy"
  ]
}
```

---

## API Endpoints

```
# Discovery Sources
GET/POST /api/discovery/sources/
GET/PUT/DELETE /api/discovery/sources/{id}/
POST /api/discovery/sources/{id}/sync/
POST /api/discovery/sources/{id}/upload/  # for spreadsheets

# Discovery Runs
GET /api/discovery/runs/
GET /api/discovery/runs/{id}/
GET /api/discovery/runs/{id}/applications/

# Normalized Applications
GET /api/discovery/applications/
GET /api/discovery/applications/{id}/
PUT /api/discovery/applications/{id}/  # manual corrections
POST /api/discovery/applications/merge/  # merge duplicates

# Gaps
GET /api/discovery/license-gaps/
GET /api/discovery/patch-gaps/
POST /api/discovery/gaps/{id}/acknowledge/
POST /api/discovery/gaps/{id}/resolve/

# Reports
GET /api/discovery/reports/inventory/
GET /api/discovery/reports/shadow-it/
GET /api/discovery/reports/license-compliance/
GET /api/discovery/reports/patch-compliance/
POST /api/discovery/reports/export/
```

---

## Frontend Components

### 1. Discovery Dashboard

```
AI Agents > Discovery
├── Summary Cards
│   ├── Total applications
│   ├── Managed vs unmanaged
│   ├── License gaps
│   └── Patch gaps
├── Application Inventory
│   ├── Search and filter
│   ├── Application cards
│   └── Bulk actions
├── Gap Analysis
│   ├── License compliance chart
│   ├── Patch status chart
│   └── Risk distribution
├── Discovery Sources
│   ├── Configured sources
│   ├── Sync status
│   └── Add source
└── Reports
    ├── Generate report
    └── Recent reports
```

### 2. Application Detail

```
Application: Microsoft Office 365
├── Header
│   ├── Status badges (managed, licensed, current)
│   └── Quick actions
├── Summary
│   ├── Publisher: Microsoft
│   ├── Category: Productivity
│   ├── Installations: 5,432
│   └── Versions in use: 3
├── Versions
│   ├── Version 16.0.14326 (3,200 installs) ✓ Current
│   ├── Version 16.0.13901 (1,800 installs) ⚠️ Update available
│   └── Version 16.0.12527 (432 installs) 🔴 EOL
├── License Status
│   ├── Entitled: 5,000
│   ├── Installed: 5,432
│   └── Gap: 432 over-deployed
├── Source Data
│   ├── SCCM: 5,200 devices
│   ├── Intune: 4,800 devices
│   └── Discrepancies
└── Actions
    ├── Create deployment
    ├── Create license request
    └── Mark as managed
```

### 3. Shadow IT Report

```
Shadow IT Applications
├── Filters
│   ├── Category
│   ├── Risk level
│   ├── Install count threshold
│   └── Date range
├── Applications Grid
│   ├── Name
│   ├── Publisher
│   ├── Install count
│   ├── First seen
│   ├── Risk score
│   └── Actions (approve, block, investigate)
├── Charts
│   ├── Shadow IT by category
│   ├── Trend over time
│   └── Top publishers
└── Export options
```

---

## Normalization Algorithms

### Name Matching

```python
class ApplicationNormalizer:
    """Normalizes discovered application names."""

    def normalize_name(self, raw_name: str) -> str:
        """Normalize application name for matching."""
        # Remove version numbers
        # Standardize separators
        # Handle common abbreviations
        # Remove architecture suffixes (x64, x86)

    def calculate_similarity(self, name1: str, name2: str) -> float:
        """Calculate similarity score between names."""
        # Use embedding-based similarity
        # Combine with fuzzy string matching

    def find_matches(self, discovered: DiscoveredApplication) -> list[tuple[NormalizedApplication, float]]:
        """Find potential matches for a discovered app."""
        # Query normalized apps
        # Calculate similarity scores
        # Return ranked matches
```

### Fingerprint Generation

```python
def generate_fingerprint(name: str, publisher: str) -> str:
    """Generate unique fingerprint for deduplication."""
    normalized_name = normalize_name(name)
    normalized_publisher = normalize_publisher(publisher)
    combined = f"{normalized_publisher}::{normalized_name}"
    return hashlib.sha256(combined.encode()).hexdigest()[:64]
```

---

## Acceptance Criteria

- [ ] SCCM inventory integration
- [ ] Intune apps integration
- [ ] Spreadsheet upload
- [ ] Application normalization
- [ ] Shadow IT detection
- [ ] License gap analysis
- [ ] Patch gap analysis
- [ ] Report generation
- [ ] Remediation recommendations
- [ ] ≥90% test coverage
