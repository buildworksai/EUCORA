# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for health check endpoints.
"""
import pytest
from django.test import RequestFactory
from django.db import connection
from django.core.cache import cache
from apps.core.health import liveness_check, readiness_check


@pytest.mark.django_db
class TestHealthChecks:
    """Test health check endpoints."""
    
    def test_liveness_check_always_returns_200(self):
        """Test that liveness check always returns 200."""
        factory = RequestFactory()
        request = factory.get('/health/live')
        
        response = liveness_check(request)
        
        assert response.status_code == 200
        assert response.json()['status'] == 'alive'
    
    def test_readiness_check_healthy(self):
        """Test readiness check when database and cache are healthy."""
        factory = RequestFactory()
        request = factory.get('/health/ready')
        
        response = readiness_check(request)
        
        assert response.status_code == 200
        data = response.json()
        assert data['database'] is True
        assert data['cache'] is True
        assert data['status'] == 'healthy'
    
    def test_readiness_check_degraded_database(self):
        """Test readiness check when database is unavailable."""
        factory = RequestFactory()
        request = factory.get('/health/ready')
        
        # Mock database failure
        original_execute = connection.cursor
        
        def mock_cursor():
            raise Exception('Database unavailable')
        
        connection.cursor = mock_cursor
        
        try:
            response = readiness_check(request)
            assert response.status_code == 503
            data = response.json()
            assert data['database'] is False
            assert data['status'] == 'degraded'
        finally:
            connection.cursor = original_execute
    
    def test_readiness_check_degraded_cache(self):
        """Test readiness check when cache is unavailable."""
        factory = RequestFactory()
        request = factory.get('/health/ready')
        
        # Mock cache failure
        original_set = cache.set
        
        def mock_set(*args, **kwargs):
            raise Exception('Cache unavailable')
        
        cache.set = mock_set
        
        try:
            response = readiness_check(request)
            assert response.status_code == 503
            data = response.json()
            assert data['cache'] is False
            assert data['status'] == 'degraded'
        finally:
            cache.set = original_set

