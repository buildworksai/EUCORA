# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Prompt templates and registry.
"""
from .base import PromptRegistry, PromptTemplate
from .templates import registry

__all__ = ["PromptTemplate", "PromptRegistry", "registry"]
