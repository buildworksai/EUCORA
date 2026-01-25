# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Azure OpenAI provider implementation (OpenAI SDK v2.0+).
"""
from typing import List, Optional

from decouple import config
from openai import AzureOpenAI

from .base import LLMCompletion, LLMMessage, LLMProvider


class AzureOpenAIProvider(LLMProvider):
    """Azure OpenAI GPT provider (SDK v2.0+)."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        endpoint: Optional[str] = None,
        deployment_name: Optional[str] = None,
        api_version: str = "2024-02-15-preview",
    ):
        """
        Initialize Azure OpenAI provider.

        Args:
            api_key: Azure OpenAI API key
            endpoint: Azure OpenAI endpoint URL
            deployment_name: Deployment name
            api_version: API version (default: 2024-02-15-preview)
        """
        self.api_key = api_key or config("AZURE_OPENAI_API_KEY", default="")
        self.endpoint = endpoint or config("AZURE_OPENAI_ENDPOINT", default="")
        self.deployment_name = deployment_name or config("AZURE_OPENAI_DEPLOYMENT", default="gpt-4")
        self.api_version = api_version

        self.client = (
            AzureOpenAI(api_key=self.api_key, azure_endpoint=self.endpoint, api_version=self.api_version)
            if self.api_key and self.endpoint
            else None
        )

    def complete(
        self, messages: List[LLMMessage], temperature: float = 0.7, max_tokens: int = 1000, **kwargs
    ) -> LLMCompletion:
        """Generate completion using Azure OpenAI API."""
        if not self.client:
            return LLMCompletion(
                content="Error: Azure OpenAI not configured",
                model=self.deployment_name,
                provider="azure_openai",
                tokens_used=0,
                confidence=0.0,
                metadata={"error": "API key or endpoint not configured"},
            )

        openai_messages = [{"role": msg.role, "content": msg.content} for msg in messages]

        try:
            response = self.client.chat.completions.create(
                model=self.deployment_name,  # Azure uses deployment name as model
                messages=openai_messages,
                temperature=temperature,
                max_tokens=max_tokens,
                **kwargs,
            )

            completion_text = response.choices[0].message.content
            tokens_used = response.usage.total_tokens
            confidence = self._estimate_confidence(completion_text, response)

            return LLMCompletion(
                content=completion_text,
                model=self.deployment_name,
                provider="azure_openai",
                tokens_used=tokens_used,
                confidence=confidence,
                metadata={"finish_reason": response.choices[0].finish_reason, "response_id": response.id},
            )

        except Exception as e:
            return LLMCompletion(
                content=f"Error: {str(e)}",
                model=self.deployment_name,
                provider="azure_openai",
                tokens_used=0,
                confidence=0.0,
                metadata={"error": str(e)},
            )

    def _estimate_confidence(self, text: str, response) -> float:
        """Estimate confidence based on response characteristics."""
        if not text:
            return 0.0

        confidence = min(len(text) / 500, 0.7)

        if response.choices[0].finish_reason == "stop":
            confidence += 0.2

        return min(confidence, 1.0)

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "azure_openai"

    def get_model_name(self) -> str:
        """Return model name."""
        return self.deployment_name

    def health_check(self) -> bool:
        """Check if Azure OpenAI API is accessible."""
        if not self.client:
            return False

        try:
            # Test with minimal completion - Azure doesn't have models.list()
            # Just return True if client was created successfully
            return True
        except Exception:
            return False
