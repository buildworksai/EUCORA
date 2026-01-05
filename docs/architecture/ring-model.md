# Ring-Based Rollout Model

**Version**: 1.0
**Status**: Active
**Last Updated**: 2026-01-04

---

## Overview

The ring-based rollout model provides **measurable, progressive deployment** with **promotion gates** and **deterministic rollback strategies**. Apps are deployed incrementally across rings (Lab → Canary → Pilot → Department → Global) with validation at each stage before promotion.

**Design Principle**: Reconciliation over hope — continuous desired-vs-actual drift detection with measurable promotion gates.

---

## Ring Definitions

### Ring 0: Lab / Automation

**Purpose**: Automated testing and validation in isolated lab environment.

**Characteristics**:
- **Target**: Test VMs, isolated lab devices (non-production)
- **Device Count**: 5–10 devices
- **Deployment Window**: 24 hours
- **Success Rate Threshold**: ≥ 95% (testing environment, higher failure tolerance)
- **Time-to-Compliance**: ≤ 4 hours
- **Approval Required**: No (automated deployment)
- **Rollback Validation**: **REQUIRED** — must validate rollback strategy in Ring 0 before Ring 1 promotion

**Purpose-Specific Validation**:
- Installation success (exit code 0 or documented success codes)
- Detection rules validation (all detection rules must trigger correctly)
- Uninstallation clean removal (no residual files or registry keys)
- Upgrade path testing (if applicable, from previous version)
- Rollback execution test (validate rollback strategy works)

**Promotion Gate to Ring 1**:
- ≥ 95% success rate
- All detection rules validated
- Rollback strategy validated
- No blocking issues identified

---

### Ring 1: Canary

**Purpose**: Early detection of issues with small, tech-savvy cohort (IT staff, early adopters).

**Characteristics**:
- **Target**: IT department, packaging engineers, early adopters
- **Device Count**: 50–100 devices
- **Deployment Window**: 24–48 hours
- **Success Rate Threshold**: ≥ **98%**
- **Time-to-Compliance**: ≤ 24 hours (online sites)
- **Approval Required**: No for `Risk ≤ 50`; evidence pack completeness still required for all
- **CAB Note**: `Risk > 50` apps can deploy to Ring 1 **without CAB approval** to enable early detection, but CAB approval **mandatory** before Ring 2 promotion

**Target Cohort Profile**:
- Technical users who can provide detailed feedback
- High tolerance for early-stage issues
- Capable of self-remediation or working around issues
- Quick to report problems (dedicated feedback channel)

**Promotion Gate to Ring 2**:
- ≥ 98% success rate
- Time-to-compliance ≤ 24h (online), ≤ 72h (intermittent), ≤ 7d (air-gapped)
- No security incidents attributable to package
- Rollback strategy validated in Ring 0 (prerequisite)
- **CAB approval if `Risk > 50` or privileged tooling**

---

### Ring 2: Pilot

**Purpose**: Controlled pilot with representative cohort from target business unit.

**Characteristics**:
- **Target**: Representative sample from target BU (e.g., Finance pilot group)
- **Device Count**: 500–1,000 devices
- **Deployment Window**: 48–72 hours
- **Success Rate Threshold**: ≥ **97%**
- **Time-to-Compliance**: ≤ 24 hours (online), ≤ 72 hours (intermittent)
- **Approval Required**: **CAB approval required** if `Risk > 50` or privileged tooling
- **Feedback Mechanism**: Pilot users complete feedback survey (optional but recommended)

**Target Cohort Profile**:
- Business users from target BU (not IT staff)
- Diverse device configurations (various Windows/macOS versions, hardware profiles)
- Representative site classes (online + intermittent if applicable)
- Willing to provide feedback on user experience

**Promotion Gate to Ring 3**:
- ≥ 97% success rate
- Time-to-compliance ≤ 24h (online), ≤ 72h (intermittent)
- No P1/P0 incidents attributable to package
- Pilot feedback reviewed (if collected)
- No unresolved blocking issues

---

### Ring 3: Department

