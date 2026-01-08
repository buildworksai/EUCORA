# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Integration services factory and registry.
"""
from .base import IntegrationService
from .factory import get_integration_service, SERVICE_REGISTRY

__all__ = [
    'IntegrationService',
    'get_integration_service',
    'SERVICE_REGISTRY',
]

