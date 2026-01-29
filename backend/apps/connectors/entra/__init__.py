# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Entra ID (Azure AD) connector for EUCORA Control Plane.

Provides user/group synchronization and authentication integration
with Microsoft Entra ID (formerly Azure Active Directory).
"""
from .auth import EntraAuth
from .client import EntraConnector

__all__ = ["EntraAuth", "EntraConnector"]
