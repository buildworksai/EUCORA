# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for Change Communications API.
"""
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import (
    ChangeDashboardViewSet,
    ChangeRecordViewSet,
    CommunicationTemplateViewSet,
    CommunicationViewSet,
    KBArticleLinkViewSet,
    StakeholderGroupViewSet,
)

app_name = "change_communications"

router = DefaultRouter()
router.register(r"changes", ChangeRecordViewSet, basename="change")
router.register(r"stakeholders", StakeholderGroupViewSet, basename="stakeholder")
router.register(r"templates", CommunicationTemplateViewSet, basename="template")
router.register(r"communications", CommunicationViewSet, basename="communication")
router.register(r"kb-articles", KBArticleLinkViewSet, basename="kb-article")
router.register(r"dashboard", ChangeDashboardViewSet, basename="dashboard")

urlpatterns = [
    path("", include(router.urls)),
]
