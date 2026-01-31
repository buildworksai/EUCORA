# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Local sentence-transformers provider.
"""
from typing import List

from sentence_transformers import SentenceTransformer

from apps.knowledge.embeddings.base import EmbeddingProvider


class LocalEmbeddingProvider(EmbeddingProvider):
    """Local sentence-transformers provider."""

    def __init__(self, model: str = "all-MiniLM-L6-v2"):
        self._model_name = model
        self._model = SentenceTransformer(model)
        self._dimensions = self._model.get_sentence_embedding_dimension()

    async def embed(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        embedding = self._model.encode(text, convert_to_numpy=True)
        return embedding.tolist()

    async def embed_batch(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts."""
        embeddings = self._model.encode(texts, convert_to_numpy=True)
        return embeddings.tolist()

    @property
    def dimensions(self) -> int:
        """Return embedding dimensions."""
        return self._dimensions

    @property
    def model_name(self) -> str:
        """Return model name."""
        return self._model_name
