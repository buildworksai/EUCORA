# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for Request Coordination API.
"""
from rest_framework.routers import DefaultRouter

from .views import (
    CommunicationTemplateViewSet,
    EscalationEventViewSet,
    EscalationRuleViewSet,
    RequestCommunicationViewSet,
    RequestCoordinationReportsViewSet,
    RequestStakeholderViewSet,
    TrackedRequestViewSet,
)

router = DefaultRouter()
router.register(r"requests", TrackedRequestViewSet, basename="tracked-request")
router.register(r"stakeholders", RequestStakeholderViewSet, basename="request-stakeholder")
router.register(r"communications", RequestCommunicationViewSet, basename="request-communication")
router.register(r"escalation-rules", EscalationRuleViewSet, basename="escalation-rule")
router.register(r"escalations", EscalationEventViewSet, basename="escalation-event")
router.register(r"templates", CommunicationTemplateViewSet, basename="communication-template")
router.register(r"reports", RequestCoordinationReportsViewSet, basename="request-coordination-reports")

urlpatterns = router.urls