**Purpose**: Full department-wide rollout within target BU.

**Characteristics**:
- **Target**: Entire business unit (e.g., all Finance users)
- **Device Count**: 1,000–10,000 devices
- **Deployment Window**: 72–168 hours (1 week)
- **Success Rate Threshold**: ≥ **99%** (enterprise standard apps)
- **Time-to-Compliance**: ≤ 24 hours (online), ≤ 72 hours (intermittent)
- **Approval Required**: CAB approval already granted in Ring 2 (revalidation not required unless scope change)
- **Support Readiness**: Endpoint Ops must be staffed and ready for support escalations

**Target Cohort Profile**:
- All users in target BU (Finance, HR, IT, etc.)
- Production workloads (business-critical usage)
- Diverse site classes (online, intermittent, air-gapped)
- Standard SLA expectations

**Promotion Gate to Ring 4**:
- ≥ 99% success rate (enterprise standard apps)
- Time-to-compliance ≤ 24h (online), ≤ 72h (intermittent), ≤ 7d (air-gapped)
- No P1/P0 incidents attributable to package
- Support ticket volume within acceptable range (baseline ± 10%)
- Endpoint Ops sign-off (operational readiness)

---

### Ring 4: Global

**Purpose**: Enterprise-wide deployment to all eligible devices.

**Characteristics**:
- **Target**: All enterprise devices (all BUs, all geographies, all acquisition boundaries)
- **Device Count**: 10,000–100,000+ devices
- **Deployment Window**: 168+ hours (1–4 weeks)
- **Success Rate Threshold**: ≥ **99%** (enterprise standard apps)
- **Time-to-Compliance**: ≤ 24 hours (online), ≤ 72 hours (intermittent), ≤ 7 days (air-gapped)
- **Approval Required**: CAB approval already granted (no revalidation unless scope change)
- **Monitoring**: Enhanced monitoring and telemetry for 30 days post-deployment

**Target Cohort Profile**:
- Entire enterprise (all users, all devices)
- All site classes (online, intermittent, air-gapped)
- Maximum blast radius
- Production-critical deployments

**Post-Deployment Monitoring**:
- Success rate tracked daily for 30 days
- Drift detection runs hourly (reconciliation loops)
- Support ticket analysis (compare to baseline)
- User feedback analysis (if collected)
- Quarterly review: Add to "history" factor for next version deployment

---

## Promotion Gate Evaluation

### Automated Promotion Gate Algorithm

