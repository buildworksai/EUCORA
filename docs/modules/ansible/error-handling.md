# Ansible (AWX/Tower) Connector Error Handling

**Version**: 1.0  
**Status**: Active  
**Last Updated**: 2026-01-06

---

## Overview

Error classification and retry logic for Ansible connector.

---

## Error Classification

### Transient Errors

**Examples**:
- SSH connection failures
- Playbook execution timeouts
- Network connectivity issues
- AWX/Tower API temporary unavailability

**Handling**: Exponential backoff retry (max 5 attempts)

### Permanent Errors

**Examples**:
- Invalid playbook syntax
- Host unreachable
- Insufficient permissions
- Package not found

**Handling**: No retry, log error, notify

---

## Retry Logic

- **Backoff**: Exponential (1s, 2s, 4s, 8s, 16s)
- **Max Retries**: 5
- **Idempotent**: Playbooks should be idempotent

---

## References

- [Ansible Connector Spec](./connector-spec.md)
- [Rollback Procedures](./rollback-procedures.md)

