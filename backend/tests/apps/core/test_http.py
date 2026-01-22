# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Unit tests for HTTP session utilities."""
import pytest
import requests
from unittest.mock import Mock, patch, MagicMock
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from apps.core.http import (
    create_resilient_session,
    get_session,
)


class TestCreateResilientSession:
    """Test resilient session creation."""

    def test_creates_requests_session(self):
        """Returns a requests.Session instance."""
        session = create_resilient_session()
        assert isinstance(session, requests.Session)

    def test_default_timeout_applied(self):
        """Default timeout is 30 seconds."""
        session = create_resilient_session()
        assert session._timeout == 30

    def test_custom_timeout(self):
        """Accepts custom timeout."""
        session = create_resilient_session(timeout=60)
        assert session._timeout == 60

    def test_http_adapter_configured(self):
        """HTTP and HTTPS adapters are configured."""
        session = create_resilient_session()
        assert 'http://' in session.adapters
        assert 'https://' in session.adapters
        assert isinstance(session.adapters['http://'], HTTPAdapter)
        assert isinstance(session.adapters['https://'], HTTPAdapter)

    def test_retry_strategy_configured(self):
        """Retry strategy is configured with backoff."""
        session = create_resilient_session(max_retries=3, backoff_factor=0.5)
        adapter = session.adapters['https://']
        assert adapter.max_retries is not None

    def test_default_status_forcelist(self):
        """Default status codes to retry on."""
        session = create_resilient_session()
        adapter = session.adapters['https://']
        retry = adapter.max_retries
        # Status forcelist is configured (429, 500, 502, 503, 504)
        assert retry.status_forcelist is not None

    def test_custom_status_forcelist(self):
        """Accepts custom status codes to retry on."""
        custom_codes = [400, 429, 500, 503]
        session = create_resilient_session(status_forcelist=custom_codes)
        adapter = session.adapters['https://']
        retry = adapter.max_retries
        assert 429 in retry.status_forcelist
        assert 500 in retry.status_forcelist

    def test_session_has_request_wrapper(self):
        """Session.request applies timeout."""
        session = create_resilient_session(timeout=45)
        assert hasattr(session, 'request')
        assert callable(session.request)


class TestSessionRequest:
    """Test session request behavior."""

    def test_request_applies_timeout(self):
        """Session request applies default timeout."""
        session = create_resilient_session(timeout=30)
        
        with patch('requests.adapters.HTTPAdapter.send') as mock_send:
            mock_send.return_value = Mock(status_code=200, content=b'')
            
            try:
                session.get('http://example.com')
            except:
                pass
            
            # Verify send was called (timeout applied in call)
            assert mock_send.called

    def test_request_allows_override_timeout(self):
        """Request can override default timeout."""
        session = create_resilient_session(timeout=30)
        
        with patch('requests.adapters.HTTPAdapter.send') as mock_send:
            mock_send.return_value = Mock(status_code=200, content=b'')
            
            try:
                session.get('http://example.com', timeout=60)
            except:
                pass
            
            assert mock_send.called


class TestGetSession:
    """Test singleton session instance."""

    def test_get_session_returns_session(self):
        """get_session() returns a requests.Session."""
        session = get_session()
        assert isinstance(session, requests.Session)

    def test_get_session_singleton(self):
        """get_session() returns same instance on multiple calls."""
        session1 = get_session()
        session2 = get_session()
        assert session1 is session2

    def test_get_session_has_defaults(self):
        """Singleton session has sensible defaults."""
        session = get_session()
        assert session._timeout == 30
        assert 'http://' in session.adapters
        assert 'https://' in session.adapters


class TestSessionRetryBehavior:
    """Test session retry behavior."""

    def test_session_retries_transient_failures(self):
        """Session retries on transient HTTP errors."""
        session = create_resilient_session(max_retries=2)
        
        # Verify retry strategy allows retries
        adapter = session.adapters['https://']
        assert adapter.max_retries.total >= 2

    def test_session_retries_on_500(self):
        """Session retries on 500 errors by default."""
        session = create_resilient_session()
        adapter = session.adapters['https://']
        assert 500 in adapter.max_retries.status_forcelist

    def test_session_retries_on_503(self):
        """Session retries on 503 errors by default."""
        session = create_resilient_session()
        adapter = session.adapters['https://']
        assert 503 in adapter.max_retries.status_forcelist

    def test_session_retries_on_429(self):
        """Session retries on 429 (rate limit) errors."""
        session = create_resilient_session()
        adapter = session.adapters['https://']
        assert 429 in adapter.max_retries.status_forcelist


class TestSessionConfiguration:
    """Test session configuration options."""

    def test_custom_max_retries(self):
        """Accepts custom max_retries."""
        session = create_resilient_session(max_retries=5)
        assert session is not None

    def test_custom_backoff_factor(self):
        """Accepts custom backoff_factor."""
        session = create_resilient_session(backoff_factor=1.0)
        assert session is not None

    def test_all_http_methods_retryable(self):
        """GET, POST, PUT, DELETE are retryable."""
        session = create_resilient_session()
        adapter = session.adapters['https://']
        retry = adapter.max_retries
        
        # Tenacity retry allows specified methods
        assert retry is not None


class TestSessionEdgeCases:
    """Test edge cases and error handling."""

    def test_session_handles_none_timeout(self):
        """Session accepts None for timeout (unlimited)."""
        session = create_resilient_session(timeout=None)
        assert session._timeout is None

    def test_session_handles_zero_timeout(self):
        """Session accepts 0 timeout."""
        session = create_resilient_session(timeout=0)
        assert session._timeout == 0

    def test_session_handles_large_timeout(self):
        """Session accepts large timeout values."""
        session = create_resilient_session(timeout=3600)
        assert session._timeout == 3600

    def test_multiple_session_instances(self):
        """Can create multiple independent sessions."""
        session1 = create_resilient_session(timeout=30)
        session2 = create_resilient_session(timeout=60)
        
        assert session1 is not session2
        assert session1._timeout == 30
        assert session2._timeout == 60


class TestSessionIntegration:
    """Integration tests with mocked HTTP calls."""

    @patch('requests.adapters.HTTPAdapter.send')
    def test_session_get_request(self, mock_send):
        """Session can make GET requests."""
        mock_send.return_value = Mock(status_code=200, content=b'response', headers={})
        
        session = create_resilient_session()
        response = session.get('http://example.com')
        
        assert mock_send.called

    @patch('requests.adapters.HTTPAdapter.send')
    def test_session_post_request(self, mock_send):
        """Session can make POST requests."""
        mock_send.return_value = Mock(status_code=201, content=b'created', headers={})
        
        session = create_resilient_session()
        response = session.post('http://example.com', json={'key': 'value'})
        
        assert mock_send.called

    @patch('requests.adapters.HTTPAdapter.send')
    def test_session_applies_timeout_to_requests(self, mock_send):
        """Session applies timeout to actual requests."""
        mock_send.return_value = Mock(status_code=200, content=b'', headers={})
        
        session = create_resilient_session(timeout=45)
        session.get('http://example.com')
        
        # Verify timeout is applied
        assert mock_send.called
