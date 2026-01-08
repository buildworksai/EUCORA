# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for authentication views.
"""
import pytest
from django.urls import reverse
from unittest.mock import patch, MagicMock
from django.conf import settings
from apps.authentication.views import _exchange_code_for_token, _get_user_profile


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

    def test_password_login_success(self, api_client, authenticated_user):
        """Test email/password login."""
        url = reverse('authentication:login')
        response = api_client.post(url, {
            'email': authenticated_user.email,
            'password': 'testpass123',
        }, format='json')

        assert response.status_code == 200
        assert response.data['user']['email'] == authenticated_user.email

    def test_password_login_failure(self, api_client, authenticated_user):
        """Test login with invalid password."""
        url = reverse('authentication:login')
        response = api_client.post(url, {
            'username': authenticated_user.username,
            'password': 'wrong',
        }, format='json')

        assert response.status_code == 401
    
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

    def test_validate_session(self, authenticated_client):
        url = reverse('authentication:validate-session')
        response = authenticated_client.get(url)
        assert response.status_code == 200
        assert response.data['valid'] is True

    @patch('apps.authentication.views._exchange_code_for_token')
    @patch('apps.authentication.views._get_user_profile')
    def test_entra_id_login_success(self, mock_profile, mock_exchange, api_client):
        mock_exchange.return_value = {'access_token': 'token'}
        mock_profile.return_value = {
            'userPrincipalName': 'entra@example.com',
            'mail': 'entra@example.com',
            'givenName': 'Entra',
            'surname': 'User',
        }

        url = reverse('authentication:login')
        response = api_client.post(url, {'code': 'valid-code'}, format='json')
        assert response.status_code == 200
        assert response.data['user']['email'] == 'entra@example.com'

    @patch('apps.authentication.views._exchange_code_for_token')
    @patch('apps.authentication.views._get_user_profile')
    def test_entra_id_profile_failure(self, mock_profile, mock_exchange, api_client):
        mock_exchange.return_value = {'access_token': 'token'}
        mock_profile.side_effect = Exception('profile error')

        url = reverse('authentication:login')
        response = api_client.post(url, {'code': 'valid-code'}, format='json')
        assert response.status_code == 401


def test_exchange_code_missing_settings(monkeypatch):
    monkeypatch.setattr(settings, "ENTRA_ID_TENANT_ID", "")
    monkeypatch.setattr(settings, "ENTRA_ID_CLIENT_ID", "")
    monkeypatch.setattr(settings, "ENTRA_ID_CLIENT_SECRET", "")
    with pytest.raises(Exception, match="Entra ID not configured"):
        _exchange_code_for_token("code", "http://localhost")


@patch("apps.authentication.views.requests.post")
def test_exchange_code_success(mock_post, monkeypatch):
    monkeypatch.setattr(settings, "ENTRA_ID_TENANT_ID", "tenant")
    monkeypatch.setattr(settings, "ENTRA_ID_CLIENT_ID", "client")
    monkeypatch.setattr(settings, "ENTRA_ID_CLIENT_SECRET", "secret")
    mock_response = MagicMock()
    mock_response.json.return_value = {"access_token": "token"}
    mock_response.raise_for_status.return_value = None
    mock_post.return_value = mock_response
    result = _exchange_code_for_token("code", "http://localhost")
    assert result["access_token"] == "token"


@patch("apps.authentication.views.requests.get")
def test_get_user_profile_success(mock_get):
    mock_response = MagicMock()
    mock_response.json.return_value = {"userPrincipalName": "user@example.com"}
    mock_response.raise_for_status.return_value = None
    mock_get.return_value = mock_response
    profile = _get_user_profile("token")
    assert profile["userPrincipalName"] == "user@example.com"
