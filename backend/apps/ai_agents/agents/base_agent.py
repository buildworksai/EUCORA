# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Base agent class for specialized AI agents.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from ..providers.base import BaseModelProvider


class BaseAgent(ABC):
    """Base class for specialized AI agents."""
    
    def __init__(self, provider: BaseModelProvider):
        self.provider = provider
    
    @abstractmethod
    def get_system_prompt(self, context: Optional[Dict[str, Any]] = None) -> str:
        """Get system prompt for this agent."""
        pass
    
    def requires_human_action(self, response: str, user_message: str = None) -> bool:
        """
        Determine if AI response requires human action.
        Override in subclasses for agent-specific logic.
        
        Args:
            response: The AI assistant's response text
            user_message: Optional user's original message to determine intent
        """
        # Default: check for explicit approval language only
        action_keywords = [
            'requires approval',
            'needs human review',
            'must be approved',
            'awaiting approval',
            'action required',
            'human decision',
        ]
        response_lower = response.lower()
        return any(keyword in response_lower for keyword in action_keywords)

