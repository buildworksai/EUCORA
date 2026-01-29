# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Microsoft Intune connector for Windows application deployment.

Provides OAuth 2.0 authentication and Microsoft Graph API integration.
"""
from .auth import IntuneAuth, IntuneAuthError
from .client import IntuneConnector, IntuneConnectorError

__all__ = [
    "IntuneAuth",
    "IntuneAuthError",
    "IntuneConnector",
    "IntuneConnectorError",
]
