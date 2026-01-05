# Risk Model

**Version**: 1.0 (Provisional)
**Status**: Active
**Last Updated**: 2026-01-04
**Next Review**: 2026-04-04 (Quarterly)

---

## Overview

This document defines the **deterministic risk scoring model** used by the Control Plane to assess deployment risk and enforce CAB approval gates. All risk scores are computed from **explicit, weighted factors** with **documented normalization rubrics**. This ensures explainability, auditability, and calibration.

**Design Principle**: Determinism — no "AI-driven deployments"; all approvals and gates are explainable.

---

## Risk Score Formula

```
RiskScore = clamp(0..100, Σ(weight_i × normalized_factor_i))
```

Where:
- `normalized_factor_i` is a value between `0.0` (no risk contribution) and `1.0` (maximum contribution)
- `weight_i` is the factor's weight (sum of all weights = 100)
- `clamp(0..100, x)` ensures the final score is between 0 and 100

**Example Calculation**:
```
privilege_impact: normalized=1.0, weight=20 → contribution=20
supply_chain_trust: normalized=0.1, weight=15 → contribution=1.5
exploitability: normalized=0.6, weight=10 → contribution=6
data_access: normalized=0.2, weight=10 → contribution=2
sbom_vulnerability: normalized=0.0, weight=15 → contribution=0
blast_radius: normalized=0.4, weight=10 → contribution=4
operational_complexity: normalized=0.3, weight=10 → contribution=3
history: normalized=0.2, weight=10 → contribution=2

RiskScore = 20 + 1.5 + 6 + 2 + 0 + 4 + 3 + 2 = 38.5 → 39
```

---

## Risk Factors (Initial Weights — Risk Model v1.0)

| Factor | Weight | Description |
|---|---:|---|
| **Privilege Impact** | 20 | Admin required, service install, system extensions, kernel/driver access |
| **Supply Chain Trust** | 15 | Signature validity, notarization, publisher reputation, provenance |
| **Exploitability** | 10 | Network listeners, exposed services, macros/scripting, user input handling |
| **Data Access** | 10 | Credential store access, wide filesystem access, sensitive data handling |
| **SBOM/Vulnerability** | 15 | Critical/High CVEs in dependencies, unpatched vulnerabilities |
| **Blast Radius** | 10 | Scope size (device count), ring level, BU/site count, criticality of targets |
| **Operational Complexity** | 10 | Offline import, reboots required, special sequencing, installation time |
| **History** | 10 | Prior incidents, failure rate, rollback difficulty, support tickets |

**Total Weight**: 100

---

## Scoring Rubric (v1.0)

### Factor 1: Privilege Impact (Weight: 20)

**Definition**: Level of system privilege required for installation and operation.

| Scenario | Normalized Value | Rationale |
|---|---:|---|
| **User-context install, no elevation** | 0.2 | Minimal privilege; limited blast radius if compromised |
| **User-context with optional admin features** | 0.5 | Some features require elevation but can run without |
| **Admin required for install, runs as user** | 0.7 | Installation is privileged, but runtime is not |
| **Admin/service install, runs elevated** | 1.0 | Full system privilege; maximum impact if compromised |
| **Driver/kernel extension/system extension** | 1.0 | Kernel-level access; critical system component |

**Examples**:
- Notepad++ (user-context install): `0.2`
- Microsoft Office (admin install, runs as user): `0.7`
- Antivirus software (service install, runs elevated): `1.0`
- Network driver (kernel extension): `1.0`

---

### Factor 2: Supply Chain Trust (Weight: 15)

**Definition**: Trustworthiness of the software supply chain (publisher, signing, provenance).

| Scenario | Normalized Value | Rationale |
|---|---:|---|
| **Signed + known vendor + consistent provenance** | 0.1 | High trust; reputable publisher with verified supply chain |
| **Signed + known vendor, weak provenance** | 0.3 | Trusted publisher but supply chain gaps (e.g., no SBOM) |
| **Signed but unknown/unverified vendor** | 0.4 | Signature present but publisher reputation unclear |
| **Unsigned or self-signed** | 0.7 | No supply chain verification; high risk |
| **Unsigned + uncertain provenance** | 0.9 | Maximum supply chain risk; unknown origin |

