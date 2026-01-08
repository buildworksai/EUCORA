# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Base integration service interface.

All integration services must implement this interface.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional
import logging
import time
from apps.integrations.models import ExternalSystem

logger = logging.getLogger(__name__)


class IntegrationService(ABC):
    """
    Base class for all external system integrations.
    
    Provides common functionality:
    - Authentication handling
    - Rate limiting with exponential backoff
    - Error classification
    - Correlation ID tracking
    """
    
    def __init__(self):
        """Initialize the integration service."""
        self.rate_limit_delay = 1.0  # Base delay in seconds
        self.max_retries = 3
    
    @abstractmethod
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """
        Test API connectivity and credentials.
        
        Args:
            config: Configuration dictionary with API URL, credentials, etc.
        
        Returns:
            Dict with 'status' ('success' or 'failed') and 'message'
        
        Raises:
            Exception: If connection test fails critically
        """
        pass
    
    @abstractmethod
    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """
        Perform full sync from external system.
        
        Args:
            system: ExternalSystem instance to sync from
        
        Returns:
            Dict with:
            - 'fetched': Number of records fetched
            - 'created': Number of records created
            - 'updated': Number of records updated
            - 'failed': Number of records that failed
        
        Raises:
            Exception: If sync fails critically
        """
        pass
    
    @abstractmethod
    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """
        Fetch asset inventory from external system.
        
        Args:
            system: ExternalSystem instance
        
        Returns:
            List of asset dictionaries with standardized fields
        """
        pass
    
    def _authenticate(self, system: ExternalSystem) -> Dict[str, str]:
        """
        Handle authentication based on auth_type.
        
        Args:
            system: ExternalSystem instance
        
        Returns:
            Dict with authentication headers
        
        Raises:
            ValueError: If auth_type is not supported
            Exception: If credential retrieval fails
        """
        # In production, this would retrieve credentials from vault
        # For now, we'll use a placeholder that returns headers structure
        credentials = system.credentials
        
        if system.auth_type == ExternalSystem.AuthType.OAUTH2:
            # OAuth2 flow - would need to handle token refresh
            token = credentials.get('access_token')
            if not token:
                raise ValueError('OAuth2 access_token not found in credentials')
            return {'Authorization': f'Bearer {token}'}
        
        elif system.auth_type == ExternalSystem.AuthType.BASIC:
            # Basic auth
            username = credentials.get('username')
            password = credentials.get('password')
            if not username or not password:
                raise ValueError('Basic auth username/password not found')
            import base64
            auth_string = f'{username}:{password}'
            encoded = base64.b64encode(auth_string.encode()).decode()
            return {'Authorization': f'Basic {encoded}'}
        
        elif system.auth_type == ExternalSystem.AuthType.TOKEN:
            # API token
            token = credentials.get('api_token')
            if not token:
                raise ValueError('API token not found in credentials')
            return {'Authorization': f'Token {token}'}
        
        elif system.auth_type == ExternalSystem.AuthType.CERTIFICATE:
            # Certificate-based auth (would use requests with cert parameter)
            # For headers, we might just return empty and handle in requests
            return {}
        
        else:
            raise ValueError(f'Unsupported auth_type: {system.auth_type}')
    
    def _handle_rate_limit(self, response, retry_count: int = 0) -> None:
        """
        Handle rate limiting with exponential backoff.
        
        Args:
            response: HTTP response object
            retry_count: Current retry attempt number
        """
        if response.status_code == 429:  # Too Many Requests
            retry_after = int(response.headers.get('Retry-After', self.rate_limit_delay * (2 ** retry_count)))
            logger.warning(f'Rate limit exceeded. Waiting {retry_after} seconds...')
            time.sleep(retry_after)
        elif response.status_code == 503:  # Service Unavailable
            # Exponential backoff
            delay = self.rate_limit_delay * (2 ** retry_count)
            logger.warning(f'Service unavailable. Waiting {delay} seconds...')
            time.sleep(delay)
    
    def _classify_error(self, error: Exception) -> str:
        """
        Classify error as transient, permanent, or policy violation.
        
        Args:
            error: Exception that occurred
        
        Returns:
            Error classification: 'transient', 'permanent', or 'policy_violation'
        """
        error_str = str(error).lower()
        
        # Transient errors (retryable)
        transient_indicators = [
            'timeout', 'connection', 'network', 'temporary',
            'rate limit', '429', '503', '502', '504',
            'service unavailable', 'bad gateway', 'gateway timeout'
        ]
        
        # Policy violations (don't retry)
        policy_indicators = [
            'unauthorized', '403', 'forbidden', 'permission',
            'access denied', 'invalid credentials'
        ]
        
        if any(indicator in error_str for indicator in transient_indicators):
            return 'transient'
        elif any(indicator in error_str for indicator in policy_indicators):
            return 'policy_violation'
        else:
            return 'permanent'
    
    def _get_correlation_id(self, system: ExternalSystem) -> str:
        """
        Get correlation ID for audit trail.
        
        Args:
            system: ExternalSystem instance
        
        Returns:
            Correlation ID string
        """
        return str(system.correlation_id)

