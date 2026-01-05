# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Anthropic provider implementation.
"""
import logging
from typing import List, Dict, AsyncGenerator
from .base import BaseModelProvider

logger = logging.getLogger(__name__)

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False
    logger.warning("Anthropic SDK not installed. Install with: pip install anthropic")


class AnthropicProvider(BaseModelProvider):
    """Anthropic provider implementation."""
    
    def __init__(self, api_key: str, model_name: str, **kwargs):
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic SDK not installed. Install with: pip install anthropic")
        
        super().__init__(api_key, model_name, **kwargs)
        self.client = anthropic.AsyncAnthropic(api_key=api_key)
    
    async def chat(self, messages: List[Dict[str, str]], **kwargs) -> str:
        """Send chat messages and get response."""
        try:
            # Convert messages format for Anthropic API
            system_message = None
            conversation_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    conversation_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            response = await self.client.messages.create(
                model=self.model_name,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', self.temperature),
                system=system_message,
                messages=conversation_messages,
            )
            
            # Extract text from response
            text_content = ""
            for content_block in response.content:
                if content_block.type == 'text':
                    text_content += content_block.text
            
            return text_content
        except Exception as e:
            logger.error(f"Anthropic API error: {e}")
            raise
    
    async def stream_chat(self, messages: List[Dict[str, str]], **kwargs) -> AsyncGenerator[str, None]:
        """Stream chat response."""
        try:
            system_message = None
            conversation_messages = []
            
            for msg in messages:
                if msg['role'] == 'system':
                    system_message = msg['content']
                else:
                    conversation_messages.append({
                        'role': msg['role'],
                        'content': msg['content']
                    })
            
            async with self.client.messages.stream(
                model=self.model_name,
                max_tokens=kwargs.get('max_tokens', self.max_tokens),
                temperature=kwargs.get('temperature', self.temperature),
                system=system_message,
                messages=conversation_messages,
            ) as stream:
                async for text in stream.text_stream:
                    yield text
        except Exception as e:
            logger.error(f"Anthropic streaming error: {e}")
            raise