**Examples**:
- Microsoft Office (Microsoft-signed, consistent provenance): `0.1`
- Open-source tool (signed by community maintainer, weak provenance): `0.3`
- Internal LOB app (self-signed by dev team): `0.7`
- Script from unknown source (unsigned, uncertain provenance): `0.9`

---

### Factor 3: Exploitability (Weight: 10)

**Definition**: Presence of network listeners, exposed services, scripting/macro capabilities, or user input handling that increases attack surface.

| Scenario | Normalized Value | Rationale |
|---|---:|---|
| **No listeners, no macro/scripting capability** | 0.2 | Minimal attack surface; isolated application |
| **User-space listener (non-privileged port)** | 0.5 | Attack surface present but limited to user context |
| **Embedded scripting or macro capability** | 0.6 | Script execution risk (e.g., Office macros, browser extensions) |
| **User-space listener + scripting** | 0.8 | Combined attack surface (network + scripting) |
| **Privileged listener or exposed service with elevated context** | 1.0 | Maximum exploitability; remote attack + privilege escalation |

**Examples**:
- PDF reader (no listeners, no scripting): `0.2`
- Web browser (user-space listeners, embedded scripting): `0.8`
- Database server (privileged listener, elevated context): `1.0`

---

### Factor 4: Data Access (Weight: 10)

**Definition**: Access to credential stores, sensitive data, or wide filesystem access.

| Scenario | Normalized Value | Rationale |
|---|---:|---|
| **Scoped to app's own data directory** | 0.1 | Minimal data access; sandboxed |
| **Read access to user's Documents/Desktop** | 0.4 | Limited data access; standard user file access |
| **Read/write to user profile (AppData, Registry)** | 0.6 | Broad user data access; potential PII exposure |
| **Access to credential stores (Windows Credential Manager, macOS Keychain)** | 0.9 | Credential theft risk |
| **Wide filesystem access (C:\, /etc/, /var/) + credential store** | 1.0 | Maximum data access risk |

**Examples**:
- Notepad (scoped to opened files): `0.1`
- File sync client (read/write to Documents/Desktop): `0.6`
- Password manager (credential store access): `0.9`
- Backup software (wide filesystem access): `1.0`

---

### Factor 5: SBOM/Vulnerability (Weight: 15)

**Definition**: Presence of Critical/High CVEs in dependencies or unpatched vulnerabilities.

| Scenario | Normalized Value | Rationale |
|---|---:|---|
| **No High/Critical findings** | 0.0 | Clean SBOM; no known vulnerabilities |
| **Low/Medium findings only** | 0.3 | Minor vulnerabilities; acceptable with monitoring |
| **High present (no Critical), compensating controls possible** | 0.7 | High-severity vulnerability with mitigations |
| **Critical present, compensating controls applied** | 0.9 | Critical vulnerability; exception required |
| **Critical present, no compensating controls** | 1.0 | **BLOCKED** — publish must be blocked without approved exception |

**Examples**:
- App with no CVEs in scan: `0.0`
- App with Medium-severity CVE in non-critical dependency: `0.3`
- App with High CVE but network segmentation mitigates: `0.7`
- App with Critical CVE and approved exception: `0.9`
- App with Critical CVE and no exception: `1.0` (publish blocked)

**Policy Enforcement**:
- `normalized_value = 1.0` (Critical without exception) → **Publish blocked** by Packaging Factory
- `normalized_value = 0.9` (Critical with exception) → CAB approval required + exception linkage

---

### Factor 6: Blast Radius (Weight: 10)

**Definition**: Scope size (device count), ring level, BU/site count, criticality of target cohort.

| Scenario | Normalized Value | Rationale |
|---|---:|---|
| **Ring 0 (Lab), < 10 devices** | 0.1 | Minimal blast radius; testing only |
| **Ring 1 (Canary), < 100 devices** | 0.3 | Small canary group; limited impact |
| **Ring 2 (Pilot), < 1,000 devices** | 0.5 | Pilot group; moderate impact |
| **Ring 3 (Department), 1,000–10,000 devices** | 0.7 | Department-wide; significant impact |
| **Ring 4 (Global), > 10,000 devices** | 1.0 | Enterprise-wide; maximum blast radius |

**Criticality Multiplier**:
- If target cohort includes **critical infrastructure** (e.g., servers, domain controllers, executive devices), multiply by `1.2` (capped at `1.0`).

