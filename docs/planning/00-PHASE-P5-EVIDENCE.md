# Phase P5: Evidence & CAB Workflow

**Duration**: 2 weeks  
**Owner**: CAB Evidence & Governance Engineer  
**Prerequisites**: P4 complete  
**Status**: 🔴 NOT STARTED

---

## Objective

Implement evidence-first governance — every CAB submission includes a complete, immutable evidence pack. Risk scoring is deterministic and versioned. Approval workflow is auditable and exception-aware.

---

## Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P5.1 | Evidence pack schema & models | All required fields per CLAUDE.md |
| P5.2 | Evidence pack generation service | Auto-generate packs for deployment intents |
| P5.3 | Risk scoring engine | Deterministic scoring per CLAUDE.md formula |
| P5.4 | CAB workflow enhancement | Complete approval flow with evidence |
| P5.5 | Exception management | Expiry dates, compensating controls, security review |
| P5.6 | ≥90% test coverage | Evidence generation tested |

---

## Technical Specifications

### P5.1: Evidence Pack Schema

**Location**: `backend/apps/evidence_store/models.py`

```python
class EvidencePack(models.Model):
    """
    Immutable evidence pack linking all relevant information for CAB approval.
    
    Required fields per CLAUDE.md:
    - artifact_hashes (SHA-256)
    - artifact_signatures (code-signing evidence)
    - sbom_data (SPDX or CycloneDX)
    - vulnerability_scan_results (pass/fail/exception)
    - policy_decision (APPROVED/DENIED with reason)
    - install_instructions (how to install)
    - uninstall_instructions (how to uninstall)
    - detection_method (registry/file/custom)
    - rollout_plan (rings, schedule, targeting, exclusions)
    - rollback_plan (plane-specific strategies)
    - test_evidence (lab + Ring 0 results)
    - exception_records (expiry + compensating controls)
    - created_at (timestamp)
    - version (e.g., "1.0", "1.1" for re-approval)
    """
    
    deployment_intent = models.ForeignKey('deployment_intents.DeploymentIntent')
    
    # Core artifact evidence
    artifact_sha256 = models.CharField(max_length=64)
    artifact_signature = models.TextField()  # Code-signing cert + signature
    artifact_size_bytes = models.BigIntegerField()
    artifact_publisher = models.CharField(max_length=255)
    
    # Supply chain
    sbom_format = models.CharField(max_length=20, choices=[('spdx', 'SPDX'), ('cyclonedx', 'CycloneDX')])
    sbom_data = models.JSONField()  # Full SBOM
    
    # Security assessment
    vuln_scan_tool = models.CharField(max_length=50)  # Trivy, Grype, Snyk, etc.
    vuln_scan_results = models.JSONField()  # Critical, High, Medium, Low counts + details
    vuln_scan_passed = models.BooleanField()  # True if no Critical/High
    
    # Installation details
    install_command = models.TextField()  # Silent install command
    install_timeout_seconds = models.IntegerField(default=600)
    uninstall_command = models.TextField()
    uninstall_timeout_seconds = models.IntegerField(default=300)
    detection_method = models.CharField(max_length=50)  # registry, file, productcode, custom
    detection_query = models.TextField()  # Query to check if installed
    
    # Deployment strategy
    rollout_plan = models.JSONField()  # {ring_1: {users: 100, days: 1}, ...}
    rollback_plan = models.JSONField()  # Plane-specific rollback strategies
    
    # Test results
    test_evidence = models.JSONField()  # Lab + Ring 0 test results
    test_summary = models.CharField(max_length=20, choices=[('pass', 'Pass'), ('fail', 'Fail'), ('partial', 'Partial')])
    
    # Policy & compliance
    policy_violations = models.JSONField(default=dict)  # Constraint violations (if any)
    policy_approved = models.BooleanField(default=False)
    
    # Exception tracking
    has_exceptions = models.BooleanField(default=False)
    exception_count = models.IntegerField(default=0)
    
    # Versioning
    version = models.CharField(max_length=10, default="1.0")
    previous_version = models.ForeignKey('self', null=True, on_delete=models.SET_NULL)
    
    # Audit trail
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT)
    is_immutable = models.BooleanField(default=True)  # Prevents accidental modification
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['deployment_intent', '-created_at']),
            models.Index(fields=['version']),
        ]
```

