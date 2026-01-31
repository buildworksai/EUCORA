---
name: cab-workflow
description: CAB (Change Advisory Board) workflow patterns for EUCORA including evidence pack generation, risk scoring formulas, approval workflows, and exception management. Use when implementing CAB approvals, generating evidence packs, or calculating risk scores.
status: ✅ Working
last-validated: 2026-01-30
---

# CAB Workflow Patterns

Change Advisory Board governance patterns for the EUCORA platform.

---

## Quick Reference

| Component | Pattern |
|-----------|---------|
| Risk Threshold | > 50 requires CAB approval |
| Privileged Tooling | Always requires CAB |
| Evidence Pack | Immutable, WORM storage |
| Approval Record | Append-only event store |
| Exceptions | Expiry date + compensating controls |

---

## Risk Scoring Formula

### Formula (v1.0)

```
RiskScore = clamp(0..100, Σ(weight_i × normalized_factor_i))
```

Where `normalized_factor_i` is between 0.0 (no risk) and 1.0 (maximum risk).

### Risk Factors and Weights

| Factor | Weight | Examples |
|--------|--------|----------|
| Privilege Impact | 20 | Admin required, service install, kernel extensions |
| Supply Chain Trust | 15 | Signature validity, notarization, publisher reputation |
| Exploitability | 10 | Network listeners, exposed services, macros |
| Data Access | 10 | Credential store, wide filesystem access |
| SBOM/Vulnerability | 15 | Critical/High CVEs in dependencies |
| Blast Radius | 10 | Scope size, ring level, BU/site count |
| Operational Complexity | 10 | Offline import, reboots, sequencing |
| History | 10 | Prior incidents, failure rate, rollback difficulty |

### Implementation

```python
# backend/apps/policy_engine/risk_scoring.py
from dataclasses import dataclass
from typing import Dict

RISK_WEIGHTS_V1 = {
    "privilege_impact": 20,
    "supply_chain_trust": 15,
    "exploitability": 10,
    "data_access": 10,
    "sbom_vulnerability": 15,
    "blast_radius": 10,
    "operational_complexity": 10,
    "history": 10,
}

@dataclass
class RiskAssessment:
    score: float
    factors: Dict[str, float]
    model_version: str = "v1.0"
    requires_cab: bool = False

    @classmethod
    def calculate(cls, factors: Dict[str, float]) -> "RiskAssessment":
        """Calculate risk score from normalized factors."""
        score = sum(
            RISK_WEIGHTS_V1.get(k, 0) * v
            for k, v in factors.items()
        )
        score = max(0, min(100, score))  # Clamp 0-100

        return cls(
            score=score,
            factors=factors,
            requires_cab=score > 50,
        )

def assess_deployment_risk(deployment) -> RiskAssessment:
    """Assess risk for a deployment."""
    factors = {}

    # Privilege impact (weight: 20)
    if deployment.requires_admin:
        factors["privilege_impact"] = 1.0
    elif deployment.requires_service_install:
        factors["privilege_impact"] = 0.7
    else:
        factors["privilege_impact"] = 0.2

    # Supply chain trust (weight: 15)
    if deployment.artifact.is_signed and deployment.artifact.is_notarized:
        factors["supply_chain_trust"] = 0.1
    elif deployment.artifact.is_signed:
        factors["supply_chain_trust"] = 0.3
    else:
        factors["supply_chain_trust"] = 0.9

    # Exploitability (weight: 10) - network listeners, exposed services, macros
    if deployment.artifact.has_network_listeners:
        factors["exploitability"] = 1.0
    elif deployment.artifact.has_exposed_services:
        factors["exploitability"] = 0.7
    elif deployment.artifact.has_macros:
        factors["exploitability"] = 0.5
    else:
        factors["exploitability"] = 0.1

    # Data access (weight: 10) - credential store, filesystem access
    if deployment.artifact.accesses_credential_store:
        factors["data_access"] = 1.0
    elif deployment.artifact.has_wide_filesystem_access:
        factors["data_access"] = 0.7
    else:
        factors["data_access"] = 0.1

    # SBOM vulnerability (weight: 15)
    if deployment.artifact.has_critical_vulns:
        factors["sbom_vulnerability"] = 1.0
    elif deployment.artifact.has_high_vulns:
        factors["sbom_vulnerability"] = 0.7
    else:
        factors["sbom_vulnerability"] = 0.0

    # Blast radius (weight: 10)
    target_count = deployment.target_scope_size
    if target_count > 10000:
        factors["blast_radius"] = 1.0
    elif target_count > 1000:
        factors["blast_radius"] = 0.6
    else:
        factors["blast_radius"] = 0.2

    # Operational complexity (weight: 10) - offline import, reboots, sequencing
    if deployment.requires_offline_import:
        factors["operational_complexity"] = 1.0
    elif deployment.requires_reboot:
        factors["operational_complexity"] = 0.7
    elif deployment.requires_sequencing:
        factors["operational_complexity"] = 0.5
    else:
        factors["operational_complexity"] = 0.1

    # History (weight: 10) - prior incidents, failure rate, rollback difficulty
    if deployment.artifact.has_prior_incidents:
        factors["history"] = 1.0
    elif deployment.artifact.failure_rate > 0.1:
        factors["history"] = 0.7
    elif deployment.artifact.rollback_difficulty == "hard":
        factors["history"] = 0.5
    else:
        factors["history"] = 0.1

    return RiskAssessment.calculate(factors)
```

