# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
EUCORA Control Plane URL Configuration.

API versioning via URL path: /api/v1/
"""
from django.contrib import admin
from django.urls import path, include
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView
from apps.core.health import liveness_check, readiness_check

urlpatterns = [
    # Health checks (Kubernetes probes)
    path('health/live', liveness_check, name='liveness'),
    path('health/ready', readiness_check, name='readiness'),
    
    # Admin
    path('admin/', admin.site.urls),
    
    # API v1
    path('api/v1/auth/', include('apps.authentication.urls')),
    path('api/v1/policy/', include('apps.policy_engine.urls')),
    path('api/v1/deployments/', include('apps.deployment_intents.urls')),
    path('api/v1/cab/', include('apps.cab_workflow.urls')),
    path('api/v1/evidence/', include('apps.evidence_store.urls')),
    path('api/v1/events/', include('apps.event_store.urls')),
    path('api/v1/connectors/', include('apps.connectors.urls')),
    path('api/v1/', include('apps.connectors.urls')),  # Assets endpoints at /api/v1/assets/
    path('api/v1/health/', include('apps.telemetry.urls')),
    path('api/v1/ai/', include('apps.ai_agents.urls')),
    
    # OpenAPI / Swagger
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),
]
