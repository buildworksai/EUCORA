# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Base LLM provider abstraction.
"""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional


@dataclass
class LLMCompletion:
    """LLM completion response."""

    content: str
    model: str
    provider: str
    tokens_used: int
    confidence: float  # 0.0-1.0
    reasoning: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class LLMMessage:
    """LLM message format."""

    role: str  # system, user, assistant
    content: str


class LLMProvider(ABC):
    """
    Abstract base class for LLM providers.

    All providers must implement this interface for swappability.
    """

    @abstractmethod
    def complete(
        self, messages: List[LLMMessage], temperature: float = 0.7, max_tokens: int = 1000, **kwargs
    ) -> LLMCompletion:
        """
        Generate completion from messages.

        Args:
            messages: List of conversation messages
            temperature: Sampling temperature (0.0-1.0)
            max_tokens: Maximum tokens to generate
            **kwargs: Provider-specific parameters

        Returns:
            LLMCompletion with content and metadata
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return provider name."""
        pass

    @abstractmethod
    def get_model_name(self) -> str:
        """Return model name."""
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """
        Check if provider is available.

        Returns:
            True if provider is healthy
        """
        pass