---

## Evidence Pack Schema

### Required Fields

```python
# backend/apps/evidence_store/models.py

class EvidencePack(TimeStampedModel, CorrelationIdModel):
    """Immutable evidence pack for CAB submission."""

    class Status(models.TextChoices):
        DRAFT = "draft"
        SUBMITTED = "submitted"
        APPROVED = "approved"
        REJECTED = "rejected"

    # Identity
    deployment = models.ForeignKey("deployments.DeploymentIntent", on_delete=models.PROTECT)
    version = models.CharField(max_length=16, default="1.0")

    # Artifact Evidence
    artifact_hash_sha256 = models.CharField(max_length=64)
    artifact_signature = models.TextField()
    artifact_signature_valid = models.BooleanField()

    # SBOM
    sbom_format = models.CharField(max_length=16)  # spdx, cyclonedx
    sbom_content = models.JSONField()

    # Vulnerability Scan
    scan_tool = models.CharField(max_length=32)  # trivy, grype, snyk
    scan_results = models.JSONField()
    scan_passed = models.BooleanField()
    critical_count = models.IntegerField(default=0)
    high_count = models.IntegerField(default=0)

    # Policy Decision
    policy_decision = models.CharField(max_length=16)  # pass, fail, exception
    policy_exceptions = models.JSONField(default=list)

    # Risk Assessment
    risk_score = models.DecimalField(max_digits=5, decimal_places=2)
    risk_factors = models.JSONField()
    risk_model_version = models.CharField(max_length=16, default="v1.0")

    # Rollout Plan
    rollout_rings = models.JSONField()  # [{ring: 1, schedule: ..., targeting: ...}]
    rollout_schedule = models.JSONField()

    # Rollback Plan
    rollback_strategy = models.CharField(max_length=32)  # supersedence, uninstall
    rollback_procedure = models.TextField()
    rollback_validated = models.BooleanField(default=False)

    # Test Evidence
    test_lab_passed = models.BooleanField()
    test_ring0_passed = models.BooleanField()
    test_evidence_urls = models.JSONField(default=list)

    # Exceptions (if any)
    exceptions = models.JSONField(default=list)  # [{id, expiry, controls, approver}]

    # Status
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.DRAFT)
    submitted_at = models.DateTimeField(null=True, blank=True)
    submitted_by = models.ForeignKey("core.User", on_delete=models.PROTECT, null=True)

    class Meta:
        ordering = ["-created_at"]
```

### Evidence Pack Generation

