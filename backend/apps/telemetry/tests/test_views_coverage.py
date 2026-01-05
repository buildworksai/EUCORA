# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Additional tests for telemetry views to reach 90% coverage.
"""
import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.db import DatabaseError


@pytest.mark.django_db
class TestTelemetryViewsCoverage:
    """Additional tests for telemetry views coverage."""
    
    @patch('apps.telemetry.views.connection')
    def test_health_check_database_failure(self, mock_connection, api_client):
        """Test health check with database failure."""
        mock_cursor = MagicMock()
        mock_cursor.__enter__.side_effect = DatabaseError('DB connection failed')
        mock_connection.cursor.return_value = mock_cursor
        
        url = reverse('telemetry:health')
        response = api_client.get(url)
        
        assert response.status_code == 503
        assert response.data['status'] == 'unhealthy'
        assert response.data['checks']['database']['status'] == 'unhealthy'
    
    @patch('apps.telemetry.views.cache')
    def test_health_check_cache_read_failure(self, mock_cache, api_client):
        """Test health check with cache read failure (value mismatch)."""
        mock_cache.get.return_value = 'wrong-value'
        
        url = reverse('telemetry:health')
        response = api_client.get(url)
        
        assert response.status_code == 503
        assert response.data['status'] == 'unhealthy'
        assert response.data['checks']['cache']['status'] == 'unhealthy'
    
    @patch('apps.telemetry.views.cache')
    def test_health_check_cache_exception(self, mock_cache, api_client):
        """Test health check with cache exception."""
        mock_cache.set.side_effect = Exception('Redis down')
        
        url = reverse('telemetry:health')
        response = api_client.get(url)
        
        assert response.status_code == 503
        assert response.data['status'] == 'unhealthy'
        assert response.data['checks']['cache']['status'] == 'unhealthy'
    
    def test_readiness_check_structure(self, api_client):
        """Test readiness check structure is identical to health check."""
        url = reverse('telemetry:readiness')
        response = api_client.get(url)
        
        assert response.status_code == 200
        assert 'status' in response.data
        assert 'checks' in response.data
        assert 'database' in response.data['checks']
