# SCCM Rollback Procedures

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

Rollback strategies for SCCM deployments.

---

## Rollback Strategies

### 1. Rollback Packages

**Method**: Deploy rollback package to collections

**Process**:
1. Create rollback package (previous version)
2. Distribute to DPs
3. Create deployment to collections
4. Monitor rollback success

### 2. Collection Targeting

**Method**: Update collection membership

**Process**:
1. Remove devices from new version collection
2. Add devices to previous version collection
3. Redeploy previous version
4. Monitor rollback success

### 3. DP Management

**Method**: Remove package from DPs

**Process**:
1. Remove package from DPs
2. Remove deployment
3. Deploy previous version
4. Monitor rollback success

---

## Rollback Validation

- Rollback package available
- Collection membership validated
- DP distribution verified

---

## References

- [SCCM Connector Spec](./connector-spec.md)
- [Error Handling](./error-handling.md)