**Examples**:
- Ring 0 (Lab), 5 devices: `0.1`
- Ring 1 (Canary), 50 devices: `0.3`
- Ring 2 (Pilot), 500 devices: `0.5`
- Ring 3 (Department), 5,000 devices: `0.7`
- Ring 4 (Global), 50,000 devices: `1.0`
- Ring 2 (Pilot), 500 executive devices (critical): `0.5 × 1.2 = 0.6` (capped at `1.0`)

---

### Factor 7: Operational Complexity (Weight: 10)

**Definition**: Offline import requirements, reboots, special sequencing, installation time, rollback difficulty.

| Scenario | Normalized Value | Rationale |
|---|---:|---|
| **Online install, no reboot, < 5 min** | 0.1 | Simple installation; minimal disruption |
| **Online install, no reboot, 5–15 min** | 0.3 | Moderate installation time |
| **Requires reboot (user-initiated)** | 0.5 | User disruption; reboot required |
| **Requires reboot + special sequencing (dependencies)** | 0.7 | Complex installation; multiple steps |
| **Offline import + reboot + special sequencing** | 1.0 | Maximum operational complexity; air-gapped |

**Examples**:
- Browser extension (online, no reboot, < 1 min): `0.1`
- Desktop app (online, no reboot, 10 min): `0.3`
- Windows update (requires reboot): `0.5`
- Database server (requires reboot + dependency sequencing): `0.7`
- Air-gapped site deployment (offline import + reboot + sequencing): `1.0`

---

### Factor 8: History (Weight: 10)

**Definition**: Prior incidents, failure rate, rollback difficulty, support tickets.

| Scenario | Normalized Value | Rationale |
|---|---:|---|
| **No prior incidents, success rate > 99%** | 0.1 | Proven reliability; minimal historical risk |
| **Minor incidents (< 5% failure rate), easy rollback** | 0.3 | Some historical issues but manageable |
| **Moderate incidents (5–10% failure rate), moderate rollback difficulty** | 0.6 | Historical issues require monitoring |
| **Major incidents (> 10% failure rate), difficult rollback** | 0.9 | High historical risk; CAB scrutiny required |
| **Prior security incident or data breach** | 1.0 | Maximum historical risk; special approval required |

**Examples**:
- App with 99.8% success rate, no incidents: `0.1`
- App with 95% success rate, occasional issues: `0.3`
- App with 90% success rate, known rollback difficulties: `0.6`
- App with 85% success rate, multiple incidents: `0.9`
- App with prior security breach: `1.0`

---

## Risk Thresholds and Gates

| Risk Score | Threshold | CAB Requirement | Ring Constraints |
|---|---|---|---|
| **0–50** | `AUTOMATED_ALLOWED` | No CAB approval required (evidence pack still required) | Automated ring progression with promotion gates |
| **51–100** | `CAB_REQUIRED` | CAB approval required before Ring 2+ | Ring 1 (Canary) allowed without CAB; Ring 2+ blocked until approval |
| **N/A** | `PRIVILEGED_TOOLING` | Always requires CAB approval regardless of score | Special scrutiny for admin tools, security software, etc. |

**Notes**:
- Ring 1 (Canary) deployment for `Risk > 50` is allowed **without CAB approval** to enable early detection, but **evidence pack completeness** and all non-CAB gates still enforced.
- CAB approval is **mandatory** before promoting `Risk > 50` apps from Ring 1 → Ring 2.
- Privileged tooling (e.g., antivirus, EDR, privilege escalation tools) **always requires CAB approval** regardless of computed risk score.

---

## Calibration Process

**Frequency**: Quarterly review by Security + CAB (Q1, Q2, Q3, Q4)

**Calibration Workflow**:
1. **Data Collection**: Gather incident data, failure rates, rollback executions, CAB approval times from previous quarter
2. **Factor Analysis**: Analyze correlation between risk factors and actual incidents/failures
3. **Weight Adjustment**: Propose weight adjustments based on data (e.g., increase `privilege_impact` weight if privilege-related incidents increased)
4. **Rubric Refinement**: Refine normalization rubrics based on edge cases encountered
5. **Model Versioning**: Create new risk model version (e.g., `v1.0` → `v1.1`) with documented changes
6. **CAB Approval**: Submit calibration proposal to CAB for approval
7. **Deployment**: Deploy new risk model version with effective date
8. **Audit Trail**: Record risk model changes in immutable event store

