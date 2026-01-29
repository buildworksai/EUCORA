# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Development-only authentication helpers.

Why this exists:
- The frontend can run in "mock auth" mode (see `VITE_USE_MOCK_AUTH=true`).
- In that mode, the browser will not have a backend session cookie, so any
  DRF endpoint protected by `IsAuthenticated` returns 401/403.

This authentication class provides a *dev-only* auto-login for browser requests
coming from trusted local frontend origins.

Security constraints:
- Only active when `settings.DEBUG` is True.
- Only triggers for requests carrying an `Origin` header that matches trusted
  frontend origins.
- Never enabled in production.
"""

from __future__ import annotations

from typing import Optional, Tuple

from django.conf import settings
from django.contrib.auth import get_user_model
from rest_framework.authentication import BaseAuthentication


class DevAutoLoginAuthentication(BaseAuthentication):
    """Auto-authenticate local browser requests in development.

    This is intentionally *not* controlled by cookies.
    It exists to keep dev/demo UX working while preserving `IsAuthenticated`
    permissions on viewsets.
    """

    def authenticate(self, request) -> Optional[Tuple[object, None]]:  # type: ignore[override]
        if not getattr(settings, "DEBUG", False):
            return None

        origin = request.META.get("HTTP_ORIGIN")
        if not origin:
            return None

        trusted_origins = set(getattr(settings, "CSRF_TRUSTED_ORIGINS", []) or [])
        trusted_origins.update(getattr(settings, "CORS_ALLOWED_ORIGINS", []) or [])
        trusted_origins.update(
            {
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "http://0.0.0.0:5173",
            }
        )

        if origin not in trusted_origins:
            return None

        user_model = get_user_model()
        user, _created = user_model.objects.get_or_create(
            username="admin",
            defaults={
                "email": "admin@eucora.com",
                "is_staff": True,
                "is_superuser": True,
                "is_active": True,
            },
        )

        # Ensure privileges remain correct across restarts.
        updates = {}
        if not user.is_active:
            updates["is_active"] = True
        if not user.is_staff:
            updates["is_staff"] = True
        if not user.is_superuser:
            updates["is_superuser"] = True
        if not getattr(user, "email", None):
            updates["email"] = "admin@eucora.com"
        if updates:
            for key, value in updates.items():
                setattr(user, key, value)
            user.save(update_fields=list(updates.keys()))

        return (user, None)
