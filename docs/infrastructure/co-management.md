# Co-Management

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

Co-management enables **Intune** (assignment/compliance plane) and **SCCM** (distribution/execution channel) to work together for Windows devices at constrained/offline sites.

**Design Principle**: Thin Control Plane — Intune remains primary assignment plane; SCCM is distribution channel.

---

## Co-Management Model

### Intune Role

- **Assignment**: Device targeting and compliance policies
- **Compliance**: Device compliance reporting
- **Policy**: Configuration policies
- **Not**: Content distribution (for constrained sites)

### SCCM Role

- **Distribution**: Application binary distribution
- **Execution**: Package installation execution
- **Content**: Distribution point management
- **Not**: Assignment or compliance (for co-managed devices)

---

## Configuration

### Device Tagging

**Site-Scoped Tags**:
- Devices tagged with site classification (Online, Intermittent, Air-gapped)
- Tags aligned to Entra ID group membership
- Tags determine distribution channel

**Example Tags**:
- `site-class:air-gapped`
- `site-class:intermittent`
- `acquisition-boundary:acquisition-a`
- `business-unit:bu-engineering`

### SCCM Collection Alignment

**Collection Mapping**:
- Control Plane maintains approved SCCM collections
- Collections aligned to site scopes
- Collections updated via SCCM connector

**Example Collections**:
- `Air-Gapped-Site-1-Devices`
- `Intermittent-Site-2-Devices`

### Co-Management Triggers

**Distribution Trigger**:
1. Intune assignment created for device with `site-class:air-gapped` tag
2. Control Plane triggers SCCM connector
3. SCCM connector creates/updates SCCM package
4. SCCM distributes to site DP
5. SCCM executes installation

---

## Workflow

### 1. Deployment Intent Creation

**Control Plane**:
- Creates Deployment Intent
- Sets target scope (includes site tags)
- Determines distribution channel (SCCM for air-gapped)

### 2. Intune Assignment

**Intune Connector**:
- Creates Intune assignment
- Targets devices via Entra ID groups
- Sets compliance policies

### 3. SCCM Distribution

**SCCM Connector**:
- Creates/updates SCCM package
- Distributes to site DPs
- Creates collection targeting

### 4. Execution

**SCCM**:
- Executes package installation
- Reports status to SCCM
- Intune queries SCCM for compliance status

### 5. Compliance Reporting

**Intune**:
- Queries device compliance
- Reports to Control Plane
- Control Plane reconciles desired vs actual state

---

## Promotion Gates

**Control Plane Enforcement**:
- Promotion gates evaluated in Control Plane
- CAB enforcement in Control Plane
- SCCM is execution channel only

**Gate Evaluation**:
- Success rate from SCCM telemetry
- Time-to-compliance from SCCM reports
- Compliance status from Intune

---

## Site Classification Integration

### Air-Gapped Sites

**Mandatory**: SCCM DP for content distribution
**Pattern**: SCCM DP is authoritative content channel

**Configuration**:
- Devices tagged `site-class:air-gapped`
- SCCM collections aligned to tags
- Intune assignments trigger SCCM distribution

### Intermittent Sites

**Optional**: SCCM DP for bandwidth optimization
**Decision**: Based on connectivity and device count

**Configuration**:
- Devices tagged `site-class:intermittent`
- SCCM collections created if SCCM selected
- Intune remains primary assignment plane

---

## Connector Integration

### Intune Connector

**Responsibilities**:
- Create Intune assignments
- Query Intune compliance
- Not trigger SCCM distribution (handled by SCCM connector)

### SCCM Connector

**Responsibilities**:
- Create/update SCCM packages
- Distribute to DPs
- Create collection targeting
- Query SCCM deployment status

### Control Plane

**Responsibilities**:
- Maintain site classification
- Maintain collection mappings
- Coordinate Intune + SCCM workflows
- Evaluate promotion gates

---

## References

- [Site Classification](./site-classification.md)
- [Distribution Decision Matrix](./distribution-decision-matrix.md)
- [Execution Plane Connectors](../architecture/execution-plane-connectors.md)
