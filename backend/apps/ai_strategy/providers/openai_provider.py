# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
OpenAI provider implementation (OpenAI SDK v2.0+).
"""
from typing import List, Optional

from decouple import config
from openai import OpenAI

from .base import LLMCompletion, LLMMessage, LLMProvider


class OpenAIProvider(LLMProvider):
    """OpenAI GPT provider (SDK v2.0+)."""

    def __init__(self, api_key: Optional[str] = None, model: str = "gpt-4"):
        """
        Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (or from config)
            model: Model name (default: gpt-4)
        """
        self.api_key = api_key or config("OPENAI_API_KEY", default="")
        self.model = model
        self.client = OpenAI(api_key=self.api_key) if self.api_key else None

    def complete(
        self, messages: List[LLMMessage], temperature: float = 0.7, max_tokens: int = 1000, **kwargs
    ) -> LLMCompletion:
        """Generate completion using OpenAI API."""
        if not self.client:
            return LLMCompletion(
                content="Error: OpenAI API key not configured",
                model=self.model,
                provider="openai",
                tokens_used=0,
                confidence=0.0,
                metadata={"error": "API key not configured"},
            )

        # Convert to OpenAI format
        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        try:
            response = self.client.chat.completions.create(
                model=self.model, messages=openai_messages, temperature=temperature, max_tokens=max_tokens, **kwargs
            )

            completion_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens

            # Extract confidence from response (if available)
            # For GPT-4, we use a heuristic based on response characteristics
            confidence = self._estimate_confidence(completion_text, response)

            return LLMCompletion(
                content=completion_text,
                model=self.model,
                provider="openai",
                tokens_used=tokens_used,
                confidence=confidence,
                metadata={"finish_reason": response.choices[0].finish_reason, "response_id": response.id},
            )

        except Exception as e:
            # Fallback response on error
            return LLMCompletion(
                content=f"Error: {str(e)}",
                model=self.model,
                provider="openai",
                tokens_used=0,
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _estimate_confidence(self, text: str, response) -> float:
        """
        Estimate confidence based on response characteristics.

        Heuristic: longer, more detailed responses = higher confidence.
        """
        if not text:
            return 0.0

        # Base confidence from text length
        confidence = min(len(text) / 500, 0.7)

        # Boost if response was complete
        if response.choices[0].finish_reason == "stop":
            confidence += 0.2

        return min(confidence, 1.0)

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "openai"

    def get_model_name(self) -> str:
        """Return model name."""
        return self.model

    def health_check(self) -> bool:
        """Check if OpenAI API is accessible."""
        if not self.client:
            return False

        try:
            # Test with minimal completion
            self.client.models.list()
            return True
        except Exception:
            return False