```python
def evaluate_promotion_gate(deployment_intent, current_ring, telemetry):
    """
    Evaluate if promotion from current_ring to next_ring is allowed.

    Returns:
        {
            "allow_promotion": bool,
            "gates_passed": [str],
            "gates_failed": [str],
            "gate_results": {
                "success_rate": {"threshold": 0.98, "actual": 0.992, "passed": True},
                "time_to_compliance": {"threshold_hours": 24, "actual_hours": 18, "passed": True},
                "incident_count": {"max_allowed": 0, "actual": 0, "passed": True},
                "cab_approval": {"required": True, "approved": True, "passed": True}
            }
        }
    """
    gates_passed = []
    gates_failed = []
    gate_results = {}

    # Gate 1: Success Rate
    threshold = get_success_rate_threshold(current_ring)
    actual_rate = telemetry.success_rate
    if actual_rate >= threshold:
        gates_passed.append("success_rate")
    else:
        gates_failed.append("success_rate")
    gate_results["success_rate"] = {
        "threshold": threshold,
        "actual": actual_rate,
        "passed": actual_rate >= threshold
    }

    # Gate 2: Time-to-Compliance
    site_class = deployment_intent.target_scope.site_class
    threshold_hours = get_time_to_compliance_threshold(site_class)
    actual_hours = telemetry.time_to_compliance_hours
    if actual_hours <= threshold_hours:
        gates_passed.append("time_to_compliance")
    else:
        gates_failed.append("time_to_compliance")
    gate_results["time_to_compliance"] = {
        "threshold_hours": threshold_hours,
        "actual_hours": actual_hours,
        "passed": actual_hours <= threshold_hours
    }

    # Gate 3: Incident Count
    max_incidents = 0  # Zero tolerance for security incidents
    actual_incidents = telemetry.security_incident_count
    if actual_incidents <= max_incidents:
        gates_passed.append("incident_count")
    else:
        gates_failed.append("incident_count")
    gate_results["incident_count"] = {
        "max_allowed": max_incidents,
        "actual": actual_incidents,
        "passed": actual_incidents <= max_incidents
    }

    # Gate 4: CAB Approval (if required)
    if deployment_intent.risk_score > 50 or deployment_intent.is_privileged:
        if deployment_intent.cab_approval_id and is_approved(deployment_intent.cab_approval_id):
            gates_passed.append("cab_approval")
        else:
            gates_failed.append("cab_approval")
        gate_results["cab_approval"] = {
            "required": True,
            "approved": deployment_intent.cab_approval_id is not None,
            "passed": deployment_intent.cab_approval_id is not None
        }
    else:
        gate_results["cab_approval"] = {"required": False, "passed": True}

    # Gate 5: Rollback Validation (for Ring 0 → Ring 1 only)
    if current_ring == "ring-0-lab":
        if deployment_intent.rollback_plan.validated:
            gates_passed.append("rollback_validation")
        else:
            gates_failed.append("rollback_validation")
        gate_results["rollback_validation"] = {
            "validated": deployment_intent.rollback_plan.validated,
            "passed": deployment_intent.rollback_plan.validated
        }

    return {
        "allow_promotion": len(gates_failed) == 0,
        "gates_passed": gates_passed,
        "gates_failed": gates_failed,
        "gate_results": gate_results
    }
```

---

## Success Rate Thresholds

| Ring | Success Rate Threshold | Rationale |
|---|---:|---|
| Ring 0 (Lab) | ≥ 95% | Testing environment; higher failure tolerance for early detection |
| Ring 1 (Canary) | ≥ 98% | Tech-savvy users; can tolerate some failures but expect high quality |
| Ring 2 (Pilot) | ≥ 97% | Business users; slightly lower than canary due to diverse configurations |
| Ring 3 (Department) | ≥ 99% | Production BU; enterprise standard |
| Ring 4 (Global) | ≥ 99% | Enterprise-wide; maximum quality expectation |

**Note**: Thresholds are **provisional for Phase 1** and subject to calibration based on actual deployment data.

---

## Time-to-Compliance Thresholds

**Time-to-Compliance**: Time from deployment intent creation to first successful install on target device.

| Site Class | Time-to-Compliance Threshold |
|---|---|
| Online | ≤ 24 hours |
| Intermittent | ≤ 72 hours |
| Air-gapped | ≤ 7 days (or next approved transfer window) |

**Enforcement**:
- Promotion gates evaluate time-to-compliance per site class
- Devices that exceed threshold trigger drift detection and remediation workflows
- Time-to-compliance tracked in telemetry dashboards

---

## Ring Assignment Strategies

### Static Ring Assignment

**Method**: Devices assigned to rings via Entra ID groups (manual or dynamic).

**Entra ID Group Naming**:
- `AAD-Ring0-Lab-Devices` (static membership, test VMs)
- `AAD-Ring1-Canary-IT-Dept` (dynamic membership, `department == "IT"`)
- `AAD-Ring2-Pilot-Finance-BU` (static membership, pilot volunteers)
- `AAD-Ring3-Department-Finance-All` (dynamic membership, `department == "Finance"`)
- `AAD-Ring4-Global-All-Devices` (dynamic membership, all compliant devices)

**Advantages**:
- Predictable cohorts
- Easy to audit ring membership
- Clear separation between rings

**Disadvantages**:
- Manual maintenance for static groups
- Requires Entra ID dynamic group rules for scalability

---

### Progressive Ring Membership (Recommended)

**Method**: Devices automatically promoted to higher rings based on telemetry.

