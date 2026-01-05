# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Abstract base class for LLM providers.
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, List, Dict, Any
import logging

logger = logging.getLogger(__name__)


class BaseModelProvider(ABC):
    """Abstract base class for LLM providers."""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        self.api_key = api_key
        self.model_name = model_name
        self.max_tokens = kwargs.get('max_tokens', 4096)
        self.temperature = kwargs.get('temperature', 0.7)
        self.endpoint_url = kwargs.get('endpoint_url')
    
    @abstractmethod
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """
        Send chat messages and get response.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters
        
        Returns:
            Response text from the model
        """
        pass
    
    @abstractmethod
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """
        Stream chat response.
        
        Args:
            messages: List of message dicts with 'role' and 'content' keys
            **kwargs: Additional provider-specific parameters
        
        Yields:
            Chunks of response text
        """
        pass
    
    def count_tokens(self, text: str) -> int:
        """
        Estimate token count (provider-specific implementation).
        Default: rough estimate of 1 token per 4 characters.
        """
        return len(text) // 4

