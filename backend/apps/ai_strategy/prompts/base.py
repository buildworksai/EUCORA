# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Prompt engineering framework.
"""
from dataclasses import dataclass
from typing import Any, Dict, List

from ..providers.base import LLMMessage


@dataclass
class PromptTemplate:
    """
    Prompt template with version control.
    """

    name: str
    version: str
    system_message: str
    user_template: str
    description: str
    metadata: Dict[str, Any]

    def format(self, **kwargs) -> List[LLMMessage]:
        """
        Format template with variables.

        Args:
            **kwargs: Template variables

        Returns:
            List of LLMMessage
        """
        return [
            LLMMessage(role="system", content=self.system_message),
            LLMMessage(role="user", content=self.user_template.format(**kwargs)),
        ]


class PromptRegistry:
    """Registry for prompt templates."""

    def __init__(self):
        """Initialize registry."""
        self._templates: Dict[str, PromptTemplate] = {}

    def register(self, template: PromptTemplate):
        """Register a prompt template."""
        key = f"{template.name}:{template.version}"
        self._templates[key] = template

    def get(self, name: str, version: str = "v1") -> PromptTemplate:
        """Get prompt template by name and version."""
        key = f"{name}:{version}"
        if key not in self._templates:
            raise KeyError(f"Prompt template not found: {key}")
        return self._templates[key]

    def list_templates(self) -> List[str]:
        """List all registered templates."""
        return list(self._templates.keys())
