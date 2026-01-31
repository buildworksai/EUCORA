# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CAB Workflow URL configuration.
Includes both legacy endpoints and P5.3 REST API endpoints.
"""
from django.urls import path

from . import api_views, views

app_name = "cab_workflow"

urlpatterns = [
    # ======================================================================
    # P5: CAB Approval API (uses CABApproval model with AllowAny for demo)
    # ======================================================================
    # Primary endpoints - use views.py with AllowAny permissions
    path("pending/", views.list_pending_approvals, name="pending"),
    path("approvals/", views.list_approvals, name="list"),
    path("<uuid:correlation_id>/approve/", views.approve_deployment, name="approve"),
    path("<uuid:correlation_id>/reject/", views.reject_deployment, name="reject"),
    # ======================================================================
    # P5.3: CAB Approval Request REST API (legacy, requires auth)
    # ======================================================================
    # CAB Approval List (API coverage requirement)
    path("requests/", api_views.list_all_cab_requests, name="list_all_requests"),
    # CAB Approval Submission
    path("requests/submit/", api_views.submit_cab_approval, name="submit"),
    path("requests/<uuid:cab_request_id>/", api_views.get_cab_request, name="get_request"),
    path("requests/<uuid:cab_request_id>/approve/", api_views.approve_cab_request, name="approve_request"),
    path("requests/<uuid:cab_request_id>/reject/", api_views.reject_cab_request, name="reject_request"),
    # CAB Approval Queries
    path("requests/pending/", api_views.list_pending_cab_requests, name="pending_requests"),
    path("requests/my-requests/", api_views.list_my_cab_requests, name="my_requests"),
    # CAB Exception Management
    path("requests/exceptions/", api_views.create_cab_exception, name="create_exception"),
    path("requests/exceptions/<uuid:exception_id>/", api_views.get_cab_exception, name="get_exception"),
    path("requests/exceptions/<uuid:exception_id>/approve/", api_views.approve_exception, name="approve_exception"),
    path("requests/exceptions/<uuid:exception_id>/reject/", api_views.reject_exception, name="reject_exception"),
    path("requests/exceptions/pending/", api_views.list_pending_exceptions, name="pending_exceptions"),
    path("requests/exceptions/my-exceptions/", api_views.list_my_exceptions, name="my_exceptions"),
    path("requests/exceptions/cleanup/", api_views.cleanup_expired_exceptions, name="cleanup_exceptions"),
]
