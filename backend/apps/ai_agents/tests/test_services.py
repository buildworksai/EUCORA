# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for AI agent services.
"""
import pytest
from types import SimpleNamespace
from apps.ai_agents.models import AIModelProvider, AIAgentType, AIConversation, AIMessage
from apps.ai_agents.services import AIAgentService
from apps.ai_agents import services


class FakeProvider:
    def __init__(self, response="Hello"):
        self._response = response

    async def chat(self, messages):
        return self._response

    def count_tokens(self, text: str) -> int:
        return max(1, len(text) // 4)


@pytest.fixture(autouse=True)
def _clear_ai_providers(db):
    AIModelProvider.objects.all().delete()
    AIConversation.objects.all().delete()
    AIMessage.objects.all().delete()
    yield


@pytest.mark.django_db
def test_get_provider_errors_no_config():
    service = AIAgentService()
    with pytest.raises(ValueError, match="No active AI provider configured"):
        service.get_provider()


@pytest.mark.django_db
def test_get_provider_missing_key():
    AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        is_active=True,
        is_default=True,
    )
    service = AIAgentService()
    with pytest.raises(ValueError, match="no API key"):
        service.get_provider()


@pytest.mark.django_db
def test_get_provider_caches_instance(monkeypatch):
    AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        api_key_dev="dev-key",
        is_active=True,
        is_default=True,
    )
    service = AIAgentService()

    fake_provider = FakeProvider()
    monkeypatch.setattr(service, "_create_provider", lambda config, api_key: fake_provider)

    provider1 = service.get_provider()
    provider2 = service.get_provider()
    assert provider1 is provider2


@pytest.mark.django_db
def test_get_api_key_from_vault_env(monkeypatch):
    config = AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        key_vault_ref="TEST",
        is_active=True,
        is_default=True,
    )
    monkeypatch.setenv("AI_PROVIDER_KEY_TEST", "vault-key")
    service = AIAgentService()
    assert service._get_api_key(config) == "vault-key"


@pytest.mark.django_db
def test_get_provider_key_retrieval_failure(monkeypatch):
    AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        key_vault_ref="MISSING",
        is_active=True,
        is_default=True,
    )
    monkeypatch.delenv("AI_PROVIDER_KEY_MISSING", raising=False)
    service = AIAgentService()
    with pytest.raises(ValueError, match="Failed to retrieve API key"):
        service.get_provider()


@pytest.mark.django_db
def test_get_provider_by_type(monkeypatch):
    AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        api_key_dev="dev-key",
        is_active=True,
    )
    AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.GROQ,
        display_name="Groq",
        model_name="llama",
        api_key_dev="groq-key",
        is_active=True,
    )
    service = AIAgentService()
    fake_provider = FakeProvider()
    monkeypatch.setattr(service, "_create_provider", lambda cfg, key: fake_provider)
    provider = service.get_provider(provider_type=AIModelProvider.ProviderType.GROQ)
    assert provider is fake_provider


@pytest.mark.django_db
def test_ask_amani_sync_success(monkeypatch, authenticated_user):
    config = AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        api_key_dev="dev-key",
        is_active=True,
        is_default=True,
    )
    service = AIAgentService()
    monkeypatch.setattr(service, "_create_provider", lambda cfg, key: FakeProvider("Please deploy"))

    result = service.ask_amani_sync(
        user_message="Hello",
        conversation_id=None,
        context={"page": "/deploy"},
        user=authenticated_user,
    )

    assert "conversation_id" in result
    assert result["requires_action"] is True
    conversation = AIConversation.objects.get(id=result["conversation_id"])
    assert conversation.provider == config
    assert conversation.messages.count() == 2


@pytest.mark.django_db
def test_ask_amani_sync_provider_error(monkeypatch, authenticated_user):
    AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        api_key_dev="dev-key",
        is_active=True,
        is_default=True,
    )
    service = AIAgentService()

    class ErrorProvider(FakeProvider):
        async def chat(self, messages):
            raise Exception("authentication failed")

    monkeypatch.setattr(service, "_create_provider", lambda cfg, key: ErrorProvider())

    result = service.ask_amani_sync(
        user_message="Hello",
        conversation_id=None,
        context=None,
        user=authenticated_user,
    )
    assert "error" in result
    assert "Invalid API key" in result["error"]


@pytest.mark.django_db
def test_ask_amani_sync_no_response(monkeypatch, authenticated_user):
    AIModelProvider.objects.create(
        provider_type=AIModelProvider.ProviderType.OPENAI,
        display_name="OpenAI",
        model_name="gpt-4o",
        api_key_dev="dev-key",
        is_active=True,
        is_default=True,
    )
    service = AIAgentService()

    class NoneProvider(FakeProvider):
        async def chat(self, messages):
            return None

    monkeypatch.setattr(service, "_create_provider", lambda cfg, key: NoneProvider())
    result = service.ask_amani_sync(
        user_message="Hello",
        conversation_id=None,
        context=None,
        user=authenticated_user,
    )
    assert "error" in result


@pytest.mark.django_db
def test_get_conversation_history_missing(authenticated_user):
    service = AIAgentService()
    history = service.get_conversation_history("00000000-0000-0000-0000-000000000000", authenticated_user)
    assert history == []


def test_create_provider_invalid_type(monkeypatch):
    service = AIAgentService()
    config = SimpleNamespace(provider_type="invalid", model_name="x", max_tokens=10, temperature=0.1)
    with pytest.raises(ValueError, match="Unsupported provider type"):
        service._create_provider(config, "key")


def test_create_provider_supported_types(monkeypatch):
    service = AIAgentService()
    monkeypatch.setattr(services, "OpenAIProvider", lambda *args, **kwargs: "openai")
    monkeypatch.setattr(services, "AnthropicProvider", lambda *args, **kwargs: "anthropic")
    monkeypatch.setattr(services, "GroqProvider", lambda *args, **kwargs: "groq")

    for provider_type, expected in [
        (AIModelProvider.ProviderType.OPENAI, "openai"),
        (AIModelProvider.ProviderType.ANTHROPIC, "anthropic"),
        (AIModelProvider.ProviderType.GROQ, "groq"),
    ]:
        config = SimpleNamespace(
            provider_type=provider_type,
            model_name="model",
            max_tokens=10,
            temperature=0.1,
        )
        assert service._create_provider(config, "key") == expected


@pytest.mark.django_db
def test_list_user_conversations(authenticated_user):
    service = AIAgentService()
    AIConversation.objects.create(
        user=authenticated_user,
        agent_type=AIAgentType.AMANI_ASSISTANT,
        title="Test",
    )
    conversations = service.list_user_conversations(authenticated_user)
    assert len(conversations) == 1
