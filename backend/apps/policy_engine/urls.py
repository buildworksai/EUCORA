# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine URL configuration.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from . import views

app_name = "policy_engine"

# Router for ViewSets
router = DefaultRouter()
router.register(r"policies", views.ApplicationPolicyViewSet, basename="policy")
router.register(r"templates", views.PolicyTemplateViewSet, basename="template")

urlpatterns = [
    # Legacy function-based views (kept for backward compatibility)
    path("", views.list_policies, name="list"),
    path("assess", views.assess_risk, name="assess-risk"),
    path("evaluate/", views.evaluate_policy, name="evaluate"),
    path("risk-model", views.get_active_risk_model, name="risk-model"),
    # ViewSet-based routes
    path("", include(router.urls)),
]
