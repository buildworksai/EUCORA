# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Core AI agent service for orchestration.
Enforces governance: all AI recommendations require human approval.
"""
import logging
from typing import Dict, Any, Optional, List
from django.contrib.auth.models import User

from .models import AIModelProvider, AIConversation, AIMessage, AIAgentType, AIAgentTask
from .providers import OpenAIProvider, AnthropicProvider, GroqProvider

logger = logging.getLogger(__name__)


class AIAgentService:
    """
    Core service for AI agent orchestration.
    Enforces governance: all AI recommendations require human approval.
    """
    
    def __init__(self):
        self._provider_cache: Dict[str, Any] = {}
    
    def _get_api_key(self, config: AIModelProvider) -> str:
        """
        Retrieve API key from the model configuration.
        Priority:
        1. Direct dev key (for development/demo only)
        2. Vault reference (for production)
        """
        # DEV MODE: Check for direct API key in database
        if config.api_key_dev:
            logger.debug(f"Using api_key_dev for provider {config.provider_type}")
            return config.api_key_dev
        
        # PRODUCTION: Retrieve from vault using reference
        if config.key_vault_ref:
            import os
            # Placeholder: In production, integrate with your vault solution
            api_key = os.getenv(f"AI_PROVIDER_KEY_{config.key_vault_ref}", "")
            if api_key:
                return api_key
        
        return ""
    
    def _create_provider(self, config: AIModelProvider, api_key: str):
        """Create provider instance based on configuration."""
        provider_type = config.provider_type
        
        if provider_type == AIModelProvider.ProviderType.OPENAI:
            return OpenAIProvider(api_key, config.model_name, max_tokens=config.max_tokens, temperature=config.temperature)
        elif provider_type == AIModelProvider.ProviderType.ANTHROPIC:
            return AnthropicProvider(api_key, config.model_name, max_tokens=config.max_tokens, temperature=config.temperature)
        elif provider_type == AIModelProvider.ProviderType.GROQ:
            return GroqProvider(api_key, config.model_name, max_tokens=config.max_tokens, temperature=config.temperature)
        else:
            raise ValueError(f"Unsupported provider type: {provider_type}")
    
    def get_provider(self, provider_type: str = None) -> Any:
        """Get configured provider instance."""
        if provider_type is None:
            # Get default provider
            config = AIModelProvider.objects.filter(is_default=True, is_active=True).first()
            if not config:
                # Fallback to first active provider
                config = AIModelProvider.objects.filter(is_active=True).first()
        else:
            config = AIModelProvider.objects.filter(
                provider_type=provider_type,
                is_active=True
            ).first()
        
        if not config:
            raise ValueError("No active AI provider configured")
        
        # Check cache
        cache_key = f"{config.provider_type}_{config.model_name}"
        if cache_key in self._provider_cache:
            return self._provider_cache[cache_key]
        
        # Check if API key is configured (either dev key or vault ref)
        if not config.api_key_dev and not config.key_vault_ref:
            raise ValueError(f"Provider {config.provider_type} has no API key configured")
        
        # Get API key
        api_key = self._get_api_key(config)
        if not api_key:
            raise ValueError(f"Failed to retrieve API key for provider {config.provider_type}")
        
        provider = self._create_provider(config, api_key)
        self._provider_cache[cache_key] = provider
        
        return provider
    
    def ask_amani_sync(
        self,
        user_message: str,
        conversation_id: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None,
        user: Optional[User] = None
    ) -> Dict[str, Any]:
        """
        "Ask Amani" - General assistant endpoint (synchronous wrapper).
        Returns recommendation + whether human action is required.
        """
        from .agents.amani_assistant import AmaniAssistant
        import asyncio
        
        # Get or create conversation (sync Django ORM)
        if conversation_id:
            try:
                conversation = AIConversation.objects.get(id=conversation_id, user=user)
            except AIConversation.DoesNotExist:
                conversation = AIConversation.objects.create(
                    user=user,
                    agent_type=AIAgentType.AMANI_ASSISTANT,
                    title=user_message[:100]
                )
        else:
            conversation = AIConversation.objects.create(
                user=user,
                agent_type=AIAgentType.AMANI_ASSISTANT,
                title=user_message[:100]
            )
        
        # Get default provider (sync)
        try:
            provider = self.get_provider()
            provider_config = AIModelProvider.objects.filter(is_default=True, is_active=True).first()
            if not provider_config:
                provider_config = AIModelProvider.objects.filter(is_active=True).first()
        except Exception as e:
            logger.error(f"Failed to get AI provider: {e}")
            return {
                'error': 'AI provider not configured. Please configure a model provider in Settings.',
                'conversation_id': str(conversation.id),
            }
        
        # Update conversation with provider (sync)
        conversation.provider = provider_config
        conversation.save()
        
        # Load conversation history (sync)
        history = list(
            conversation.messages.order_by('created_at').values('role', 'content')
        )
        
        # Get contextual system prompt
        assistant = AmaniAssistant(provider)
        system_prompt = assistant.get_system_prompt(context)
        
        # Prepare messages
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})
        
        # Generate response (run async provider.chat in sync context)
        response_text = None
        loop = None
        try:
            # Create new event loop for this sync call
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            response_text = loop.run_until_complete(provider.chat(messages))
        except Exception as e:
            error_msg = str(e)
            # Provide more specific error messages for common cases
            if 'authentication' in error_msg.lower() or '401' in error_msg or 'api_key' in error_msg.lower():
                error_msg = 'Invalid API key. Please check your API key in Settings and try again.'
            elif 'rate_limit' in error_msg.lower() or '429' in error_msg:
                error_msg = 'Rate limit exceeded. Please wait a moment and try again.'
            elif 'model' in error_msg.lower() and 'not found' in error_msg.lower():
                error_msg = 'The selected model is not available. Please choose a different model in Settings.'
            else:
                error_msg = f'AI provider error: {error_msg}'
            
            logger.error(f"AI provider error: {e}")
            return {
                'error': error_msg,
                'conversation_id': str(conversation.id),
            }
        finally:
            if loop:
                loop.close()
        
        # If response_text is still None, something went wrong
        if response_text is None:
            return {
                'error': 'Failed to get response from AI provider',
                'conversation_id': str(conversation.id),
            }
        
        # Determine if human action is required
        requires_action = assistant.requires_human_action(response_text)
        
        # Store messages (immutable audit trail) - sync Django ORM
        AIMessage.objects.create(
            conversation=conversation,
            role='user',
            content=user_message,
            token_count=provider.count_tokens(user_message)
        )
        
        ai_message = AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=response_text,
            model_used=provider_config.model_name,
            token_count=provider.count_tokens(response_text),
            requires_human_action=requires_action
        )
        
        return {
            'conversation_id': str(conversation.id),
            'message_id': str(ai_message.id),
            'response': response_text,
            'requires_action': requires_action
        }
    
    def get_conversation_history(self, conversation_id: str, user: User) -> List[Dict[str, Any]]:
        """Get conversation history."""
        try:
            conversation = AIConversation.objects.get(id=conversation_id, user=user)
            messages = conversation.messages.order_by('created_at')
            
            return [
                {
                    'id': str(msg.id),
                    'role': msg.role,
                    'content': msg.content,
                    'timestamp': msg.created_at.isoformat(),
                    'requires_action': msg.requires_human_action,
                }
                for msg in messages
            ]
        except AIConversation.DoesNotExist:
            return []
    
    def list_user_conversations(self, user: User, agent_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """List user's conversations."""
        queryset = AIConversation.objects.filter(user=user, is_active=True)
        
        if agent_type:
            queryset = queryset.filter(agent_type=agent_type)
        
        conversations = queryset.order_by('-created_at')[:50]
        
        return [
            {
                'id': str(conv.id),
                'agent_type': conv.agent_type,
                'title': conv.title,
                'created_at': conv.created_at.isoformat(),
                'message_count': conv.messages.count(),
            }
            for conv in conversations
        ]


# Singleton instance
_ai_agent_service = None

def get_ai_agent_service() -> AIAgentService:
    """Get singleton AI agent service instance."""
    global _ai_agent_service
    if _ai_agent_service is None:
        _ai_agent_service = AIAgentService()
    return _ai_agent_service

