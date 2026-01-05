# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for authentication views.
"""
import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock


@pytest.mark.django_db
class TestAuthenticationViews:
    """Test authentication view endpoints."""
    
    def test_entra_id_login_missing_code(self, api_client):
        """Test login without authorization code."""
        url = reverse('authentication:login')
        response = api_client.post(url, {}, format='json')
        
        assert response.status_code == 400
        assert 'error' in response.data
    
    @patch('apps.authentication.views._exchange_code_for_token')
    def test_entra_id_login_invalid_code(self, mock_exchange_token, api_client):
        """Test login with invalid authorization code."""
        mock_exchange_token.side_effect = Exception('Invalid code')
        
        url = reverse('authentication:login')
        response = api_client.post(url, {
            'code': 'invalid-code',
        }, format='json')
        
        assert response.status_code == 401
        assert 'error' in response.data
    
    def test_logout(self, authenticated_client, authenticated_user):
        """Test logout endpoint."""
        url = reverse('authentication:logout')
        response = authenticated_client.post(url)
        
        assert response.status_code == 200
        assert 'message' in response.data
    
    def test_current_user(self, authenticated_client, authenticated_user):
        """Test current user endpoint."""
        url = reverse('authentication:current-user')
        response = authenticated_client.get(url)
        
        assert response.status_code == 200
        assert 'user' in response.data
        assert response.data['user']['username'] == authenticated_user.username
    
    def test_current_user_unauthenticated(self, api_client):
        """Test current user endpoint without authentication."""
        url = reverse('authentication:current-user')
        response = api_client.get(url)
        
        assert response.status_code == 403  # Forbidden
