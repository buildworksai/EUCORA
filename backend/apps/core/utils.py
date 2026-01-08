# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Core utility functions.
"""
import uuid
from typing import Optional


def generate_correlation_id(prefix: Optional[str] = None) -> str:
    """
    Generate a correlation ID with optional prefix.
    
    Args:
        prefix: Optional prefix for the correlation ID (e.g., 'deploy', 'cab', 'audit')
    
    Returns:
        Correlation ID string (e.g., 'deploy-a1b2c3d4-...' or UUID if no prefix)
    
    Example:
        >>> generate_correlation_id('deploy')
        'deploy-a1b2c3d4-e5f6-7890-abcd-ef1234567890'
    """
    correlation_id = str(uuid.uuid4())
    if prefix:
        return f'{prefix}-{correlation_id}'
    return correlation_id


def get_demo_mode_enabled() -> bool:
    """
    Read the global demo mode flag.
    """
    from apps.core.models import DemoModeConfig

    config = DemoModeConfig.objects.order_by('id').first()
    return bool(config and config.is_enabled)


def set_demo_mode_enabled(is_enabled: bool) -> bool:
    """
    Set the global demo mode flag.
    """
    from apps.core.models import DemoModeConfig

    config = DemoModeConfig.objects.order_by('id').first()
    if not config:
        config = DemoModeConfig.objects.create(is_enabled=is_enabled)
        return config.is_enabled

    if config.is_enabled != is_enabled:
        config.is_enabled = is_enabled
        config.save(update_fields=['is_enabled', 'updated_at'])
    return config.is_enabled


def apply_demo_filter(queryset, request):
    """
    Apply demo filter to a queryset based on global demo mode and query params.
    """
    include_demo = request.query_params.get('include_demo')

    if include_demo == 'all':
        return queryset
    if include_demo == 'true':
        return queryset.filter(is_demo=True)
    if include_demo == 'false':
        return queryset.filter(is_demo=False)

    if get_demo_mode_enabled():
        return queryset.filter(is_demo=True)
    return queryset.filter(is_demo=False)
