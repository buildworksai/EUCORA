# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Rate limiting throttle classes for DRF.

Implements throttling strategies for different API endpoints to prevent abuse and
ensure fair resource utilization.
"""
from rest_framework.throttling import UserRateThrottle, AnonRateThrottle


class LoginRateThrottle(AnonRateThrottle):
    """
    Rate throttle for login endpoint.
    
    Allows anonymous users to attempt login at a limited rate to prevent
    brute force attacks.
    
    Rate: 5 login attempts per hour per IP address
    """
    scope = 'login'


class APIRateThrottle(UserRateThrottle):
    """
    Default rate throttle for authenticated API endpoints.
    
    Applies to standard API operations for authenticated users.
    
    Rate: 1000 requests per hour per user
    """
    scope = 'api'


class BurstRateThrottle(UserRateThrottle):
    """
    Burst rate throttle for endpoints that may have legitimate high traffic.
    
    Used for endpoints that frequently receive rapid requests from legitimate clients
    (e.g., polling, streaming data).
    
    Rate: 5000 requests per hour per user
    """
    scope = 'burst'


class StrictRateThrottle(UserRateThrottle):
    """
    Strict rate throttle for sensitive operations.
    
    Applied to endpoints performing sensitive operations like deployments,
    CAB approvals, and configuration changes to prevent abuse.
    
    Rate: 100 requests per hour per user
    """
    scope = 'strict'