**Calibration Criteria**:
- **Incident Correlation**: If incidents are not correlated with high risk scores, adjust factors/weights
- **False Positive Rate**: If low-risk apps (score < 50) have high incident rates, adjust thresholds downward
- **False Negative Rate**: If high-risk apps (score > 50) have low incident rates, adjust thresholds upward
- **CAB Burden**: If CAB approval pipeline is overwhelmed (> 80% of apps require approval), consider threshold adjustment

**Version History**:
| Version | Effective Date | Changes | Approved By |
|---|---|---|---|
| v1.0 | 2026-01-04 | Initial risk model | CAB Board |
| v1.1 | TBD | TBD | TBD |

---

## Risk Model Versioning

**Versioning Scheme**: `vMAJOR.MINOR`
- **MAJOR**: Significant changes to formula, factors, or thresholds (requires CAB approval)
- **MINOR**: Rubric refinements, weight adjustments (requires CAB approval)

**Backward Compatibility**:
- Control Plane must support multiple risk model versions concurrently during transition period (30 days)
- Deployment intents include `risk_model_version` field to track which version was used
- Historical risk assessments remain immutable; re-assessment uses current model version

**Migration Strategy**:
1. Deploy new risk model version alongside current version
2. Run parallel assessments for 7 days (compute risk with both versions, log differences)
3. Review parallel assessment results with Security + CAB
4. Approve migration if no significant discrepancies
5. Set new version as default; deprecate old version after 30 days

---

## Exception Handling

**Exception Types**:
1. **Vulnerability Exception**: Critical/High CVE present with compensating controls
2. **Scope Exception**: Cross-boundary deployment with CAB approval
3. **Privileged Tooling Exception**: Privileged tooling with special approval workflow

**Exception Workflow**:
1. **Packaging Engineer** identifies exception trigger (e.g., High CVE in scan)
2. **Packaging Engineer** documents compensating controls and submits exception request
3. **Security Reviewer** reviews exception request and approves/denies
4. **Exception Record** created with expiry date (max 90 days)
5. **Exception linked to Deployment Intent** for audit trail
6. **CAB Evidence Pack** includes exception record and compensating controls

**Exception Expiry Handling**:
- Exceptions expire automatically after expiry date
- Deployment intents with expired exceptions are **blocked** from new ring promotions
- Automated alerts sent 14 days before expiry to exception owner
- Exception renewal requires re-review by Security Reviewer

---

## Risk Assessment API

### Compute Risk Score

**Endpoint**: `POST /api/v1/risk-assessment/compute`

**Request**:
```json
{
  "artifact_id": "artifact-uuid",
  "deployment_intent": {
    "target_scope": {
      "ring": "ring-2-pilot",
      "device_count": 500,
      "business_unit": "bu-finance",
      "criticality": "standard"
    }
  },
  "risk_model_version": "v1.0"
}
```

**Response**:
```json
{
  "risk_assessment_id": "uuid-v4",
  "artifact_id": "artifact-uuid",
  "risk_score": 45,
  "risk_model_version": "v1.0",
  "threshold": "AUTOMATED_ALLOWED",
  "cab_required": false,
  "computed_at": "2026-01-04T10:00:00Z",
  "factors": [
    {
      "name": "privilege_impact",
      "normalized_value": 0.7,
      "weight": 20,
      "contribution": 14,
      "rationale": "Admin required for install, runs as user"
    },
    {
      "name": "supply_chain_trust",
      "normalized_value": 0.1,
      "weight": 15,
      "contribution": 1.5,
      "rationale": "Signed + known vendor + consistent provenance"
    },
    {
      "name": "exploitability",
      "normalized_value": 0.2,
      "weight": 10,
      "contribution": 2,
      "rationale": "No listeners, no macro/scripting capability"
    },
    {
      "name": "data_access",
      "normalized_value": 0.4,
      "weight": 10,
      "contribution": 4,
      "rationale": "Read access to user's Documents/Desktop"
    },
    {
      "name": "sbom_vulnerability",
      "normalized_value": 0.0,
      "weight": 15,
      "contribution": 0,
      "rationale": "No High/Critical findings"
    },
    {
      "name": "blast_radius",
      "normalized_value": 0.5,
      "weight": 10,
      "contribution": 5,
      "rationale": "Ring 2 (Pilot), 500 devices"
    },
    {
      "name": "operational_complexity",
      "normalized_value": 0.5,
      "weight": 10,
      "contribution": 5,
      "rationale": "Requires reboot (user-initiated)"
    },
    {
      "name": "history",
      "normalized_value": 0.3,
      "weight": 10,
      "contribution": 3,
      "rationale": "Minor incidents (< 5% failure rate), easy rollback"
    }
  ],
  "total_contribution": 34.5,
  "clamped_score": 45
}
```

