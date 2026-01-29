# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Ansible/AWX connector for Linux automation and remediation.

This module provides integration with AWX/Ansible Tower for:
- Job template management and execution
- Inventory synchronization
- Playbook-based package deployment
- Remediation workflows
- Compliance enforcement
"""
from .auth import AnsibleAuth, AnsibleAuthError
from .client import AnsibleConnector, AnsibleConnectorError

__all__ = [
    "AnsibleAuth",
    "AnsibleAuthError",
    "AnsibleConnector",
    "AnsibleConnectorError",
]
