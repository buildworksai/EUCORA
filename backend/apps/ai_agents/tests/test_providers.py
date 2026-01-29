# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for AI providers and base class.
"""
from types import SimpleNamespace

import pytest

from apps.ai_agents.providers import anthropic_provider, groq_provider, openai_provider
from apps.ai_agents.providers.base import BaseModelProvider


class DummyProvider(BaseModelProvider):
    async def chat(self, messages, **kwargs):
        return "ok"

    async def stream_chat(self, messages, **kwargs):
        if False:
            yield "noop"


def test_base_provider_count_tokens():
    provider = DummyProvider("key", "model")
    assert provider.count_tokens("1234") == 1
    assert provider.count_tokens("") == 0


def test_openai_provider_import_error():
    openai_provider.OPENAI_AVAILABLE = False
    with pytest.raises(ImportError):
        openai_provider.OpenAIProvider("key", "model")


@pytest.mark.anyio
async def test_openai_provider_chat_and_stream(monkeypatch):
    class FakeStream:
        def __aiter__(self):
            async def _gen():
                yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hi"))])

            return _gen()

    class FakeCompletions:
        async def create(self, *args, **kwargs):
            if kwargs.get("stream"):
                return FakeStream()
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Hello"))])

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    openai_provider.OPENAI_AVAILABLE = True
    monkeypatch.setattr(openai_provider, "AsyncOpenAI", lambda api_key: FakeClient())

    provider = openai_provider.OpenAIProvider("key", "model")
    assert await provider.chat([{"role": "user", "content": "hi"}]) == "Hello"

    chunks = []
    async for chunk in provider.stream_chat([{"role": "user", "content": "hi"}]):
        chunks.append(chunk)
    assert chunks == ["Hi"]


def test_anthropic_provider_import_error():
    anthropic_provider.ANTHROPIC_AVAILABLE = False
    with pytest.raises(ImportError):
        anthropic_provider.AnthropicProvider("key", "model")


@pytest.mark.anyio
async def test_anthropic_provider_chat_and_stream(monkeypatch):
    class FakeContent:
        def __init__(self, text):
            self.type = "text"
            self.text = text

    class FakeMessages:
        async def create(self, *args, **kwargs):
            return SimpleNamespace(content=[FakeContent("Claude")])

        def stream(self, *args, **kwargs):
            class FakeStream:
                async def __aenter__(self):
                    async def _gen():
                        yield "Stream"

                    return SimpleNamespace(text_stream=_gen())

                async def __aexit__(self, exc_type, exc, tb):
                    return False

            return FakeStream()

    class FakeClient:
        messages = FakeMessages()

    anthropic_provider.ANTHROPIC_AVAILABLE = True
    monkeypatch.setattr(anthropic_provider, "anthropic", SimpleNamespace(AsyncAnthropic=lambda api_key: FakeClient()))

    provider = anthropic_provider.AnthropicProvider("key", "model")
    assert await provider.chat([{"role": "user", "content": "hi"}]) == "Claude"

    chunks = []
    async for chunk in provider.stream_chat([{"role": "user", "content": "hi"}]):
        chunks.append(chunk)
    assert chunks == ["Stream"]


def test_groq_provider_import_error():
    groq_provider.GROQ_AVAILABLE = False
    with pytest.raises(ImportError):
        groq_provider.GroqProvider("key", "model")


@pytest.mark.anyio
async def test_groq_provider_chat_and_stream(monkeypatch):
    class FakeStream:
        def __aiter__(self):
            async def _gen():
                yield SimpleNamespace(choices=[SimpleNamespace(delta=SimpleNamespace(content="Hi"))])

            return _gen()

    class FakeCompletions:
        async def create(self, *args, **kwargs):
            if kwargs.get("stream"):
                return FakeStream()
            return SimpleNamespace(choices=[SimpleNamespace(message=SimpleNamespace(content="Groq"))])

    class FakeChat:
        completions = FakeCompletions()

    class FakeClient:
        chat = FakeChat()

    groq_provider.GROQ_AVAILABLE = True
    monkeypatch.setattr(groq_provider, "AsyncGroq", lambda api_key: FakeClient())

    provider = groq_provider.GroqProvider("key", "model")
    assert await provider.chat([{"role": "user", "content": "hi"}]) == "Groq"

    chunks = []
    async for chunk in provider.stream_chat([{"role": "user", "content": "hi"}]):
        chunks.append(chunk)
    assert chunks == ["Hi"]