---

## Example Risk Assessments

### Example 1: Low-Risk Desktop App

**Application**: Notepad++ (text editor)

| Factor | Normalized Value | Weight | Contribution | Rationale |
|---|---:|---:|---:|---|
| Privilege Impact | 0.2 | 20 | 4 | User-context install, no elevation |
| Supply Chain Trust | 0.1 | 15 | 1.5 | Signed + known vendor (open-source) |
| Exploitability | 0.2 | 10 | 2 | No listeners, no macro/scripting |
| Data Access | 0.1 | 10 | 1 | Scoped to opened files |
| SBOM/Vulnerability | 0.0 | 15 | 0 | No High/Critical findings |
| Blast Radius | 0.3 | 10 | 3 | Ring 1 (Canary), 50 devices |
| Operational Complexity | 0.1 | 10 | 1 | Online install, no reboot, < 5 min |
| History | 0.1 | 10 | 1 | No prior incidents, success rate > 99% |

**Risk Score**: 13.5 → **14**
**Threshold**: `AUTOMATED_ALLOWED`
**CAB Required**: No

---

### Example 2: High-Risk Security Software

**Application**: Antivirus/EDR Agent

| Factor | Normalized Value | Weight | Contribution | Rationale |
|---|---:|---:|---:|---|
| Privilege Impact | 1.0 | 20 | 20 | Service install, runs elevated (kernel driver) |
| Supply Chain Trust | 0.1 | 15 | 1.5 | Signed + known vendor + consistent provenance |
| Exploitability | 1.0 | 10 | 10 | Privileged listener, elevated context |
| Data Access | 1.0 | 10 | 10 | Wide filesystem access + credential store |
| SBOM/Vulnerability | 0.0 | 15 | 0 | No High/Critical findings |
| Blast Radius | 1.0 | 10 | 10 | Ring 4 (Global), 50,000 devices |
| Operational Complexity | 0.7 | 10 | 7 | Requires reboot + special sequencing |
| History | 0.3 | 10 | 3 | Minor incidents, moderate rollback difficulty |

**Risk Score**: 61.5 → **62**
**Threshold**: `CAB_REQUIRED` + `PRIVILEGED_TOOLING`
**CAB Required**: Yes (before Ring 2+ promotion)

---

### Example 3: Medium-Risk LOB App with Exception

**Application**: Custom Finance Dashboard (internal LOB app)

| Factor | Normalized Value | Weight | Contribution | Rationale |
|---|---:|---:|---:|---|
| Privilege Impact | 0.7 | 20 | 14 | Admin required for install, runs as user |
| Supply Chain Trust | 0.7 | 15 | 10.5 | Self-signed by dev team (internal LOB) |
| Exploitability | 0.5 | 10 | 5 | User-space listener (non-privileged port) |
| Data Access | 0.6 | 10 | 6 | Read/write to user profile (AppData, Registry) |
| SBOM/Vulnerability | 0.9 | 15 | 13.5 | **High CVE with approved exception** |
| Blast Radius | 0.5 | 10 | 5 | Ring 2 (Pilot), 500 devices (Finance BU) |
| Operational Complexity | 0.3 | 10 | 3 | Online install, no reboot, 10 min |
| History | 0.1 | 10 | 1 | No prior incidents (new app) |

**Risk Score**: 58 → **58**
**Threshold**: `CAB_REQUIRED`
**CAB Required**: Yes (before Ring 2+ promotion)
**Exception**: High CVE with compensating controls (network segmentation, EDR monitoring, vendor patch expected within 14 days)

---

## Related Documentation

- [Architecture Overview](architecture-overview.md)
- [Control Plane Design](control-plane-design.md)
- [Evidence Pack Schema](evidence-pack-schema.md)
- [CAB Workflow](cab-workflow.md)
- [Exception Management](exception-management.md)

---

**Risk Model v1.0 is PROVISIONAL. Calibration and refinement expected after Phase 1 deployment.**
