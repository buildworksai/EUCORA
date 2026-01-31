# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Cohere embedding provider.
"""
from typing import List

import cohere

from apps.knowledge.embeddings.base import EmbeddingProvider


class CohereEmbeddingProvider(EmbeddingProvider):
    """Cohere embedding provider."""

    def __init__(self, api_key: str, model: str = "embed-english-v3.0"):
        self.client = cohere.AsyncClient(api_key=api_key)
        self._model = model
        self._dimensions = 1024  # Cohere v3 default

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        response = await self.client.embed(texts=[text], model=self._model, input_type="search_document")
        return response.embeddings[0]

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        response = await self.client.embed(texts=texts, model=self._model, input_type="search_document")
        return response.embeddings

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model
