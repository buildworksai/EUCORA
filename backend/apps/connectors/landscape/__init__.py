# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Landscape connector for Ubuntu/Linux endpoint management.

This module provides integration with Canonical Landscape for:
- Package management and deployment
- Computer inventory and compliance
- Repository synchronization
- Script execution and remediation
"""
from .auth import LandscapeAuth, LandscapeAuthError
from .client import LandscapeConnector, LandscapeConnectorError

__all__ = [
    "LandscapeAuth",
    "LandscapeAuthError",
    "LandscapeConnector",
    "LandscapeConnectorError",
]
