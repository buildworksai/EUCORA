# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Microsoft SCCM (Configuration Manager) connector for Windows application deployment.

Provides Windows Integrated Authentication (WIA) and SCCM AdminService REST API integration.
Used for offline site distribution and constrained environments where Intune is not suitable.
"""
from .auth import SCCMAuth, SCCMAuthError
from .client import SCCMConnector, SCCMConnectorError

__all__ = [
    "SCCMAuth",
    "SCCMAuthError",
    "SCCMConnector",
    "SCCMConnectorError",
]
