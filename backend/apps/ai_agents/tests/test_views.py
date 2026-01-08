# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for AI agents API views.
"""
import pytest
from rest_framework.test import APIClient
from django.contrib.auth.models import User
from django.utils import timezone
from apps.ai_agents.models import AIModelProvider, AIConversation, AIMessage, AIAgentTask, AIAgentType


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture(autouse=True)
def _clear_ai_data(db):
    AIModelProvider.objects.all().delete()
    AIAgentTask.objects.all().delete()
    AIMessage.objects.all().delete()
    AIConversation.objects.all().delete()
    yield


@pytest.fixture
def admin_user(db):
    return User.objects.create_user(
        username="admin",
        email="admin@example.com",
        password="adminpass",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def normal_user(db):
    return User.objects.create_user(
        username="user",
        email="user@example.com",
        password="userpass",
    )


@pytest.mark.django_db
def test_list_providers(api_client):
    AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        api_key_dev="key",
        is_active=True,
        is_default=True,
    )
    response = api_client.get("/api/v1/ai/providers/")
    assert response.status_code == 200
    assert response.data["providers"][0]["key_configured"] is True


@pytest.mark.django_db
def test_configure_provider_validation(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    response = api_client.post("/api/v1/ai/providers/configure/", {}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_configure_provider_success(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    response = api_client.post(
        "/api/v1/ai/providers/configure/",
        {
            "provider_type": "openai",
            "api_key": "key",
            "model_name": "gpt-4o",
            "display_name": "OpenAI",
            "is_default": True,
        },
        format="json",
    )
    assert response.status_code == 200
    assert response.data["provider"]["is_default"] is True


@pytest.mark.django_db
def test_delete_provider(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    provider = AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        api_key_dev="key",
        is_active=True,
    )
    response = api_client.delete(f"/api/v1/ai/providers/{provider.id}/delete/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_delete_provider_by_type_not_found(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    response = api_client.delete("/api/v1/ai/providers/type/anthropic/delete/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_delete_provider_not_found(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    response = api_client.delete("/api/v1/ai/providers/00000000-0000-0000-0000-000000000000/delete/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_ask_amani_missing_message(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    response = api_client.post("/api/v1/ai/amani/ask/", {}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_ask_amani_success(api_client, normal_user, monkeypatch):
    api_client.force_authenticate(normal_user)

    class FakeService:
        def ask_amani_sync(self, **kwargs):
            return {"conversation_id": "conv", "response": "ok", "requires_action": False}

    from apps.ai_agents import views
    monkeypatch.setattr(views, "get_ai_agent_service", lambda: FakeService())

    response = api_client.post("/api/v1/ai/amani/ask/", {"message": "hi"}, format="json")
    assert response.status_code == 200


@pytest.mark.django_db
def test_ask_amani_error_status(api_client, normal_user, monkeypatch):
    api_client.force_authenticate(normal_user)

    class FakeService:
        def ask_amani_sync(self, **kwargs):
            return {"error": "Invalid API key"}

    from apps.ai_agents import views
    monkeypatch.setattr(views, "get_ai_agent_service", lambda: FakeService())

    response = api_client.post("/api/v1/ai/amani/ask/", {"message": "hi"}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_ask_amani_service_error(api_client, normal_user, monkeypatch):
    api_client.force_authenticate(normal_user)

    class FakeService:
        def ask_amani_sync(self, **kwargs):
            return {"error": "Service unavailable"}

    from apps.ai_agents import views
    monkeypatch.setattr(views, "get_ai_agent_service", lambda: FakeService())

    response = api_client.post("/api/v1/ai/amani/ask/", {"message": "hi"}, format="json")
    assert response.status_code == 503


@pytest.mark.django_db
def test_agent_stats_authenticated(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    conversation = AIConversation.objects.create(
        user=normal_user,
        agent_type=AIAgentType.AMANI_ASSISTANT,
        title="Test",
    )
    AIMessage.objects.create(
        conversation=conversation,
        role="assistant",
        content="Test",
        token_count=1200,
        requires_human_action=False,
    )
    response = api_client.get("/api/v1/ai/stats/")
    assert response.status_code == 200
    assert response.data["tokens_used"] == 1


@pytest.mark.django_db
def test_agent_stats_anonymous(api_client):
    response = api_client.get("/api/v1/ai/stats/")
    assert response.status_code == 200
    assert response.data["active_tasks"] == 0


@pytest.mark.django_db
def test_list_and_get_conversations(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    conversation = AIConversation.objects.create(
        user=normal_user,
        agent_type=AIAgentType.AMANI_ASSISTANT,
        title="Test",
    )
    AIMessage.objects.create(
        conversation=conversation,
        role="user",
        content="hello",
        token_count=2,
    )
    response = api_client.get("/api/v1/ai/conversations/")
    assert response.status_code == 200
    assert response.data["conversations"][0]["id"] == str(conversation.id)

    response = api_client.get(f"/api/v1/ai/conversations/{conversation.id}/")
    assert response.status_code == 200
    assert response.data["messages"][0]["content"] == "hello"


@pytest.mark.django_db
def test_list_tasks_anonymous(api_client):
    response = api_client.get("/api/v1/ai/tasks/")
    assert response.status_code == 200
    assert response.data["tasks"] == []


@pytest.mark.django_db
def test_list_tasks_authenticated(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=normal_user,
        title="Task",
        description="Desc",
        task_type="ai_recommendation",
        status="pending",
    )
    response = api_client.get("/api/v1/ai/tasks/?status=pending")
    assert response.status_code == 200
    assert len(response.data["tasks"]) == 1


@pytest.mark.django_db
def test_pending_approvals_admin(api_client, admin_user, normal_user):
    api_client.force_authenticate(admin_user)
    AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=normal_user,
        title="Task",
        description="Desc",
        task_type="ai_recommendation",
        status="awaiting_approval",
    )
    response = api_client.get("/api/v1/ai/tasks/pending/")
    assert response.status_code == 200
    assert response.data["total_count"] == 1


@pytest.mark.django_db
def test_pending_approvals_user_only(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=normal_user,
        title="Task",
        description="Desc",
        task_type="ai_recommendation",
        status="awaiting_approval",
    )
    response = api_client.get("/api/v1/ai/tasks/pending/")
    assert response.status_code == 200
    assert response.data["pending_approvals"][0]["id"] == str(task.id)


@pytest.mark.django_db
def test_pending_approvals_anonymous(api_client):
    response = api_client.get("/api/v1/ai/tasks/pending/")
    assert response.status_code == 200
    assert response.data["pending_approvals"] == []
    assert response.data["total_count"] == 0


@pytest.mark.django_db
def test_get_task_permissions(api_client, normal_user, admin_user):
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=admin_user,
        title="Task",
        description="Desc",
        task_type="ai_recommendation",
        status="awaiting_approval",
    )
    api_client.force_authenticate(normal_user)
    response = api_client.get(f"/api/v1/ai/tasks/{task.id}/")
    assert response.status_code == 403


@pytest.mark.django_db
def test_get_task_success(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=normal_user,
        title="Task",
        description="Desc",
        task_type="ai_recommendation",
        status="awaiting_approval",
    )
    response = api_client.get(f"/api/v1/ai/tasks/{task.id}/")
    assert response.status_code == 200


@pytest.mark.django_db
def test_get_task_not_found(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    response = api_client.get("/api/v1/ai/tasks/00000000-0000-0000-0000-000000000000/")
    assert response.status_code == 404


@pytest.mark.django_db
def test_approve_task_flow(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=admin_user,
        title="Task",
        description="Desc",
        task_type="ai_recommendation",
        status="awaiting_approval",
        output_data={},
    )
    response = api_client.post(f"/api/v1/ai/tasks/{task.id}/approve/", {"comment": "ok"}, format="json")
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.status == "approved"


@pytest.mark.django_db
def test_approve_task_invalid_status(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=admin_user,
        title="Task",
        description="Desc",
        task_type="ai_recommendation",
        status="completed",
        output_data={},
    )
    response = api_client.post(f"/api/v1/ai/tasks/{task.id}/approve/", {}, format="json")
    assert response.status_code == 400


@pytest.mark.django_db
def test_reject_task_flow(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=admin_user,
        title="Task",
        description="Desc",
        task_type="ai_recommendation",
        status="awaiting_approval",
        output_data={},
    )
    response = api_client.post(f"/api/v1/ai/tasks/{task.id}/reject/", {"reason": "no"}, format="json")
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.status == "rejected"


@pytest.mark.django_db
def test_request_task_revision_requires_feedback(api_client, admin_user):
    api_client.force_authenticate(admin_user)
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=admin_user,
        title="Task",
        description="Desc",
        task_type="ai_recommendation",
        status="awaiting_approval",
        output_data={},
    )
    response = api_client.post(
        f"/api/v1/ai/tasks/{task.id}/request-revision/",
        {"feedback": ""},
        format="json",
    )
    assert response.status_code == 400


@pytest.mark.django_db
def test_request_task_revision_success(api_client, admin_user, monkeypatch):
    api_client.force_authenticate(admin_user)
    conversation = AIConversation.objects.create(
        user=admin_user,
        agent_type=AIAgentType.AMANI_ASSISTANT,
        title="Test",
    )
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=admin_user,
        conversation=conversation,
        title="Task",
        description="Original",
        task_type="ai_recommendation",
        status="awaiting_approval",
        output_data={},
    )

    class FakeService:
        def ask_amani_sync(self, **kwargs):
            return {"response": "Revised"}

    from apps.ai_agents import views
    monkeypatch.setattr(views, "get_ai_agent_service", lambda: FakeService())

    response = api_client.post(
        f"/api/v1/ai/tasks/{task.id}/request-revision/",
        {"feedback": "Improve"},
        format="json",
    )
    assert response.status_code == 200
    task.refresh_from_db()
    assert task.status == "awaiting_approval"


@pytest.mark.django_db
def test_request_task_revision_ai_error(api_client, admin_user, monkeypatch):
    api_client.force_authenticate(admin_user)
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=admin_user,
        title="Task",
        description="Original",
        task_type="ai_recommendation",
        status="awaiting_approval",
        output_data={},
    )

    class FakeService:
        def ask_amani_sync(self, **kwargs):
            return {"error": "provider down"}

    from apps.ai_agents import views
    monkeypatch.setattr(views, "get_ai_agent_service", lambda: FakeService())

    response = api_client.post(
        f"/api/v1/ai/tasks/{task.id}/request-revision/",
        {"feedback": "Improve"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["task"]["ai_status"] == "pending"


@pytest.mark.django_db
def test_request_task_revision_ai_exception(api_client, admin_user, monkeypatch):
    api_client.force_authenticate(admin_user)
    task = AIAgentTask.objects.create(
        agent_type=AIAgentType.AMANI_ASSISTANT,
        initiated_by=admin_user,
        title="Task",
        description="Original",
        task_type="ai_recommendation",
        status="awaiting_approval",
        output_data={},
    )

    class FakeService:
        def ask_amani_sync(self, **kwargs):
            raise Exception("boom")

    from apps.ai_agents import views
    monkeypatch.setattr(views, "get_ai_agent_service", lambda: FakeService())

    response = api_client.post(
        f"/api/v1/ai/tasks/{task.id}/request-revision/",
        {"feedback": "Improve"},
        format="json",
    )
    assert response.status_code == 200
    assert response.data["task"]["ai_status"] == "pending"


@pytest.mark.django_db
def test_create_task_from_message(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    response = api_client.post(
        "/api/v1/ai/tasks/create/",
        {
            "title": "New",
            "description": "Desc",
            "agent_type": "amani",
            "task_type": "ai_recommendation",
            "input_data": {"k": "v"},
            "output_data": {},
        },
        format="json",
    )
    assert response.status_code == 201


@pytest.mark.django_db
def test_create_task_from_message_missing_fields(api_client, normal_user):
    api_client.force_authenticate(normal_user)
    response = api_client.post("/api/v1/ai/tasks/create/", {"title": ""}, format="json")
    assert response.status_code == 400
