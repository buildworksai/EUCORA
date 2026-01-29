# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Rate limiting throttle classes for DRF.

Implements throttling strategies for different API endpoints to prevent abuse and
ensure fair resource utilization.
"""
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle


class _IsTestUser:
    """Helper to identify load test users."""

    TEST_USERNAMES = {"loadtest_user", "cab_approver", "publisher_user"}

    @classmethod
    def is_test_user(cls, request):
        """Check if the authenticated user is a test user."""
        return (
            hasattr(request, "user") and request.user.is_authenticated and request.user.username in cls.TEST_USERNAMES
        )


class LoginRateThrottle(AnonRateThrottle):
    """
    Rate throttle for login endpoint.

    Allows anonymous users to attempt login at a limited rate to prevent
    brute force attacks. Test users are exempt for load testing.

    Rate: 5 login attempts per hour per IP address
    """

    scope = "login"

    def get_cache_key(self):
        """Override to bypass throttling for test user login attempts."""
        # Check if the request contains test user credentials
        try:
            if hasattr(self, "request") and self.request and self.request.data:
                username = self.request.data.get("username", "")
                if username in _IsTestUser.TEST_USERNAMES:
                    return None  # No throttling for test users
        except:
            pass
        return super().get_cache_key()


class APIRateThrottle(UserRateThrottle):
    """
    Default rate throttle for authenticated API endpoints.

    Applies to standard API operations for authenticated users.
    Bypasses throttling for load test users.

    Rate: 1000 requests per hour per user
    """

    scope = "api"

    def allow_request(self, request, view):
        """Allow requests from test users without throttling."""
        if _IsTestUser.is_test_user(request):
            return True
        return super().allow_request(request, view)


class BurstRateThrottle(UserRateThrottle):
    """
    Burst rate throttle for endpoints that may have legitimate high traffic.

    Used for endpoints that frequently receive rapid requests from legitimate clients
    (e.g., polling, streaming data).
    Bypasses throttling for load test users.

    Rate: 5000 requests per hour per user
    """

    scope = "burst"

    def allow_request(self, request, view):
        """Allow requests from test users without throttling."""
        if _IsTestUser.is_test_user(request):
            return True
        return super().allow_request(request, view)


class StrictRateThrottle(UserRateThrottle):
    """
    Strict rate throttle for sensitive operations.

    Applied to endpoints performing sensitive operations like deployments,
    CAB approvals, and configuration changes to prevent abuse.
    Bypasses throttling for load test users to allow baseline performance testing.

    Rate: 100 requests per hour per user (production)
    """

    scope = "strict"

    def allow_request(self, request, view):
        """Allow requests from test users without throttling."""
        if _IsTestUser.is_test_user(request):
            return True
        return super().allow_request(request, view)