**Exception Model** (`backend/apps/evidence_store/models.py`):

```python
class EvidenceException(models.Model):
    """
    Exceptions to evidence pack requirements (e.g., accepted vulnerabilities).
    
    Must have:
    - Expiry date (never permanent)
    - Compensating controls
    - Security Reviewer approval
    """
    
    evidence_pack = models.ForeignKey(EvidencePack, on_delete=models.CASCADE)
    exception_type = models.CharField(max_length=50)  # vuln_high, policy_violation, etc.
    description = models.TextField()
    
    # Approval tracking
    approved_by = models.ForeignKey(User, on_delete=models.PROTECT)  # Must be Security Reviewer
    approved_at = models.DateTimeField(auto_now_add=True)
    
    # Expiry (never permanent)
    expires_at = models.DateTimeField()  # Required, enforced in validation
    days_until_expiry = models.IntegerField()  # Cached for dashboard
    
    # Compensating controls
    compensating_controls = models.TextField()  # What mitigates the risk
    compensating_control_verification = models.TextField()  # How to verify
    
    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.PROTECT, related_name='created_exceptions')
    
    class Meta:
        ordering = ['expires_at']
```

### P5.2: Evidence Pack Generation Service

**Location**: `backend/apps/evidence_store/services.py`

```python
class EvidencePackGenerator:
    """
    Auto-generates evidence packs from deployment intents + build artifacts.
    
    Process:
    1. Retrieve deployment intent
    2. Fetch artifact + build metadata
    3. Query vulnerability scan results
    4. Evaluate policy constraints
    5. Gather test results
    6. Create immutable evidence pack
    """
    
    def generate_evidence_pack(self, deployment_intent_id: str) -> EvidencePack:
        """
        Generate complete evidence pack for CAB submission.
        
        Raises:
            ValueError: If required data missing
            EvidenceGenerationError: If scan/policy evaluation fails
        """
        intent = DeploymentIntent.objects.get(id=deployment_intent_id)
        
        # 1. Gather artifact data
        artifact = self._fetch_artifact_metadata(intent.artifact_id)
        
        # 2. Get vulnerability scan results
        vuln_results = self._fetch_vulnerability_scan(artifact.sha256)
        if not vuln_results['passed'] and not self._has_approved_exception(artifact.sha256):
            raise EvidenceGenerationError(f"Vulnerability scan failed: {vuln_results['critical_count']} critical")
        
        # 3. Evaluate policy constraints
        policy_result = PolicyEngine().evaluate(intent)
        
        # 4. Get test results from Ring 0 (Lab)
        test_results = self._fetch_ring_0_tests(intent.app_name, intent.version)
        
        # 5. Create evidence pack
        evidence = EvidencePack.objects.create(
            deployment_intent=intent,
            artifact_sha256=artifact.sha256,
            artifact_signature=self._get_signature(artifact),
            sbom_data=artifact.sbom,
            vuln_scan_results=vuln_results,
            vuln_scan_passed=vuln_results['passed'],
            install_command=intent.install_command,
            uninstall_command=intent.uninstall_command,
            detection_method=intent.detection_method,
            detection_query=intent.detection_query,
            rollout_plan=intent.rollout_plan,
            rollback_plan=intent.rollback_plan,
            test_evidence=test_results,
            policy_violations=policy_result.get('violations', {}),
            policy_approved=policy_result.get('approved', False),
            created_by=self._get_current_user(),
        )
        
        # 6. Link exceptions
        for exception in self._find_approved_exceptions(artifact.sha256):
            evidence.exceptions.add(exception)
        
        return evidence
```

### P5.3: Risk Scoring Engine

**Location**: `backend/apps/evidence_store/risk_scoring.py`

**Formula** (per CLAUDE.md):
```
RiskScore = clamp(0..100, Σ(weight_i * normalized_factor_i))

Factors:
- artifact_age: Days since build (weight: 5)
- test_coverage: % of code tested (weight: 15)
- vulnerability_count: High + Critical vulns (weight: 25)
- policy_violations: Constraint violations (weight: 20)
- exception_count: Active exceptions (weight: 15)
- ring_0_failures: Lab test failures (weight: 10)
- dependency_risk: Transitive dependencies (weight: 10)

Normalization rubric (example for vulnerabilities):
- 0 vulnerabilities → 0 risk
- 1-5 vulns → 20 risk (partial)
- 6-10 vulns → 50 risk (moderate)
- 11+ vulns → 100 risk (critical)
```

