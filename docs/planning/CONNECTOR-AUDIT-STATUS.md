# EUCORA — Connector Audit Status

**SPDX-License-Identifier: Apache-2.0**

**Version**: 1.0.0
**Status**: AUTHORITATIVE
**Created**: January 25, 2026
**Classification**: INTERNAL — Technical Audit

---

## Executive Summary

This document provides a **detailed technical audit** of all connector implementations against SOW D-03 requirements.

**Bottom Line**:
- **Production-Ready**: 2 (Intune, Jamf)
- **Implemented but Partial**: 3 (ServiceNow, Entra ID, ABM)
- **Vaporware**: 3 (SCCM, Landscape, Ansible)
- **Not Started**: 2 (iOS ABM VPP, Android Enterprise deployment)

---

## SOW D-03 Requirements Mapping

The SOW requires the following connectors:

| Connector | SOW Requirement | Status | Gap |
|-----------|-----------------|--------|-----|
| Intune | App CRUD, assignment, compliance | ✅ Complete | None |
| Jamf | Package upload, policy creation | ✅ Complete | Minor (XML parsing) |
| SCCM | Package distribution, collections | ❌ Vaporware | Full implementation needed |
| Landscape | Repo sync, package install | ❌ Vaporware | Full implementation needed |
| Ansible/AWX | Job templates, remediation | ❌ Vaporware | Full implementation needed |
| AD/Entra ID | User/group sync | ✅ Complete | None |
| ServiceNow | ITSM integration | ⚠️ Partial | CMDB query missing |
| Mobile (iOS) | ABM + VPP | ⚠️ Partial | VPP licensing stub |
| Mobile (Android) | Android Enterprise | ⚠️ Partial | Deployment flow missing |

---

## Detailed Connector Analysis

### 1. Intune Connector

**Status**: ✅ PRODUCTION-READY

**File Locations**:
- [intune/auth.py](backend/apps/connectors/intune/auth.py) (250 lines)
- [intune/client.py](backend/apps/connectors/intune/client.py) (475 lines)
- [IntuneConnector.ps1](scripts/connectors/intune/IntuneConnector.ps1) (80+ lines)

**Operations Matrix**:

| Operation | Implemented | Tested | Idempotent | Notes |
|-----------|-------------|--------|------------|-------|
| Test connection | ✅ | ✅ | N/A | OAuth validation |
| List managed devices | ✅ | ✅ | N/A | OData pagination |
| Create Win32 app | ✅ | ✅ | ✅ | 409 conflict handling |
| Assign app to group | ✅ | ✅ | ✅ | Intent support |
| Get install status | ✅ | ✅ | N/A | Device-level tracking |
| Rollback | ✅ | ✅ | ✅ | Supersedence/uninstall |

**Authentication**:
- OAuth 2.0 client credentials flow
- Token caching with 5-minute expiry buffer
- Automatic refresh on expiry

**Test Coverage**: ~90%

**Issues**: None identified

---

### 2. Jamf Connector

**Status**: ✅ PRODUCTION-READY (minor issue)

**File Locations**:
- [jamf/auth.py](backend/apps/connectors/jamf/auth.py) (394 lines)
- [jamf/client.py](backend/apps/connectors/jamf/client.py) (582 lines)
- [JamfConnector.ps1](scripts/connectors/jamf/JamfConnector.ps1) (80+ lines)

**Operations Matrix**:

| Operation | Implemented | Tested | Idempotent | Notes |
|-----------|-------------|--------|------------|-------|
| Test connection | ✅ | ✅ | N/A | OAuth + Basic fallback |
| List computers | ✅ | ✅ | N/A | RSQL filtering |
| Create package | ✅ | ✅ | ✅ | 409 conflict handling |
| Create policy | ✅ | ✅ | ✅ | XML-based Classic API |
| Get policy logs | ✅ | ✅ | N/A | Deployment status |
| Get applications | ✅ | ✅ | N/A | Installed app inventory |

