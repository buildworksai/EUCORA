# Site Classification

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-06

---

## Overview

Site classification determines **distribution strategy** and **time-to-compliance expectations** for each site. All sites MUST be classified as Online, Intermittent, or Air-gapped.

**Design Principle**: Offline is First-Class — explicit distribution strategy per site class.

---

## Site Classes

### Online

**Definition**: Stable, high-bandwidth connectivity to cloud services

**Characteristics**:
- Continuous internet connectivity
- Low latency (<100ms to cloud)
- High bandwidth (>10 Mbps)
- Reliable connection (>99.9% uptime)

**Distribution Strategy**:
- **Windows**: Intune primary with Delivery Optimization
- **macOS**: Intune/Jamf standard distribution
- **Linux**: Central APT repository

**Time-to-Compliance**: ≤ **24 hours**

**Examples**:
- Corporate headquarters
- Regional offices with fiber connectivity
- Cloud-hosted VDI environments

---

### Intermittent

**Definition**: Limited bandwidth or frequent connectivity outages

**Characteristics**:
- Periodic internet connectivity
- Variable bandwidth (1-10 Mbps)
- Frequent outages (<95% uptime)
- High latency (>200ms)

**Distribution Strategy**:
- **Windows**: Intune + local caching (Delivery Optimization) or SCCM DPs
- **macOS**: Intune/Jamf with distribution points
- **Linux**: Site-local APT mirrors + Landscape/Ansible

**Time-to-Compliance**: ≤ **72 hours**

**Examples**:
- Remote offices with satellite connectivity
- Field sites with cellular connectivity
- Branch offices with limited bandwidth

---

### Air-Gapped

**Definition**: No cloud access; controlled transfer windows

**Characteristics**:
- No internet connectivity
- Controlled import windows (quarterly, monthly, etc.)
- Physical media transfer required
- Strict security controls

**Distribution Strategy**:
- **Windows**: SCCM distribution points (mandatory)
- **macOS**: Jamf packages via controlled import
- **Linux**: APT mirrors via controlled import + pinning

**Time-to-Compliance**: ≤ **7 days** (or next approved transfer window)

**Examples**:
- Classified networks
- Industrial control systems
- Secure facilities

---

## Site Classification Process

### 1. Initial Classification

**Performed By**: Platform Admin, Site Owner
**Criteria**:
- Network connectivity assessment
- Bandwidth measurement
- Uptime monitoring
- Security requirements

**Documentation**:
- Site classification record
- Justification
- Distribution strategy
- Time-to-compliance target

### 2. Classification Review

**Frequency**: Annual or on network changes
**Reviewers**: Platform Admin, Network Team, Security Team

**Update Triggers**:
- Network infrastructure changes
- Connectivity improvements
- Security policy changes
- Site relocation

### 3. Classification Storage

**Storage**: Control Plane database
**Schema**:
```json
{
  "site_id": "uuid",
  "site_name": "Site Name",
  "classification": "online|intermittent|air_gapped",
  "distribution_strategy": {
    "windows": "intune|sccm",
    "macos": "intune|jamf",
    "linux": "apt_mirror|landscape|ansible"
  },
  "time_to_compliance_hours": 24,
  "last_reviewed": "2026-01-06",
  "next_review": "2027-01-06"
}
```

---

## Distribution Decision Matrix

| Site Class | Windows | macOS | Linux |
|------------|---------|-------|-------|
| **Online** | Intune + Delivery Optimization | Intune/Jamf | Central APT repo |
| **Intermittent** | Intune + caching or SCCM DPs | Intune/Jamf + DPs | Site mirror + Landscape/Ansible |
| **Air-Gapped** | SCCM DPs (mandatory) | Jamf via import | Mirror via import + pinning |

---

## Co-Management Configuration

### Windows Offline/Constrained Sites

**Standard Pattern**:
- **SCCM DP**: Authoritative content channel for binaries
- **Intune**: Primary assignment/compliance plane
- **Co-Management**: Intune targeting triggers SCCM distribution

**Configuration**:
- Site-scoped device tags
- SCCM collections aligned to site scopes
- Control Plane maintains collection mappings

---

## References

- [Distribution Decision Matrix](./distribution-decision-matrix.md)
- [Air-Gapped Procedures](./air-gapped-procedures.md)
- [Co-Management](./co-management.md)
- [Bandwidth Optimization](./bandwidth-optimization.md)
