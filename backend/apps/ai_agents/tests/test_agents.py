# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for AI agent helpers.
"""
import pytest

from apps.ai_agents.agents.amani_assistant import AmaniAssistant
from apps.ai_agents.agents.base_agent import BaseAgent


class DummyAgent(BaseAgent):
    def get_system_prompt(self, context=None) -> str:
        return "dummy"


def test_base_agent_requires_human_action():
    agent = DummyAgent(provider=None)
    assert agent.requires_human_action("This requires approval") is True
    assert agent.requires_human_action("No action needed") is False


def test_amani_system_prompt_default():
    assistant = AmaniAssistant(provider=None)
    prompt = assistant.get_system_prompt()
    assert "CRITICAL GOVERNANCE RULES" in prompt
    assert "You are Amani" in prompt


def test_amani_system_prompt_custom_with_context():
    assistant = AmaniAssistant(provider=None)
    prompt = assistant.get_system_prompt(
        {
            "custom_system_prompt": "Custom prompt",
            "page": "/deploy",
            "page_title": "Deployments",
            "environment": "demo",
        }
    )
    assert "MANDATORY GOVERNANCE RULES" in prompt
    assert "Area: Deployments" in prompt
    assert "environment: demo" in prompt


def test_amani_requires_human_action_indicators():
    assistant = AmaniAssistant(provider=None)
    assert assistant.requires_human_action("You should deploy to pilot") is True
    assert assistant.requires_human_action("Status is healthy") is False


def test_amani_contextual_suggestions():
    assistant = AmaniAssistant(provider=None)
    suggestions = assistant.get_contextual_suggestions("/cab")
    assert len(suggestions) > 0
    fallback = assistant.get_contextual_suggestions("/unknown")
    assert "How does EUCORA work?" in fallback
