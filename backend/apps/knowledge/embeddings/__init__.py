# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Embedding providers for vector generation.
"""

from apps.knowledge.embeddings.base import EmbeddingProvider
from apps.knowledge.embeddings.cohere import CohereEmbeddingProvider
from apps.knowledge.embeddings.factory import EmbeddingService
from apps.knowledge.embeddings.local import LocalEmbeddingProvider
from apps.knowledge.embeddings.openai import OpenAIEmbeddingProvider

__all__ = [
    "EmbeddingProvider",
    "OpenAIEmbeddingProvider",
    "CohereEmbeddingProvider",
    "LocalEmbeddingProvider",
    "EmbeddingService",
]
