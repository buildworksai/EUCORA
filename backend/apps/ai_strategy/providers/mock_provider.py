# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Mock LLM provider for testing and air-gapped environments.
"""
from typing import List

from .base import LLMCompletion, LLMMessage, LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock provider for testing without external API calls."""

    def __init__(self, model: str = "mock-gpt"):
        """Initialize mock provider."""
        self.model = model
        self.call_count = 0

    def complete(
        self, messages: List[LLMMessage], temperature: float = 0.7, max_tokens: int = 1000, **kwargs
    ) -> LLMCompletion:
        """Generate mock completion."""
        self.call_count += 1

        # Extract last user message
        user_messages = [m for m in messages if m.role == "user"]
        last_message = user_messages[-1].content if user_messages else ""

        # Simple response based on content - order matters!
        # Check for remediation keywords first (before risk/deployment which may overlap)
        if "remediate" in last_message.lower() or "fix" in last_message.lower() or "suggest" in last_message.lower():
            response = """Suggested remediation steps:
Steps:
1. Update to latest version
2. Restart service
3. Verify functionality

Rollback: Revert to previous version if issues persist
Risk: LOW"""
        elif "classify" in last_message.lower() or "incident" in last_message.lower():
            response = """Classification: MEDIUM severity incident.
Severity: MEDIUM
Confidence: 0.85
Reasoning: Mock classification based on incident description."""
        elif "search" in last_message.lower():
            response = "Knowledge base result: No exact match found."
        elif "risk" in last_message.lower() or "deployment" in last_message.lower():
            response = """Risk Score: 45/100
Factors: Privilege level, scan results
Recommendation: APPROVE with monitoring"""
        else:
            response = f"Mock response to: {last_message[:50]}..."

        return LLMCompletion(
            content=response,
            model=self.model,
            provider="mock",
            tokens_used=len(response),
            confidence=0.85,
            reasoning="Mock provider always returns high confidence",
            metadata={"call_count": self.call_count},
        )

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "mock"

    def get_model_name(self) -> str:
        """Return model name."""
        return self.model

    def health_check(self) -> bool:
        """Mock provider is always healthy."""
        return True