```python
class RiskScoringEngine:
    """
    Deterministic, versioned risk scoring for deployment intents.
    """
    
    RISK_MODEL_VERSION = "1.0"  # Must be versioned
    
    def compute_risk_score(self, evidence_pack: EvidencePack) -> RiskScoreResult:
        """
        Compute risk score with all contributing factors.
        
        Returns:
            {
              "score": 65,  # 0-100
              "model_version": "1.0",
              "factors": {
                "vuln_count": {"raw": 3, "weight": 25, "normalized": 30},
                "test_coverage": {"raw": 85, "weight": 15, "normalized": 10},
                ...
              },
              "recommendation": "CAUTION",  # LOW, MODERATE, CAUTION, HIGH, CRITICAL
            }
        """
        
        factors = {}
        total_weighted_score = 0
        
        # Factor 1: Vulnerability count
        vuln_normalized = self._normalize_vulnerability_risk(
            evidence_pack.vuln_scan_results['critical_count'],
            evidence_pack.vuln_scan_results['high_count']
        )
        factors['vulnerabilities'] = {
            'weight': 25,
            'normalized': vuln_normalized,
            'weighted': 25 * vuln_normalized / 100,
        }
        total_weighted_score += factors['vulnerabilities']['weighted']
        
        # Factor 2: Test coverage
        test_coverage = self._extract_test_coverage(evidence_pack.test_evidence)
        test_normalized = 100 - test_coverage  # Lower coverage = higher risk
        factors['test_coverage'] = {
            'weight': 15,
            'normalized': test_normalized,
            'weighted': 15 * test_normalized / 100,
        }
        total_weighted_score += factors['test_coverage']['weighted']
        
        # ... more factors ...
        
        final_score = self._clamp(total_weighted_score, 0, 100)
        
        return RiskScoreResult(
            score=final_score,
            factors=factors,
            model_version=self.RISK_MODEL_VERSION,
            recommendation=self._get_recommendation(final_score),
        )
    
    def _normalize_vulnerability_risk(self, critical_count: int, high_count: int) -> float:
        """Normalization rubric for vulnerabilities."""
        total_severe = critical_count + (high_count * 0.5)
        if total_severe == 0:
            return 0
        elif total_severe <= 3:
            return 20
        elif total_severe <= 7:
            return 50
        else:
            return 100
```

### P5.4: CAB Workflow Enhancement

**Location**: `backend/apps/cab_workflow/models.py` + `views.py`

```python
class CABApprovalRequest(models.Model):
    """
    CAB approval request linking evidence pack and policy decision.
    """
    
    evidence_pack = models.OneToOneField(EvidencePack, on_delete=models.PROTECT)
    deployment_intent = models.ForeignKey(DeploymentIntent, on_delete=models.PROTECT)
    
    # Risk assessment
    risk_score = models.IntegerField()  # From RiskScoringEngine
    risk_model_version = models.CharField(max_length=10)
    risk_threshold_exceeded = models.BooleanField()  # Score > 50 requires CAB
    
    # Submission
    submitted_at = models.DateTimeField(auto_now_add=True)
    submitted_by = models.ForeignKey(User, on_delete=models.PROTECT)
    submission_justification = models.TextField()
    
    # Review
    status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending Review'),
        ('approved', 'Approved'),
        ('approved_with_conditions', 'Approved With Conditions'),
        ('denied', 'Denied'),
    ])
    
    reviewed_at = models.DateTimeField(null=True)
    reviewed_by = models.ForeignKey(User, null=True, on_delete=models.SET_NULL, related_name='reviewed_cabs')
    review_notes = models.TextField(blank=True)
    
    # Conditions (if applicable)
    approval_conditions = models.JSONField(default=dict)  # {condition_1: {...}, ...}
    
    class Meta:
        ordering = ['-submitted_at']
```

**Workflow endpoints**:
```
POST /api/v1/cab/submit/
- Submit evidence pack for review
- Auto-compute risk score
- Only submit if risk > 50 OR policy_violations exist
- Email notification to CAB members

GET /api/v1/cab/pending/
- List pending approval requests
- Filter by status, risk level
- Show evidence summary

POST /api/v1/cab/{id}/approve/
- Approve with optional conditions
- Create event store record
- Trigger deployment execution

POST /api/v1/cab/{id}/deny/
- Deny with required reason
- Create event store record
- Notify submitter
```

