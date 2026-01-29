# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine URL configuration.
"""
from django.urls import path

from . import views

app_name = "policy_engine"

urlpatterns = [
    path("", views.list_policies, name="list"),
    path("assess", views.assess_risk, name="assess-risk"),
    path("evaluate/", views.evaluate_policy, name="evaluate"),
    path("risk-model", views.get_active_risk_model, name="risk-model"),
]