```python
# backend/apps/evidence_store/services.py

class EvidencePackGenerator:
    """Generate complete evidence pack for CAB submission."""

    async def generate(self, deployment) -> EvidencePack:
        """Generate evidence pack from deployment."""
        artifact = deployment.artifact

        # Collect all evidence
        evidence = EvidencePack(
            deployment=deployment,

            # Artifact evidence
            artifact_hash_sha256=artifact.sha256_hash,
            artifact_signature=artifact.signature,
            artifact_signature_valid=await self._verify_signature(artifact),

            # SBOM
            sbom_format=artifact.sbom.format,
            sbom_content=artifact.sbom.content,

            # Vulnerability scan
            scan_tool=settings.VULN_SCANNER,
            scan_results=await self._run_scan(artifact),
            scan_passed=await self._evaluate_scan_policy(artifact),
            critical_count=artifact.critical_vuln_count,
            high_count=artifact.high_vuln_count,

            # Policy decision
            policy_decision=await self._evaluate_policy(artifact),
            policy_exceptions=await self._get_exceptions(artifact),

            # Risk assessment
            risk_score=deployment.risk_score,
            risk_factors=deployment.risk_factors,
            risk_model_version="v1.0",

            # Rollout plan
            rollout_rings=deployment.rollout_plan.rings,
            rollout_schedule=deployment.rollout_plan.schedule,

            # Rollback plan
            rollback_strategy=deployment.rollback_strategy,
            rollback_procedure=deployment.rollback_procedure,
            rollback_validated=await self._check_rollback_validated(deployment),

            # Test evidence
            test_lab_passed=await self._check_lab_tests(deployment),
            test_ring0_passed=await self._check_ring0_tests(deployment),
            test_evidence_urls=await self._collect_test_urls(deployment),
        )

        await evidence.asave()
        return evidence
```

---

## CAB Approval Workflow

### States

```
┌─────────┐    submit    ┌───────────┐
│  DRAFT  │────────────▶│ SUBMITTED │
└─────────┘              └─────┬─────┘
                               │
                    ┌──────────┼──────────┐
                    │          │          │
                    ▼          ▼          ▼
              ┌──────────┐ ┌────────┐ ┌────────────┐
              │ APPROVED │ │REJECTED│ │ CONDITIONS │
              └──────────┘ └────────┘ └────────────┘
                                            │
                                            ▼
                                      ┌──────────┐
                                      │ APPROVED │
                                      └──────────┘
```

### Approval Service

```python
# backend/apps/cab_workflow/services.py

class CABApprovalService:
    """CAB approval workflow service."""

    async def submit_for_approval(
        self,
        evidence_pack: EvidencePack,
        submitter: User,
    ) -> CABSubmission:
        """Submit evidence pack for CAB approval."""
        # Validate evidence pack is complete
        await self._validate_evidence_complete(evidence_pack)

        # Check risk threshold
        if evidence_pack.risk_score <= 50:
            # Auto-approve low risk
            return await self._auto_approve(evidence_pack, "Low risk - auto-approved")

        # Create CAB submission
        submission = await CABSubmission.objects.acreate(
            evidence_pack=evidence_pack,
            submitted_by=submitter,
            status=CABSubmission.Status.PENDING,
            correlation_id=evidence_pack.correlation_id,
        )

        # Notify CAB approvers
        await self._notify_approvers(submission)

        return submission

    async def approve(
        self,
        submission: CABSubmission,
        approver: User,
        conditions: list[str] = None,
    ) -> CABApproval:
        """Approve a CAB submission."""
        # Validate approver role
        if not approver.has_role("cab_approver"):
            raise PermissionError("User is not a CAB approver")

        # Cannot approve own submission
        if submission.submitted_by == approver:
            raise PermissionError("Cannot approve own submission")

        # Create approval record
        approval = await CABApproval.objects.acreate(
            submission=submission,
            approver=approver,
            decision=CABApproval.Decision.APPROVED,
            conditions=conditions or [],
            correlation_id=submission.correlation_id,
        )

        # Update submission status
        submission.status = CABSubmission.Status.APPROVED
        submission.approved_at = timezone.now()
        await submission.asave()

        # Log to event store (immutable)
        await EventStore.objects.acreate(
            event_type="cab.approved",
            correlation_id=submission.correlation_id,
            data={
                "submission_id": str(submission.id),
                "evidence_pack_id": str(submission.evidence_pack_id),
                "approver_id": str(approver.id),
                "conditions": conditions,
            },
        )

        return approval

    async def reject(
        self,
        submission: CABSubmission,
        approver: User,
        reason: str,
    ) -> CABApproval:
        """Reject a CAB submission."""
        approval = await CABApproval.objects.acreate(
            submission=submission,
            approver=approver,
            decision=CABApproval.Decision.REJECTED,
            rejection_reason=reason,
            correlation_id=submission.correlation_id,
        )

        submission.status = CABSubmission.Status.REJECTED
        await submission.asave()

        return approval
```