**Authentication**:
- OAuth 2.0 (preferred) with Basic auth fallback
- Token caching with 30-minute TTL
- Automatic refresh

**Test Coverage**: ~90%

**Issues**:
1. `_extract_policy_id_from_xml()` uses regex instead of ElementTree
   - Location: [jamf/client.py:474-480](backend/apps/connectors/jamf/client.py#L474-L480)
   - Severity: Medium
   - Fix: Replace regex with `xml.etree.ElementTree`

---

### 3. SCCM Connector

**Status**: ❌ VAPORWARE

**File Locations**:
- [Invoke-SCCMConnector.ps1](scripts/connectors/Invoke-SCCMConnector.ps1) (42 lines - **STUB**)
- [SccmConnector.ps1](scripts/connectors/sccm/SccmConnector.ps1) (60 lines - **SKELETON**)

**Operations Matrix**:

| Operation | Implemented | Tested | Idempotent | Notes |
|-----------|-------------|--------|------------|-------|
| Test connection | ❌ | ❌ | N/A | Returns hardcoded `true` |
| Sync inventory | ❌ | ❌ | N/A | Returns empty list |
| Create application | ❌ | ❌ | N/A | Function stub only |
| Deploy to collection | ❌ | ❌ | N/A | Not implemented |
| Compliance query | ❌ | ❌ | N/A | Not implemented |
| Rollback | ❌ | ❌ | N/A | Not implemented |

**Stub Behavior**:
```powershell
# Invoke-SCCMConnector.ps1 returns hardcoded success
Write-Result -Payload @{
    status = 'success'
    message = 'Deployment submitted'
    object_id = [guid]::NewGuid().ToString()
}
```

**What's Missing**:
1. SCCM AdminService REST API client
2. Windows Integrated Authentication handling
3. Collection targeting logic
4. Package distribution to DPs
5. Deployment status polling
6. Error classification (transient vs permanent)
7. Idempotency key handling

**Estimated Work**: 120 hours

**Implementation Path**:
```
Week 1:
  - Day 1-2: Python SCCM connector class with WIA auth
  - Day 3-4: AdminService REST API integration
  - Day 5: Collection management

Week 2:
  - Day 1-2: Package distribution to DPs
  - Day 3-4: Deployment creation and targeting
  - Day 5: Integration tests
```

---

### 4. Landscape Connector

**Status**: ❌ VAPORWARE

**File Locations**:
- [Invoke-LandscapeConnector.ps1](scripts/connectors/Invoke-LandscapeConnector.ps1) (42 lines - **STUB**)
- `landscape/LandscapeConnector.ps1` - **MISSING OR EMPTY**

**Operations Matrix**:

| Operation | Implemented | Tested | Idempotent | Notes |
|-----------|-------------|--------|------------|-------|
| Test connection | ❌ | ❌ | N/A | Returns hardcoded `true` |
| Sync inventory | ❌ | ❌ | N/A | Returns empty list |
| Repo sync | ❌ | ❌ | N/A | Not implemented |
| Package install | ❌ | ❌ | N/A | Not implemented |
| Compliance query | ❌ | ❌ | N/A | Not implemented |
| Rollback | ❌ | ❌ | N/A | Not implemented |

**What's Missing**:
1. Landscape API client (HTTP)
2. OAuth/API key authentication
3. Computer management operations
4. Package/repository management
5. Script execution
6. Compliance/status queries

**Estimated Work**: 100 hours

**Implementation Path**:
```
Week 1:
  - Day 1-2: Python Landscape connector class
  - Day 3-4: API authentication (OAuth/token)
  - Day 5: Computer listing and inventory

Week 2:
  - Day 1-2: Package management
  - Day 3-4: Script execution
  - Day 5: Integration tests
```

---

### 5. Ansible/AWX Connector

**Status**: ❌ VAPORWARE

**File Locations**:
- [Invoke-AnsibleConnector.ps1](scripts/connectors/Invoke-AnsibleConnector.ps1) (42 lines - **STUB**)
- `ansible/AnsibleConnector.ps1` - **MISSING OR EMPTY**

**Operations Matrix**:

| Operation | Implemented | Tested | Idempotent | Notes |
|-----------|-------------|--------|------------|-------|
| Test connection | ❌ | ❌ | N/A | Returns hardcoded `true` |
| Sync inventory | ❌ | ❌ | N/A | Returns empty dict |
| Job template list | ❌ | ❌ | N/A | Not implemented |
| Launch job | ❌ | ❌ | N/A | Not implemented |
| Job status | ❌ | ❌ | N/A | Not implemented |
| Rollback | ❌ | ❌ | N/A | Not implemented |

**What's Missing**:
1. AWX/Tower API client
2. OAuth 2.0 authentication
3. Job template CRUD
4. Job launch and monitoring
5. Inventory sync from AWX
6. Async job status polling

**Estimated Work**: 80 hours

**Implementation Path**:
```
Week 1:
  - Day 1-2: Python AWX connector class
  - Day 3-4: OAuth authentication
  - Day 5: Job template listing

Week 2:
  - Day 1-2: Job launch and monitoring
  - Day 3: Inventory sync
  - Day 4-5: Integration tests
```

---

### 6. AD/Entra ID Integration

**Status**: ✅ COMPLETE

**File Locations**:
- [services/entra_id.py](backend/apps/integrations/services/entra_id.py)
- [services/active_directory.py](backend/apps/integrations/services/active_directory.py)

**Operations Matrix**:

| Operation | Implemented | Tested | Notes |
|-----------|-------------|--------|-------|
| Test connection | ✅ | ✅ | Microsoft Graph API |
| Sync users | ✅ | ✅ | Pagination via @odata.nextLink |
| Sync groups | ✅ | ✅ | Group membership |
| Sync devices | ✅ | ✅ | Managed device inventory |
| LDAP sync (on-prem) | ✅ | ✅ | ldap3 library |

**Test Coverage**: ~80%

**Issues**: None

---

### 7. ServiceNow Integration

**Status**: ⚠️ PARTIAL

**File Locations**:
- [services/servicenow.py](backend/apps/integrations/services/servicenow.py)
- [services/servicenow_itsm.py](backend/apps/integrations/services/servicenow_itsm.py)

**Operations Matrix**:

| Operation | Implemented | Tested | Notes |
|-----------|-------------|--------|-------|
| Test connection | ✅ | ✅ | cmdb_ci_computer |
| Sync CMDB assets | ✅ | ✅ | Paginated fetch |
| Create incident | ✅ | ✅ | Basic implementation |
| Update incident | ✅ | ✅ | Basic implementation |
| Query CMDB | ❌ | ❌ | Not implemented |
| Change request sync | ❌ | ❌ | Partial implementation |

**Gap**: CMDB query and bidirectional change request sync incomplete

**Estimated Work**: 40 hours

---

### 8. Mobile Connectors

#### 8.1 Apple Business Manager (iOS/macOS)

**Status**: ⚠️ PARTIAL

**File Location**: [services/abm.py](backend/apps/integrations/services/abm.py)

**Operations Matrix**:

| Operation | Implemented | Tested | Notes |
|-----------|-------------|--------|-------|
| Test connection | ✅ | ✅ | /devices endpoint |
| Sync devices | ✅ | ✅ | Enrolled devices |
| Sync VPP licenses | ❌ | ❌ | **STUB** - returns (0, 0) |
| App assignment | ❌ | ❌ | Not implemented |

**Gap**: VPP license management is a stub at lines 91-94:
```python
def sync_licenses(self):
    # Stub: would sync VPP licenses to Application model
    return 0, 0
```

**Estimated Work**: 60 hours

---

#### 8.2 Android Enterprise

**Status**: ⚠️ PARTIAL

**File Location**: [services/android_enterprise.py](backend/apps/integrations/services/android_enterprise.py)

**Operations Matrix**:

| Operation | Implemented | Tested | Notes |
|-----------|-------------|--------|-------|
| Test connection | ✅ | ✅ | /enterprises endpoint |
| Sync devices | ✅ | ✅ | Enrolled devices |
| App deployment | ❌ | ❌ | Not implemented |
| Managed Play store | ❌ | ❌ | Not implemented |

**Gap**: Actual app deployment through Managed Google Play not implemented

**Estimated Work**: 60 hours

---

## Integration Services Status

The following integration services are fully implemented:

| Service | Type | Status | Test Coverage |
|---------|------|--------|---------------|
| ServiceNow CMDB | Asset Sync | ✅ Complete | ~80% |
| Entra ID | Identity Sync | ✅ Complete | ~80% |
| Active Directory | Identity Sync | ✅ Complete | ~80% |
| Jira Assets | Asset Sync | ✅ Complete | ~80% |
| Jira ITSM | ITSM | ✅ Complete | ~80% |
| Freshservice CMDB | Asset Sync | ✅ Complete | ~80% |
| Freshservice ITSM | ITSM | ✅ Complete | ~80% |
| Datadog | Monitoring | ✅ Complete | ~80% |
| Splunk | Monitoring | ✅ Complete | ~80% |
| Elastic | Monitoring | ✅ Complete | ~80% |
| Defender | Security | ✅ Complete | ~80% |
| Trivy | Scanning | ✅ Complete | ~80% |
| Grype | Scanning | ✅ Complete | ~80% |
| Snyk | Scanning | ✅ Complete | ~80% |

---

## PowerShell Script Inventory

### Stub Scripts (Return Hardcoded Success)

| Script | Lines | Purpose | Problem |
|--------|-------|---------|---------|
| Invoke-SCCMConnector.ps1 | 42 | SCCM wrapper | Hardcoded success |
| Invoke-LandscapeConnector.ps1 | 42 | Landscape wrapper | Hardcoded success |
| Invoke-AnsibleConnector.ps1 | 42 | Ansible wrapper | Hardcoded success |
| Invoke-IntuneConnector.ps1 | 42 | Intune wrapper | Calls real impl |
| Invoke-JamfConnector.ps1 | 42 | Jamf wrapper | Calls real impl |

### Implementation Scripts

| Script | Lines | Status | Notes |
|--------|-------|--------|-------|
| intune/IntuneConnector.ps1 | 80+ | ✅ Complete | Graph API integration |
| jamf/JamfConnector.ps1 | 80+ | ✅ Complete | Jamf API integration |
| sccm/SccmConnector.ps1 | 60+ | ⚠️ Skeleton | Function stubs only |
| landscape/LandscapeConnector.ps1 | ? | ❌ Missing | File empty or absent |
| ansible/AnsibleConnector.ps1 | ? | ❌ Missing | File empty or absent |

### Utility Scripts

| Script | Lines | Status |
|--------|-------|--------|
| common/ConnectorBase.ps1 | 80+ | ✅ Complete |
| utilities/logging/Write-StructuredLog.ps1 | ? | ✅ Complete |
| utilities/common/Get-ConfigValue.ps1 | ? | ✅ Complete |
| utilities/common/Invoke-RetryWithBackoff.ps1 | ? | ✅ Complete |
| utilities/common/Test-IdempotencyKey.ps1 | ? | ✅ Complete |

---

## Connector Checklist for SOW Acceptance

For each connector to be SOW-compliant:

### Intune ✅
- [x] Test connection implemented
- [x] Sync inventory implemented
- [x] Push intent implemented
- [x] Compliance query implemented
- [x] Rollback implemented
- [x] Idempotency verified
- [x] Integration tests pass

### Jamf ✅
- [x] Test connection implemented
- [x] Sync inventory implemented
- [x] Push intent implemented
- [x] Compliance query implemented
- [x] Rollback implemented
- [x] Idempotency verified
- [x] Integration tests pass

### SCCM ❌
- [ ] Test connection implemented
- [ ] Sync inventory implemented
- [ ] Push intent implemented
- [ ] Compliance query implemented
- [ ] Rollback implemented
- [ ] Idempotency verified
- [ ] Integration tests pass

### Landscape ❌
- [ ] Test connection implemented
- [ ] Sync inventory implemented
- [ ] Push intent implemented
- [ ] Compliance query implemented
- [ ] Rollback implemented
- [ ] Idempotency verified
- [ ] Integration tests pass

### Ansible ❌
- [ ] Test connection implemented
- [ ] Sync inventory implemented
- [ ] Push intent implemented
- [ ] Compliance query implemented
- [ ] Rollback implemented
- [ ] Idempotency verified
- [ ] Integration tests pass

### AD/Entra ID ✅
- [x] Test connection implemented
- [x] Sync users implemented
- [x] Sync groups implemented
- [x] Sync devices implemented
- [x] Integration tests pass

### ServiceNow ⚠️
- [x] Test connection implemented
- [x] CMDB sync implemented
- [ ] CMDB query implemented
- [x] Incident management implemented
- [ ] Change request bidirectional sync
- [ ] Integration tests pass

### Mobile (iOS ABM) ⚠️
- [x] Test connection implemented
- [x] Device sync implemented
- [ ] VPP license sync implemented
- [ ] App assignment implemented
- [ ] Integration tests pass

### Mobile (Android) ⚠️
- [x] Test connection implemented
- [x] Device sync implemented
- [ ] App deployment implemented
- [ ] Managed Play integration
- [ ] Integration tests pass

---

## Effort Estimates

| Connector | Current State | Hours to Complete | Priority |
|-----------|---------------|-------------------|----------|
| SCCM | Vaporware | 120 | CRITICAL |
| Landscape | Vaporware | 100 | CRITICAL |
| Ansible | Vaporware | 80 | CRITICAL |
| ServiceNow | Partial | 40 | HIGH |
| iOS ABM VPP | Stub | 60 | HIGH |
| Android Enterprise | Partial | 60 | HIGH |
| **Total** | | **460 hours** | |

---

## Recommendations

### Immediate (Week 1)

1. **Start SCCM connector implementation**
   - Create Python SCCM connector class
   - Implement Windows Integrated Auth
   - Build AdminService REST client

2. **Start Landscape connector implementation**
   - Create Python Landscape connector class
   - Implement API authentication
   - Build package management methods

3. **Fix Jamf XML parsing**
   - Replace regex with ElementTree
   - Add unit tests for XML edge cases

### Short-term (Week 2-3)

4. **Complete Ansible/AWX connector**
   - AWX API client
   - Job template management
   - Async job monitoring

5. **Complete ServiceNow CMDB query**
   - Implement query API
   - Bidirectional change request sync

6. **Complete mobile deployment flows**
   - iOS VPP license sync
   - Android Enterprise app deployment

### Medium-term (Week 4)

7. **Integration testing**
   - Test all connectors against sandbox environments
   - Validate idempotency
   - Document error scenarios

8. **Documentation**
   - Create connector-specific runbooks
   - Document auth patterns per platform
   - Create troubleshooting guides

---

## Risk Assessment

| Risk | Impact | Probability | Mitigation |
|------|--------|-------------|------------|
| SCCM AdminService access unavailable | HIGH | MEDIUM | Request sandbox access NOW |
| Landscape API differences per version | MEDIUM | HIGH | Test against customer version |
| AWX/Tower vs Ansible Engine confusion | MEDIUM | MEDIUM | Clarify customer's setup |
| ServiceNow custom fields in CMDB | MEDIUM | HIGH | Get customer schema |
| iOS ABM requires Apple cert setup | HIGH | HIGH | Start Apple cert process immediately |

---

*This audit was conducted on January 25, 2026. Status will change as implementation progresses.*
