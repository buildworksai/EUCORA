# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
CAB Workflow URL configuration.
Includes both legacy endpoints and P5.3 REST API endpoints.
"""
from django.urls import path
from . import views, api_views

app_name = 'cab_workflow'

urlpatterns = [
    # ======================================================================
    # P5.3: CAB Approval Request REST API
    # ======================================================================
    
    # CAB Approval Submission
    path('submit/', api_views.submit_cab_approval, name='submit'),
    path('<uuid:cab_request_id>/', api_views.get_cab_request, name='get_request'),
    path('<uuid:cab_request_id>/approve/', api_views.approve_cab_request, name='approve_request'),
    path('<uuid:cab_request_id>/reject/', api_views.reject_cab_request, name='reject_request'),
    
    # CAB Approval Queries
    path('pending/', api_views.list_pending_cab_requests, name='pending'),
    path('my-requests/', api_views.list_my_cab_requests, name='my_requests'),
    
    # CAB Exception Management
    path('exceptions/', api_views.create_cab_exception, name='create_exception'),
    path('exceptions/<uuid:exception_id>/', api_views.get_cab_exception, name='get_exception'),
    path('exceptions/<uuid:exception_id>/approve/', api_views.approve_exception, name='approve_exception'),
    path('exceptions/<uuid:exception_id>/reject/', api_views.reject_exception, name='reject_exception'),
    path('exceptions/pending/', api_views.list_pending_exceptions, name='pending_exceptions'),
    path('exceptions/my-exceptions/', api_views.list_my_exceptions, name='my_exceptions'),
    path('exceptions/cleanup/', api_views.cleanup_expired_exceptions, name='cleanup_exceptions'),
    
    # ======================================================================
    # Legacy Endpoints (preserved for backward compatibility)
    # ======================================================================
    
    # Dynamic UUID-based paths must come BEFORE static paths
    path('legacy/<uuid:correlation_id>/approve/', views.approve_deployment, name='legacy_approve'),
    path('legacy/<uuid:correlation_id>/reject/', views.reject_deployment, name='legacy_reject'),
    # Static paths last
    path('legacy/pending/', views.list_pending_approvals, name='legacy_pending'),
    path('legacy/approvals/', views.list_approvals, name='legacy_list'),
]
