# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Development settings for EUCORA Control Plane.

Extends base settings with development-specific overrides.
"""
from .base import *

DEBUG = True

# Development-specific apps
INSTALLED_APPS += [
    # 'django_extensions',  # Optional - install separately if needed
]

# Allow all hosts in development
ALLOWED_HOSTS = ["*"]

# Disable HTTPS-only cookies in development
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False

# CORS - Allow all origins in development
CORS_ALLOW_ALL_ORIGINS = True

# Email backend (console for development)
EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
# DRF default permissions: Allow anonymous reads in development
REST_FRAMEWORK.update(
    {
        "DEFAULT_PERMISSION_CLASSES": [
            "rest_framework.permissions.AllowAny",
        ],
        "DEFAULT_AUTHENTICATION_CLASSES": [
            "apps.authentication.dev_auth.DevAutoLoginAuthentication",
            "rest_framework.authentication.SessionAuthentication",
        ],
    }
)


# Use SQLite for local development (no PostgreSQL required)
if config("USE_SQLITE", default=False, cast=bool):
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }

# Django Debug Toolbar (optional)
if config("ENABLE_DEBUG_TOOLBAR", default=False, cast=bool):
    INSTALLED_APPS += ["debug_toolbar"]
    MIDDLEWARE.insert(0, "debug_toolbar.middleware.DebugToolbarMiddleware")
    INTERNAL_IPS = ["127.0.0.1"]
