# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Factory and manager for embedding providers.
"""
from typing import Dict, Optional

from apps.knowledge.embeddings.base import EmbeddingProvider
from apps.knowledge.embeddings.cohere import CohereEmbeddingProvider
from apps.knowledge.embeddings.local import LocalEmbeddingProvider
from apps.knowledge.embeddings.openai import OpenAIEmbeddingProvider
from apps.knowledge.models import EmbeddingConfig


class EmbeddingService:
    """Factory and manager for embedding providers."""

    _instance: Optional["EmbeddingService"] = None

    @classmethod
    def get_instance(cls) -> "EmbeddingService":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance

    def __init__(self):
        self._providers: Dict[str, EmbeddingProvider] = {}
        self._default_provider: Optional[EmbeddingProvider] = None

    async def initialize(self):
        """Load embedding configurations from database."""
        configs = EmbeddingConfig.objects.filter(is_active=True).all()

        for config in configs:
            provider = self._create_provider(config)
            self._providers[str(config.id)] = provider

            if config.is_default:
                self._default_provider = provider

    def _create_provider(self, config: EmbeddingConfig) -> EmbeddingProvider:
        """Create provider instance from config."""
        if config.provider == EmbeddingConfig.Provider.OPENAI:
            return OpenAIEmbeddingProvider(config.api_key, config.model_name)
        elif config.provider == EmbeddingConfig.Provider.COHERE:
            return CohereEmbeddingProvider(config.api_key, config.model_name)
        elif config.provider == EmbeddingConfig.Provider.LOCAL:
            return LocalEmbeddingProvider(config.model_name)
        else:
            raise ValueError(f"Unknown provider: {config.provider}")

    async def embed(self, text: str, provider_id: Optional[str] = None) -> list[float]:
        """Generate embedding for text."""
        provider = self._get_provider(provider_id)
        return await provider.embed(text)

    async def embed_batch(self, texts: list[str], provider_id: Optional[str] = None) -> list[list[float]]:
        """Generate embeddings for multiple texts."""
        provider = self._get_provider(provider_id)
        return await provider.embed_batch(texts)

    def _get_provider(self, provider_id: Optional[str] = None) -> EmbeddingProvider:
        """Get provider by ID or default."""
        if provider_id and provider_id in self._providers:
            return self._providers[provider_id]

        if self._default_provider:
            return self._default_provider

        raise ValueError("No embedding provider configured")
