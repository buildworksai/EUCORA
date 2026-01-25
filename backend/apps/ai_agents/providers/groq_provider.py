# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Groq provider implementation.
"""
import logging
from typing import AsyncGenerator, Dict, List

from .base import BaseModelProvider

logger = logging.getLogger(__name__)

try:
    from groq import AsyncGroq

    GROQ_AVAILABLE = True
except ImportError:
    GROQ_AVAILABLE = False
    logger.warning("Groq SDK not installed. Install with: pip install groq")


class GroqProvider(BaseModelProvider):
    """Groq provider implementation."""

    def __init__(self, api_key: str, model_name: str, **kwargs):
        if not GROQ_AVAILABLE:
            raise ImportError("Groq SDK not installed. Install with: pip install groq")

        super().__init__(api_key, model_name, **kwargs)
        self.client = AsyncGroq(api_key=api_key)

    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send chat messages and get response."""
        try:
            response = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Groq API error: {e}")
            raise

    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat response."""
        try:
            stream = await self.client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                max_tokens=kwargs.get("max_tokens", self.max_tokens),
                temperature=kwargs.get("temperature", self.temperature),
                stream=True,
            )
            async for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
        except Exception as e:
            logger.error(f"Groq streaming error: {e}")
            raise
