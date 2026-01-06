# SCCM Connector Error Handling

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

Error classification and retry logic for SCCM connector.

---

## Error Classification

### Transient Errors

**Examples**:
- WMI timeouts
- PowerShell remoting failures
- Network connectivity issues
- Site server temporary unavailability

**Handling**: Exponential backoff retry (max 5 attempts)

### Permanent Errors

**Examples**:
- Invalid package configuration
- Collection not found
- Insufficient permissions
- Package already exists (non-idempotent)

**Handling**: No retry, log error, notify

### Policy Violations

**Examples**:
- Scope validation failures
- SoD violations

**Handling**: No retry, log, notify, block

---

## Retry Logic

- **Backoff**: Exponential (1s, 2s, 4s, 8s, 16s)
- **Max Retries**: 5
- **Idempotent Keys**: Package IDs used for idempotency

---

## References

- [SCCM Connector Spec](./connector-spec.md)
- [Rollback Procedures](./rollback-procedures.md)