---

## Exception Management

### Exception Record

```python
class VulnerabilityException(TimeStampedModel, CorrelationIdModel):
    """Exception for vulnerability findings."""

    # What is being excepted
    vulnerability_id = models.CharField(max_length=64)  # CVE-2024-XXXX
    artifact = models.ForeignKey("packaging.Artifact", on_delete=models.PROTECT)

    # Why (justification)
    justification = models.TextField()
    compensating_controls = models.TextField()

    # When it expires (MANDATORY)
    expires_at = models.DateTimeField()

    # Who approved
    approved_by = models.ForeignKey("core.User", on_delete=models.PROTECT)
    approved_at = models.DateTimeField(auto_now_add=True)

    # Status
    is_active = models.BooleanField(default=True)
    revoked_at = models.DateTimeField(null=True, blank=True)
    revoked_by = models.ForeignKey("core.User", null=True, on_delete=models.SET_NULL)
    revoked_reason = models.TextField(blank=True)

    class Meta:
        constraints = [
            models.CheckConstraint(
                check=models.Q(expires_at__gt=models.F("created_at")),
                name="exception_must_have_future_expiry",
            ),
        ]
```

### Exception Workflow

```python
class ExceptionService:
    """Manage vulnerability exceptions."""

    async def create_exception(
        self,
        vulnerability_id: str,
        artifact,
        justification: str,
        compensating_controls: str,
        expires_at: datetime,
        requestor: User,
        approver: User,
    ) -> VulnerabilityException:
        """Create a vulnerability exception."""
        # Validate approver is Security Reviewer
        if not approver.has_role("security_reviewer"):
            raise PermissionError("Security Reviewer approval required")

        # Validate expiry is in future
        if expires_at <= timezone.now():
            raise ValueError("Expiry must be in the future")

        # Max 90 days for exceptions
        max_expiry = timezone.now() + timedelta(days=90)
        if expires_at > max_expiry:
            raise ValueError("Exception cannot exceed 90 days")

        exception = await VulnerabilityException.objects.acreate(
            vulnerability_id=vulnerability_id,
            artifact=artifact,
            justification=justification,
            compensating_controls=compensating_controls,
            expires_at=expires_at,
            approved_by=approver,
            correlation_id=generate_correlation_id("exc"),
        )

        # Log the exception
        logger.info(
            f"Exception created for {vulnerability_id}",
            extra={
                "exception_id": str(exception.id),
                "artifact_id": str(artifact.id),
                "expires_at": expires_at.isoformat(),
            }
        )

        return exception
```

---

## Ring Gates

### Promotion Gates

| Ring | Success Rate | Time-to-Compliance | Additional Requirements |
|------|-------------|-------------------|------------------------|
| Ring 1 (Canary) | ≥ 98% | ≤ 24h | Rollback validated |
| Ring 2 (Pilot) | ≥ 97% | ≤ 24h | CAB approved if Risk > 50 |
| Ring 3 (Department) | ≥ 99% | ≤ 24h | All previous gates passed |
| Ring 4 (Global) | ≥ 99% | ≤ 24h | Stakeholder sign-off |