**Algorithm**:
```python
def assign_device_to_ring(device, app):
    """Assign device to ring based on telemetry and device profile."""
    if device in test_lab:
        return "ring-0-lab"
    elif device.department == "IT" or device.user in early_adopters:
        return "ring-1-canary"
    elif device.user in pilot_volunteers and app.target_bu == device.department:
        return "ring-2-pilot"
    elif app.target_bu == device.department:
        return "ring-3-department"
    else:
        return "ring-4-global"
```

**Advantages**:
- Automated ring assignment reduces manual overhead
- Scales to large device fleets
- Consistent ring membership across apps

**Disadvantages**:
- Requires device metadata (department, user profile, site class)
- Complexity in multi-BU deployments

---

## Deployment Scheduling

### Ring Deployment Schedule (Example)

**App**: Notepad++ 8.6.2
**Target BU**: Finance
**Site Class**: Online

| Ring | Start Date | Duration | Target Devices | Cumulative Devices |
|---|---|---|---:|---:|
| Ring 0 (Lab) | 2026-01-05 00:00 | 24 hours | 5 | 5 |
| Ring 1 (Canary) | 2026-01-06 00:00 | 24 hours | 50 | 55 |
| Ring 2 (Pilot) | 2026-01-07 00:00 | 48 hours | 500 | 555 |
| Ring 3 (Department) | 2026-01-09 00:00 | 72 hours | 5,000 | 5,555 |
| Ring 4 (Global) | 2026-01-12 00:00 | 168 hours | 50,000 | 55,555 |

**Deployment Cadence**:
- Ring 0 → Ring 1: 1 day gap (24h validation)
- Ring 1 → Ring 2: 1 day gap (24h validation + CAB approval if required)
- Ring 2 → Ring 3: 2 days gap (48h validation)
- Ring 3 → Ring 4: 3 days gap (72h validation + operational readiness)

**Total Deployment Duration**: 12 days (from Ring 0 start to Ring 4 completion)

---

## Rollback Strategies (Per-Plane Reality)

### Intune Rollback

**Strategy**: Supersedence or version pinning.

**Steps**:
1. Update Intune app supersedence relationship (new version supersedes old version)
2. Remove assignments for failing version
3. Add assignments for rollback version (previous stable version)
4. Monitor install success rate (target: >98% within 24h)
5. Validate detection rules for rollback version

**Rollback Time**: 30–60 minutes (assignment changes + Intune sync cycle)

**Limitations**:
- Requires previous version to be retained in Intune (retention policy: 90 days)
- Supersedence only works if relationship was defined upfront

---

### SCCM Rollback

**Strategy**: Rollback packages + collections + distribution points.

**Steps**:
1. Create rollback package (previous version) if not already present
2. Distribute rollback package to DPs aligned to affected site collections
3. Remove deployment for failing version
4. Create deployment for rollback version targeting affected collections
5. Monitor deployment status via SCCM reporting

**Rollback Time**: 1–4 hours (depends on DP distribution speed and site connectivity)

**Limitations**:
- Requires DP bandwidth for rollback package distribution
- Air-gapped sites: Rollback package must be pre-staged on DPs

---

### Jamf Pro Rollback

**Strategy**: Policy-based version pinning + uninstall scripts.

**Steps**:
1. Update Jamf policy to pin to previous version
2. Scope policy to affected smart groups
3. Trigger policy update on devices (push notification or device check-in)
4. Execute uninstall script for failing version (if needed)
5. Install rollback version via updated policy

**Rollback Time**: 30–60 minutes (policy update + device check-in)

**Limitations**:
- Requires device check-in to Jamf (offline devices delayed)
- Uninstall scripts must be tested in Ring 0

---

### Linux (APT) Rollback

**Strategy**: `apt pinning` or package downgrade via Landscape/Ansible.

**Steps**:
1. Update APT pinning rules to pin to previous version
2. Push pinning configuration via Landscape schedules or Ansible playbooks
3. Execute `apt install package=version` to downgrade
4. Verify package version via `dpkg -l`

**Rollback Time**: 15–30 minutes (online sites), 1–7 days (air-gapped sites)

