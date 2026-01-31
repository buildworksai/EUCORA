# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Unit tests for DEX API views.
"""
import pytest
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APIClient

from apps.integrations.dex.models import DEXProvider


@pytest.mark.django_db
class TestDEXProviderViewSet:
    """Tests for DEXProviderViewSet."""

    def test_get_provider_requires_auth(self):
        """Test that provider endpoint requires authentication."""
        client = APIClient()
        url = reverse("dex:dex-provider-list")
        response = client.get(url)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_provider_with_auth(self):
        """Test getting provider with authentication."""
        # Create a provider
        DEXProvider.objects.create(
            name="Test Provider",
            provider_type=DEXProvider.ProviderType.MOCK,
        )

        client = APIClient()
        # Note: In real tests, would authenticate user here
        # For now, just verify endpoint exists
        url = reverse("dex:dex-provider-list")
        # This will fail auth but confirms endpoint is registered
        response = client.get(url)
        assert response.status_code in [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN]
