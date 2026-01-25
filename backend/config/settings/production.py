# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Production settings for EUCORA Control Plane.

Extends base settings with production-specific security and performance optimizations.
"""
from .base import *

DEBUG = False

# Security settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = "DENY"

# Session security
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email backend (SMTP for production)
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = config("EMAIL_HOST", default="smtp.gmail.com")
EMAIL_PORT = config("EMAIL_PORT", default=587, cast=int)
EMAIL_USE_TLS = True
EMAIL_HOST_USER = config("EMAIL_HOST_USER", default="")
EMAIL_HOST_PASSWORD = config("EMAIL_HOST_PASSWORD", default="")

# Logging - Send to Azure Sentinel
LOGGING["handlers"]["azure_sentinel"] = {
    "class": "apps.telemetry.handlers.AzureSentinelHandler",
    "level": "WARNING",
}
LOGGING["root"]["handlers"].append("azure_sentinel")
