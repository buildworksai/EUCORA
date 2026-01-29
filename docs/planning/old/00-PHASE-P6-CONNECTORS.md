# Phase P6: Execution Plane Connectors

**Duration**: 2 weeks
**Owner**: Execution Plane Connector Developer
**Prerequisites**: P5 complete
**Status**: 🔴 NOT STARTED

---

## Objective

Implement production-ready connectors to all execution planes (Intune, Jamf, SCCM, Landscape, Ansible). All operations idempotent with deterministic mapping from control-plane intents to plane-specific objects.

---

## Deliverables

| ID | Deliverable | Acceptance Criteria |
|----|-------------|---------------------|
| P6.1 | Intune connector (Microsoft Graph) | Deploy packages, assignments, track telemetry |
| P6.2 | Jamf Pro connector | Packages, policies, smart groups, DPs |
| P6.3 | SCCM connector | Packages, collections, DPs, constrained delegation |
| P6.4 | Landscape connector | Scheduling, compliance reporting, mirrors |
| P6.5 | Ansible (AWX/Tower) connector | Playbooks, package install/remediation |
| P6.6 | ≥90% test coverage | Integration tests per connector |

---

## Technical Specifications

### Connector Pattern (All Connectors)

**Base Architecture**:
```python
class ExecutionPlaneConnector(ABC):
    """
    Base class for all execution plane connectors.

    Requirements:
    - Idempotent operations (safe retries)
    - Deterministic mapping (same intent → same output)
    - Correlation ID tracking (audit trail)
    - Error classification (transient/permanent/policy)
    - Rate limit handling
    """

    def __init__(self, correlation_id: str):
        self.correlation_id = correlation_id
        self.http_client = ResilientHTTPClient(self.SERVICE_NAME)

    @abstractmethod
    def publish_package(
        self,
        package_intent: PackageIntent,
    ) -> PublishResult:
        """Publish package to execution plane."""
        pass

    @abstractmethod
    def create_assignment(
        self,
        assignment_intent: AssignmentIntent,
    ) -> AssignmentResult:
        """Create user/device assignment."""
        pass

    @abstractmethod
    def query_state(
        self,
        assignment_id: str,
    ) -> DeviceState:
        """Query current device state."""
        pass

    @abstractmethod
    def remediate(
        self,
        assignment_id: str,
        intended_state: str,
    ) -> RemediationResult:
        """Remediate drift (bring to intended state)."""
        pass

    @abstractmethod
    def rollback(
        self,
        assignment_id: str,
        target_version: str,
    ) -> RollbackResult:
        """Rollback to previous version."""
        pass
```

### P6.1: Intune Connector

**Implementation**:
```python
class IntuneConnector(ExecutionPlaneConnector):
    """
    Microsoft Graph API integration for Intune.

    Uses:
    - Entra ID app registration (cert-based auth)
    - microsoft.graph endpoints:
      - /deviceAppManagement/mobileApps (create Win32/iOS/Android apps)
      - /deviceAppManagement/mobileAppAssignments (assign to groups)
      - /deviceManagement/managedDevices (query device state)
    - Handles Graph throttling + pagination
    """

    SERVICE_NAME = 'intune'

    def publish_package(self, intent: PackageIntent) -> PublishResult:
        """
        Create Win32 app in Intune.

        Idempotent: Uses app name + version as unique key
        Returns: app_id for assignment
        """

    def create_assignment(self, intent: AssignmentIntent) -> AssignmentResult:
        """
        Create mobile app assignment.

        Targets:
        - Entra ID groups
        - Device filters
        - Assignment intent (available/required/uninstall)
        """

    def query_state(self, assignment_id: str) -> DeviceState:
        """
        Query device install status from Microsoft Graph.

        Handles:
        - Eventual consistency (eventual query)
        - Device filtering (online/offline)
        - Status mapping (pending/installed/failed)
        """
```

### P6.2: Jamf Pro Connector

```python
class JamfConnector(ExecutionPlaneConnector):
    """
    Jamf Pro API integration.

    Endpoints:
    - POST /packages (upload package)
    - POST /policies (create policy)
    - POST /smartgroups (create assignment group)
    - GET /mobiledevicecommands (query status)
    """

    SERVICE_NAME = 'jamf'

    # Similar pattern to Intune
    # Policy-based version pinning for rollback
```

### P6.3: SCCM Connector

```python
class SCCMConnector(ExecutionPlaneConnector):
    """
    System Center Configuration Manager (SCCM) integration.

    Uses:
    - PowerShell provider + constrained delegation
    - Strict SoD (no shared service principal with other connectors)
    - Operations:
      - Create packages
      - Create collections (targeting)
      - Distribute to DPs
      - Create deployments
    """

    SERVICE_NAME = 'sccm'

    # Windows legacy/offline support
    # DP management for air-gapped sites
```

### P6.4: Landscape Connector

```python
class LandscapeConnector(ExecutionPlaneConnector):
    """
    Canonical Landscape integration for Linux.

    Uses:
    - Landscape API / client tooling
    - Scheduling + compliance reporting
    - APT mirror management
    """

    SERVICE_NAME = 'landscape'

    # Linux package scheduling
    # Mirror management
```

### P6.5: Ansible Connector

```python
class AnsibleConnector(ExecutionPlaneConnector):
    """
    Ansible AWX/Tower integration.

    Uses:
    - AWX/Tower API
    - Playbooks for:
      - Package install
      - Package remediation
      - Repository mirror configuration
    """

    SERVICE_NAME = 'ansible'

    # Cross-platform playbook execution
```

---

## Quality Gates

- [ ] All connectors implement base interface
- [ ] All operations idempotent (safe retries)
- [ ] All operations include correlation_id
- [ ] Error classification implemented (transient/permanent/policy)
- [ ] Rate limit handling implemented
- [ ] ≥90% test coverage
- [ ] Integration tests per connector
- [ ] No hardcoded credentials (vault integration)

---

## Files to Create

```
backend/apps/connectors/
├── base.py (MODIFY) - ExecutionPlaneConnector base
├── intune.py (CREATE)
├── jamf.py (CREATE)
├── sccm.py (CREATE)
├── landscape.py (CREATE)
├── ansible.py (CREATE)
└── tests/
    ├── test_intune.py (CREATE)
    ├── test_jamf.py (CREATE)
    ├── test_sccm.py (CREATE)
    ├── test_landscape.py (CREATE)
    └── test_ansible.py (CREATE)

docs/modules/
├── intune/connector-spec.md (CREATE)
├── jamf/connector-spec.md (CREATE)
├── sccm/connector-spec.md (CREATE)
├── landscape/connector-spec.md (CREATE)
└── ansible/connector-spec.md (CREATE)
```

---

## Success Criteria

✅ **P6 is COMPLETE when**:
1. All 5 connectors implemented
2. All operations idempotent
3. All operations traceable (correlation_id)
4. ≥90% test coverage
5. Integration tests pass for each connector
6. Error handling comprehensive
7. Rate limiting implemented
8. All quality gates green

**Target Completion**: 2 weeks (February 19 - March 5, 2026)
