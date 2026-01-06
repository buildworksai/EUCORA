# Jamf Pro Rollback Procedures

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

Rollback strategies for Jamf Pro deployments.

---

## Rollback Strategies

### 1. Policy-Based Version Pinning

**Method**: Update policy to pin previous version

**Process**:
1. Identify previous version
2. Update policy to target previous version
3. Redeploy policy
4. Monitor rollback success

### 2. Uninstall Scripts

**Method**: Deploy uninstall script via policy

**Process**:
1. Create uninstall script
2. Package as policy
3. Deploy uninstall policy
4. Monitor uninstall success

---

## Rollback Validation

- Previous version available
- Uninstall script tested
- Policy scope validated

---

## References

- [Jamf Connector Spec](./connector-spec.md)
- [Error Handling](./error-handling.md)

