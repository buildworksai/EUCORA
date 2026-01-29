# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Authentication URL configuration.
"""
from django.urls import path

from . import views

app_name = "authentication"

urlpatterns = [
    path("login", views.entra_id_login, name="login"),
    path("logout", views.auth_logout, name="logout"),
    path("me", views.current_user, name="current-user"),
    path("validate", views.validate_session, name="validate-session"),
]
