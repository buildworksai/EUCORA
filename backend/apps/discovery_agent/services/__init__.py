# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Discovery Agent services.
"""
from .gap_analysis import GapAnalysisEngine
from .normalization import ApplicationNormalizer

__all__ = [
    "ApplicationNormalizer",
    "GapAnalysisEngine",
]
