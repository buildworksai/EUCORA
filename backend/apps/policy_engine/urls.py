# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine URL configuration.
"""
from django.urls import path
from . import views

app_name = 'policy_engine'

urlpatterns = [
    path('assess', views.assess_risk, name='assess-risk'),
    path('risk-model', views.get_active_risk_model, name='risk-model'),
]