### Gate Evaluation

```python
class PromotionGateService:
    """Evaluate ring promotion gates."""

    THRESHOLDS = {
        1: {"success_rate": 0.98, "time_to_compliance_hours": 24},
        2: {"success_rate": 0.97, "time_to_compliance_hours": 24},
        3: {"success_rate": 0.99, "time_to_compliance_hours": 24},
        4: {"success_rate": 0.99, "time_to_compliance_hours": 24},
    }

    async def can_promote(
        self,
        deployment,
        target_ring: int,
    ) -> tuple[bool, list[str]]:
        """Check if deployment can promote to target ring."""
        issues = []
        thresholds = self.THRESHOLDS[target_ring]

        # Check success rate
        success_rate = await self._get_success_rate(deployment)
        if success_rate < thresholds["success_rate"]:
            issues.append(
                f"Success rate {success_rate:.1%} below threshold {thresholds['success_rate']:.0%}"
            )

        # Check time-to-compliance
        avg_compliance_time = await self._get_avg_compliance_time(deployment)
        if avg_compliance_time > thresholds["time_to_compliance_hours"]:
            issues.append(
                f"Compliance time {avg_compliance_time}h exceeds {thresholds['time_to_compliance_hours']}h"
            )

        # Check rollback validation
        if not deployment.rollback_validated:
            issues.append("Rollback not validated")

        # Check CAB approval for Ring 2+ (CRITICAL: uses AND logic)
        # Per CLAUDE.md: CAB approval only required when BOTH conditions are true:
        # - Risk > 50 AND targeting Ring 2+ (Pilot or higher)
        # Ring 1 (Canary) bypasses CAB even for high-risk artifacts
        if target_ring >= 2 and deployment.risk_score > 50:
            if not await self._has_cab_approval(deployment):
                issues.append("CAB approval required for Risk > 50 when targeting Ring 2+")

        # Check no active incidents
        if await self._has_active_incidents(deployment):
            issues.append("Active incidents block promotion")

        return len(issues) == 0, issues
```

---

## API Endpoints

```python
# CAB Workflow Endpoints
POST   /api/v1/cab/submit/                      # Submit for CAB approval
GET    /api/v1/cab/pending/                     # List pending approvals
POST   /api/v1/cab/{id}/approve/                # Approve submission
POST   /api/v1/cab/{id}/reject/                 # Reject submission
GET    /api/v1/cab/{id}/evidence/               # Get evidence pack

# Exception Management
POST   /api/v1/exceptions/                      # Create exception
GET    /api/v1/exceptions/                      # List active exceptions
DELETE /api/v1/exceptions/{id}/                 # Revoke exception

# Risk Scoring
POST   /api/v1/risk/assess/                     # Assess risk for deployment
GET    /api/v1/risk/factors/                    # Get risk factors and weights
```

---

## Checklist

### Evidence Pack Generation

```
☐ Artifact hash (SHA-256) computed
☐ Signature verified
☐ SBOM generated (SPDX or CycloneDX)
☐ Vulnerability scan completed
☐ Risk score calculated
☐ Rollout plan documented
☐ Rollback plan documented and validated
☐ Test evidence collected
```

### CAB Submission

```
☐ Evidence pack complete
☐ Risk score > 50? → CAB required
☐ Privileged tooling? → CAB required
☐ Exceptions documented with expiry
☐ Submitted by authorized user
☐ Approval recorded in event store
```

---

## Anti-Patterns

| ❌ FORBIDDEN | ✅ CORRECT |
|--------------|------------|
| Publishing without CAB (Risk > 50) | CAB approval mandatory |
| Exception without expiry | All exceptions expire ≤90 days |
| Modifying evidence pack | Immutable - version and resubmit |
| Same person submit + approve | Separate submitter and approver |
| Skipping rollback validation | Rollback tested before Ring 2 |
