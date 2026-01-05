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
