# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
EUCORA Control Plane URL Configuration.

API versioning via URL path: /api/v1/
"""
from django.contrib import admin
from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from apps.core.health import comprehensive_health_check, demo_readiness_check, liveness_check, readiness_check
from apps.core.views_metrics import metrics_endpoint

urlpatterns = [
    # Health checks (Kubernetes probes)
    path("health/live", liveness_check, name="liveness"),
    path("health/ready", readiness_check, name="readiness"),
    path("health/demo-ready", demo_readiness_check, name="demo-readiness"),
    path("api/v1/health/", comprehensive_health_check, name="comprehensive-health"),
    # Metrics endpoint (Prometheus scraping)
    path("api/v1/metrics/", metrics_endpoint, name="metrics"),
    # Admin
    path("admin/", admin.site.urls),
    # API v1
    path("api/v1/auth/", include("apps.authentication.urls")),
    path("api/v1/policy/", include("apps.policy_engine.urls")),
    path("api/v1/deployments/", include("apps.deployment_intents.urls")),
    path("api/v1/cab/", include("apps.cab_workflow.urls")),
    path("api/v1/evidence/", include("apps.evidence_store.urls")),
    path("api/v1/events/", include("apps.event_store.urls")),
    # Connectors endpoints - assets at /api/v1/assets/, connector ops at /api/v1/connectors/
    path("api/v1/", include("apps.connectors.urls")),  # Assets endpoints at /api/v1/assets/
    path("api/v1/health/", include("apps.telemetry.urls")),
    path("api/v1/telemetry/", include("apps.telemetry.urls")),  # Add telemetry namespace
    path("api/v1/ai/", include("apps.ai_agents.urls")),
    path("api/v1/", include("apps.integrations.urls")),
    path("api/v1/admin/", include("apps.core.urls")),  # Admin demo data endpoints
    path("api/v1/core/", include("apps.core.urls")),  # Core wrapper endpoints for API coverage
    path("api/v1/agent-management/", include("apps.agent_management.urls")),
    path("api/v1/packaging/", include("apps.packaging_factory.urls")),
    path("api/v1/licenses/", include("apps.license_management.urls")),
    path("api/v1/portfolio/", include("apps.application_portfolio.urls")),
    # OpenAPI / Swagger
    path("api/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
]