### P5.5: Exception Management

**Location**: `backend/apps/evidence_store/exception_manager.py`

```python
class ExceptionManager:
    """
    Manage exceptions to policy requirements.
    
    Rules:
    - Every exception must have expiry date (no permanent exceptions)
    - Compensating controls must be documented and verified
    - Security Reviewer must approve
    - Exceptions tracked for audit
    """
    
    def request_exception(
        self,
        exception_type: str,
        evidence_pack: EvidencePack,
        description: str,
        compensating_controls: str,
        expires_at: datetime,
    ) -> EvidenceException:
        """
        Request exception (creates pending approval).
        
        Args:
            exception_type: vuln_high, policy_violation, etc.
            evidence_pack: The evidence pack
            description: Why exception is needed
            compensating_controls: How risk is mitigated
            expires_at: When exception expires (required)
        """
        
        if expires_at <= now():
            raise ValueError("Expiry date must be in future")
        
        exception = EvidenceException.objects.create(
            evidence_pack=evidence_pack,
            exception_type=exception_type,
            description=description,
            compensating_controls=compensating_controls,
            expires_at=expires_at,
            days_until_expiry=self._days_until(expires_at),
            created_by=self._get_current_user(),
        )
        
        # Email security reviewers for approval
        self._notify_security_reviewers(exception)
        
        return exception
    
    def approve_exception(
        self,
        exception_id: str,
        security_reviewer: User,
        verification_steps: str,
    ) -> EvidenceException:
        """
        Security Reviewer approves exception.
        """
        exception = EvidenceException.objects.get(id=exception_id)
        
        if not self._is_security_reviewer(security_reviewer):
            raise PermissionError("Only Security Reviewers can approve exceptions")
        
        exception.approved_by = security_reviewer
        exception.approved_at = now()
        exception.compensating_control_verification = verification_steps
        exception.save()
        
        # Log to event store
        EventStore.log(
            event_type='exception_approved',
            correlation_id=self._get_correlation_id(),
            data={'exception_id': exception_id, 'reviewer': security_reviewer.email},
        )
        
        return exception
```

---

## Quality Gates

- [ ] Evidence pack schema models created
- [ ] Risk scoring deterministic and versioned
- [ ] All required fields present per CLAUDE.md
- [ ] CAB workflow endpoints implemented
- [ ] Exception management with expiry enforcement
- [ ] ≥90% test coverage
- [ ] Evidence pack immutability enforced
- [ ] All tests pass

---

## Files to Create/Modify

```
backend/apps/evidence_store/
├── models.py (MODIFY) - Add EvidencePack, EvidenceException
├── services.py (CREATE) - EvidencePackGenerator
├── risk_scoring.py (CREATE) - RiskScoringEngine
├── exception_manager.py (CREATE) - ExceptionManager
├── views.py (MODIFY) - Evidence endpoints
├── serializers.py (MODIFY) - Evidence serializers
├── urls.py (MODIFY) - Evidence routes
└── tests/
    ├── test_models.py (CREATE)
    ├── test_services.py (CREATE)
    ├── test_risk_scoring.py (CREATE)
    └── test_exception_manager.py (CREATE)

backend/apps/cab_workflow/
├── models.py (MODIFY) - CABApprovalRequest
├── views.py (MODIFY) - Approval endpoints
├── serializers.py (MODIFY) - CAB serializers
└── tests/
    └── test_workflow.py (CREATE)

docs/
├── architecture/
│   ├── evidence-pack-schema.md (CREATE)
│   ├── risk-model.md (CREATE)
│   └── cab-workflow.md (CREATE)
└── architecture/
    └── exception-management.md (CREATE)
```

---

## Success Criteria

✅ **P5 is COMPLETE when**:
1. Evidence pack schema captures all required fields
2. Evidence pack generation is fully automated
3. Risk scoring is deterministic and versioned
4. CAB workflow supports approve/deny/conditions
5. Exceptions require expiry + compensating controls
6. All evidence immutable once created
7. ≥90% test coverage
8. All event store records created for audit trail

**Target Completion**: 2 weeks (February 5-19, 2026)