**Limitations**:
- Air-gapped sites: Rollback package must be present in local mirror
- APT pinning requires careful configuration to avoid dependency conflicts

---

### Mobile (iOS/iPadOS + Android) Rollback

**Strategy**: Assignment/remove or track/version strategies.

**iOS/iPadOS (Intune + VPP)**:
1. Remove assignment for failing version
2. Reassign previous version (if retained in VPP)
3. Device updates app on next MDM check-in

**Limitations**:
- Public store apps: Rollback typically not supported (Apple controls versioning)
- LOB apps: Rollback feasible if previous version retained (90-day retention policy)

**Android (Managed Google Play)**:
1. Update managed Google Play track to previous version
2. Remove assignment for failing version
3. Reassign previous version from track

**Limitations**:
- Private apps: Rollback depends on what versions are retained/published to tracks
- BYOD devices: Require user action for rollback (not fully automated)

**Rollback Time**: 1–24 hours (depends on device check-in frequency)

---

## Incident Response During Rollout

### P0/P1 Incident (Critical)

**Definition**: Security breach, data loss, widespread outages, or critical functionality failure.

**Actions**:
1. **Immediately halt** all in-progress ring deployments (pause promotion)
2. **Initiate rollback** for affected rings (execute plane-specific rollback strategy)
3. **Activate incident response team** (Endpoint Ops + Security + Platform Admin)
4. **Notify CAB** within 1 hour (incident summary, affected scope, remediation plan)
5. **Root cause analysis** within 24 hours (post-incident report to CAB)
6. **Remediation approval** required before resuming rollout

**Rollback SLA**: ≤ 4 hours from incident detection to rollback completion

---

### P2 Incident (High)

**Definition**: Elevated failure rate (> 10%), significant user impact, or operational disruption.

**Actions**:
1. **Pause** current ring deployment (do not promote to next ring)
2. **Investigate** failure root cause (analyze telemetry, failure reasons, user feedback)
3. **Remediate** via hotfix or configuration change (if feasible within 24 hours)
4. **Rollback** if remediation not feasible within 24 hours
5. **Notify CAB** within 4 hours (incident summary, remediation plan)

**Rollback Decision**: Endpoint Ops + Platform Admin (no CAB approval required for P2 rollback)

---

### P3 Incident (Medium)

**Definition**: Moderate failure rate (5–10%), isolated user issues, or minor functionality degradation.

**Actions**:
1. **Monitor** telemetry for 24–48 hours (do not pause deployment)
2. **Collect** user feedback and failure analysis
3. **Remediate** via support tickets or configuration adjustments
4. **Escalate to P2** if failure rate increases or user impact worsens
5. **Document** lessons learned for next version deployment

**Rollback Decision**: Not typically required for P3 (remediation via support)

---

## Telemetry and Dashboards

### Ring Rollout Health Dashboard

**Metrics per Ring**:
- Success rate (actual vs threshold)
- Time-to-compliance (actual vs threshold, per site class)
- Failure rate (broken down by failure reason)
- Incident count (P0/P1/P2/P3)
- Rollback execution count
- Promotion gate status (pass/fail)

**Visualization**:
- Ring progression chart (timeline view with gate checkpoints)
- Success rate trend line (per ring, over time)
- Failure analysis pie chart (top 5 failure reasons)
- Time-to-compliance histogram (per site class)

**Alerts**:
- **Critical**: Success rate falls below threshold (trigger rollback consideration)
- **High**: Time-to-compliance exceeds threshold (trigger remediation)
- **Medium**: Failure rate trend upward (early warning)

---

## Related Documentation

- [Architecture Overview](architecture-overview.md)
- [Control Plane Design](control-plane-design.md)
- [Risk Model](risk-model.md)
- [Evidence Pack Schema](evidence-pack-schema.md)
- [Execution Plane Connectors](execution-plane-connectors.md)

---

**Ring Model v1.0 — Thresholds are PROVISIONAL and subject to calibration after Phase 1 deployment.**
