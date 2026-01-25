# Distribution Decision Matrix

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

This matrix defines **distribution strategies** by platform and site class. Distribution decisions are **deterministic** based on site classification and platform requirements.

**Design Principle**: Offline is First-Class — explicit distribution strategy per site class.

---

## Decision Matrix

| Site Class | Windows | macOS | Linux |
|------------|---------|-------|-------|
| **Online** | Intune + Delivery Optimization | Intune/Jamf | Central APT repo |
| **Intermittent** | Intune + caching or SCCM DPs | Intune/Jamf + DPs | Site mirror + Landscape/Ansible |
| **Air-Gapped** | SCCM DPs (mandatory) | Jamf via import | Mirror via import + pinning |

---

## Windows Distribution

### Online Sites

**Primary**: Microsoft Intune
**Optimization**: Delivery Optimization (peer-to-peer caching)
**Enterprise Caching**: Microsoft Connected Cache (where feasible)

**Benefits**:
- Centralized management
- Bandwidth optimization via peer caching
- Real-time compliance reporting

### Intermittent Sites

**Options**:
1. **Intune + Delivery Optimization**: For sites with periodic connectivity
2. **SCCM Distribution Points**: For sites requiring local content

**Decision Criteria**:
- Connectivity reliability (<95% uptime → SCCM)
- Bandwidth constraints (<5 Mbps → SCCM)
- Device count (>100 devices → SCCM for efficiency)

### Air-Gapped Sites

**Mandatory**: SCCM Distribution Points
**Pattern**: SCCM DP is authoritative content channel

**Co-Management**:
- Intune remains assignment/compliance plane
- SCCM executes distribution for constrained cohorts
- Control Plane maintains collection mappings

---

## macOS Distribution

### Online Sites

**Primary**: Microsoft Intune
**Secondary**: Jamf Pro (where deeper macOS controls required)

**Decision Criteria**:
- Standard macOS management → Intune
- Advanced macOS features required → Jamf

### Intermittent Sites

**Options**:
1. **Intune/Jamf + Distribution Points**: Local content caching
2. **Jamf Cloud + DPs**: For Jamf-managed sites

**Decision Criteria**:
- Existing Jamf infrastructure → Jamf DPs
- Intune-only → Intune with local caching

### Air-Gapped Sites

**Method**: Jamf packages via controlled import

**Process**:
1. Package prepared in Packaging Factory
2. Transferred via approved media
3. Imported to Jamf DP
4. Distributed via Jamf policies

---

## Linux Distribution

### Online Sites

**Method**: Central signed APT repository

**Benefits**:
- Centralized package management
- Version control
- Signed packages

### Intermittent Sites

**Method**: Site-local APT mirrors + Landscape/Ansible

**Configuration**:
- APT mirror at site
- Landscape schedules or Ansible playbooks for enforcement
- Periodic sync with central repo

### Air-Gapped Sites

**Method**: APT mirror via controlled import + pinning

**Process**:
1. Mirror prepared with required packages
2. Transferred via approved media
3. Imported to site mirror
4. Package pinning for version control
5. Landscape/Ansible for enforcement

---

## Mobile Distribution

### iOS/iPadOS

**Method**: Intune (ABM + ADE)

**Distribution**:
- VPP apps: Managed distribution via Intune
- LOB apps: Managed distribution via Intune
- Offline: Limited (requires periodic MDM check-in)

### Android

**Method**: Intune (Android Enterprise)

**Distribution**:
- Managed Google Play: Standard distribution
- Private apps: Managed distribution via Intune
- Offline: Limited (requires periodic MDM check-in)

---

## Decision Workflow

### 1. Site Classification

Determine site class (Online, Intermittent, Air-gapped)

### 2. Platform Selection

Identify target platform (Windows, macOS, Linux, Mobile)

### 3. Matrix Lookup

Use decision matrix to determine distribution method

### 4. Configuration

Configure distribution method per site requirements

### 5. Validation

Validate distribution configuration and test

---

## Exception Process

**Exceptions Require**:
- CAB approval
- Justification
- Compensating controls
- Expiry date

**Example Exception**:
- Using Intune for air-gapped Windows site (requires Connected Cache + CAB approval)

---

## References

- [Site Classification](./site-classification.md)
- [Air-Gapped Procedures](./air-gapped-procedures.md)
- [Co-Management](./co-management.md)
- [Bandwidth Optimization](./bandwidth-optimization.md)
