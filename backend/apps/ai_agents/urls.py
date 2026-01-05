# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
URL configuration for AI Agents app.
"""
from django.urls import path
from . import views

app_name = 'ai_agents'

urlpatterns = [
    # Provider management
    path('providers/', views.list_providers, name='list_providers'),
    path('providers/configure/', views.configure_provider, name='configure_provider'),
    path('providers/<uuid:provider_id>/delete/', views.delete_provider, name='delete_provider'),
    path('providers/type/<str:provider_type>/delete/', views.delete_provider_by_type, name='delete_provider_by_type'),
    
    # Amani assistant
    path('amani/ask/', views.ask_amani, name='ask_amani'),
    path('conversations/', views.list_conversations, name='list_conversations'),
    path('conversations/<str:conversation_id>/', views.get_conversation, name='get_conversation'),
    
    # Agent tasks and stats
    path('stats/', views.agent_stats, name='agent_stats'),
    path('tasks/', views.list_tasks, name='list_tasks'),
    path('tasks/<uuid:task_id>/', views.get_task, name='get_task'),
    path('tasks/<uuid:task_id>/approve/', views.approve_task, name='approve_task'),
    path('tasks/<uuid:task_id>/reject/', views.reject_task, name='reject_task'),
    path('tasks/<uuid:task_id>/request-revision/', views.request_task_revision, name='request_revision'),
    path('tasks/create/', views.create_task_from_message, name='create_task'),
    path('tasks/pending/', views.list_pending_approvals, name='list_pending_approvals'),
]

