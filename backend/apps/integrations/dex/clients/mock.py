# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Mock DEX data provider for development and demo environments.

Generates realistic DEX metrics without requiring a live 1E server.
"""
import random
from datetime import datetime
from typing import AsyncGenerator, Dict, Optional

from apps.integrations.dex.clients.base import DEXClientBase


class MockDEXClient(DEXClientBase):
    """
    Mock DEX data provider.

    Generates realistic DEX scores for 500 mock devices.
    Supports reproducible seeds for testing.
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize mock client.

        Args:
            seed: Optional random seed for reproducible data
        """
        if seed is not None:
            random.seed(seed)
        self._seed = seed

    async def get_experience_scores(
        self,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None,
    ) -> AsyncGenerator[Dict, None]:
        """
        Generate mock DEX scores for 500 devices.

        Args:
            start_date: Optional start date filter (ignored for mock)
            end_date: Optional end date filter (ignored for mock)

        Yields:
            Device experience score dictionaries
        """
        # Generate 500 mock devices
        for i in range(500):
            # Realistic DEX score distribution (most devices score 6-9)
            dex_score = round(random.uniform(5.0, 9.5), 2)
            performance_score = round(random.uniform(5.0, 9.5), 2)
            stability_score = round(random.uniform(6.0, 9.8), 2)
            responsiveness_score = round(random.uniform(4.0, 9.0), 2)

            # Boot time: most devices boot in 20-60 seconds
            boot_time_seconds = random.randint(15, 120)
            login_time_seconds = random.randint(5, 45)

            # Sentiment distribution: ~60% positive, ~30% neutral, ~10% negative
            sentiment_roll = random.random()
            if sentiment_roll < 0.6:
                user_sentiment = "Positive"
                sentiment_score = round(random.uniform(0.3, 1.0), 2)
            elif sentiment_roll < 0.9:
                user_sentiment = "Neutral"
                sentiment_score = round(random.uniform(-0.2, 0.3), 2)
            else:
                user_sentiment = "Negative"
                sentiment_score = round(random.uniform(-1.0, -0.1), 2)

            # Green IT: realistic carbon footprint (50-200 kg CO2/year)
            carbon_footprint_kg = round(random.uniform(50, 200), 1)
            power_consumption_kwh = round(random.uniform(20, 80), 1)

            yield {
                "device_id": f"MOCK-DEV-{i:05d}",
                "device_name": f"Device-{i:05d}",
                "dex_score": dex_score,
                "performance_score": performance_score,
                "stability_score": stability_score,
                "responsiveness_score": responsiveness_score,
                "boot_time_seconds": boot_time_seconds,
                "login_time_seconds": login_time_seconds,
                "user_sentiment": user_sentiment,
                "sentiment_score": sentiment_score,
                "carbon_footprint_kg": carbon_footprint_kg,
                "power_consumption_kwh": power_consumption_kwh,
                "collected_at": datetime.utcnow().isoformat(),
            }

    async def health_check(self) -> bool:
        """
        Mock health check always returns True.

        Returns:
            True (mock provider is always available)
        """
        return True
