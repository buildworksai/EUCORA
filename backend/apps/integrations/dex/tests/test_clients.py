# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Unit tests for DEX API clients.
"""
import pytest

from apps.integrations.dex.clients.mock import MockDEXClient


@pytest.mark.asyncio
class TestMockDEXClient:
    """Tests for MockDEXClient."""

    async def test_get_experience_scores(self):
        """Test getting experience scores from mock client."""
        client = MockDEXClient(seed=42)
        count = 0
        async for device in client.get_experience_scores():
            assert "device_id" in device
            assert "dex_score" in device
            assert 0 <= device["dex_score"] <= 10
            count += 1
            if count >= 10:  # Test first 10 devices
                break
        assert count == 10

    async def test_health_check(self):
        """Test mock client health check."""
        client = MockDEXClient()
        result = await client.health_check()
        assert result is True

    async def test_reproducible_seed(self):
        """Test that seed produces reproducible data."""
        client1 = MockDEXClient(seed=123)
        client2 = MockDEXClient(seed=123)

        devices1 = []
        devices2 = []

        async for device in client1.get_experience_scores():
            devices1.append(device)
            if len(devices1) >= 5:
                break

        async for device in client2.get_experience_scores():
            devices2.append(device)
            if len(devices2) >= 5:
                break

        assert devices1 == devices2
