# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Abstract base class for DEX API clients.

All DEX clients (1E, Mock) must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import AsyncGenerator, Dict, Optional


class DEXClientBase(ABC):
    """
    Abstract base class for DEX data providers.

    Provides a consistent interface for fetching DEX metrics regardless of source.
    """

    @abstractmethod
    async def get_experience_scores(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AsyncGenerator[Dict, None]:
        """
        Stream experience scores for all devices.

        Args:
            start_date: Optional start date filter (ISO format)
            end_date: Optional end date filter (ISO format)

        Yields:
            Device experience score dictionaries with keys:
            - device_id: str
            - device_name: str
            - dex_score: float (0-10)
            - performance_score: float (0-10)
            - stability_score: float (0-10)
            - responsiveness_score: float (0-10)
            - boot_time_seconds: int
            - login_time_seconds: int
            - user_sentiment: str (Positive/Neutral/Negative)
            - sentiment_score: float (-1 to 1)
            - carbon_footprint_kg: float
            - power_consumption_kwh: float
            - collected_at: str (ISO format)
        """
        pass

    @abstractmethod
    async def health_check(self) -> bool:
        """
        Check if the DEX provider is healthy and reachable.

        Returns:
            True if healthy, False otherwise
        """
        pass
