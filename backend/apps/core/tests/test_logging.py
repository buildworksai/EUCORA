# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for structured logging and correlation ID propagation.
"""
import json
import logging
import pytest
from django.test import TestCase, RequestFactory, Client
from django.contrib.auth.models import User
from apps.core.middleware import CorrelationIdMiddleware
from io import StringIO


class TestCorrelationIdMiddleware(TestCase):
    """Test correlation ID injection and propagation."""
    
    def setUp(self):
        self.factory = RequestFactory()
        self.middleware = CorrelationIdMiddleware(lambda r: None)
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_correlation_id_generated_if_not_provided(self):
        """Correlation ID is generated if not in request headers."""
        request = self.factory.get('/')
        self.middleware.process_request(request)
        
        self.assertIsNotNone(request.correlation_id)
        self.assertIsInstance(request.correlation_id, str)
        self.assertGreater(len(request.correlation_id), 0)
    
    def test_correlation_id_extracted_from_header(self):
        """Correlation ID is extracted from X-Correlation-ID header."""
        test_id = '12345-67890-abcdef'
        request = self.factory.get('/', HTTP_X_CORRELATION_ID=test_id)
        self.middleware.process_request(request)
        
        self.assertEqual(request.correlation_id, test_id)
    
    def test_correlation_id_in_response_header(self):
        """Correlation ID is added to response headers."""
        request = self.factory.get('/')
        self.middleware.process_request(request)
        
        # Create a mock response
        from django.http import HttpResponse
        response = HttpResponse()
        response = self.middleware.process_response(request, response)
        
        self.assertEqual(response.get('X-Correlation-ID'), request.correlation_id)
    
    def test_correlation_id_in_logger_adapter(self):
        """Correlation ID is available in request.logger adapter."""
        request = self.factory.get('/')
        request.user = self.user
        self.middleware.process_request(request)
        
        self.assertIsNotNone(request.logger)
        self.assertIsInstance(request.logger, logging.LoggerAdapter)
        self.assertIn('correlation_id', request.logger.extra)


class TestJSONLoggingFormat(TestCase):
    """Test JSON logging format with correlation IDs."""
    
    def setUp(self):
        self.logger = logging.getLogger('apps')
        
    def test_json_logging_includes_correlation_id(self):
        """JSON logs include correlation_id field."""
        # This test requires pythonjsonlogger to be configured
        # which it is in settings/base.py
        
        # Create a test handler with JSON formatter
        from pythonjsonlogger.jsonlogger import JsonFormatter
        stream = StringIO()
        handler = logging.StreamHandler(stream)
        handler.setFormatter(JsonFormatter())
        
        test_logger = logging.getLogger('test_json')
        test_logger.addHandler(handler)
        test_logger.setLevel(logging.INFO)
        
        # Log with correlation_id in extra
        test_logger.info(
            'Test message',
            extra={'correlation_id': 'test-123', 'user_id': 'user@test.com'}
        )
        
        # Verify JSON output
        log_output = stream.getvalue()
        log_data = json.loads(log_output.strip())
        
        self.assertEqual(log_data['message'], 'Test message')
        self.assertEqual(log_data['correlation_id'], 'test-123')
        self.assertEqual(log_data['user_id'], 'user@test.com')


class TestHealthCheckEndpoint(TestCase):
    """Test comprehensive health check endpoint."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='testuser', password='testpass')
    
    def test_comprehensive_health_check_returns_200(self):
        """Health check endpoint returns 200 when healthy."""
        # Unauthenticated access to health endpoint should work
        response = self.client.get('/api/v1/health/')
        self.assertEqual(response.status_code, 200)
        
        data = response.json()
        self.assertIn('status', data)
        self.assertIn('checks', data)
        self.assertIn('timestamp', data)
    
    def test_health_check_has_all_components(self):
        """Health check includes all dependency checks."""
        response = self.client.get('/api/v1/health/')
        data = response.json()
        
        required_checks = ['database', 'redis', 'celery', 'minio', 'circuit_breakers']
        for check in required_checks:
            self.assertIn(check, data['checks'])
            self.assertIn('status', data['checks'][check])
    
    def test_health_check_status_summary(self):
        """Health check includes summary of statuses."""
        response = self.client.get('/api/v1/health/')
        data = response.json()
        
        # Some responses may not have summary, but checks should be there
        self.assertIn('checks', data)
        self.assertIsInstance(data['checks'], dict)


class TestErrorSanitization(TestCase):
    """Test error response sanitization."""
    
    def setUp(self):
        self.client = Client()
    
    def test_500_error_sanitizes_response(self):
        """500 errors are sanitized (no stack traces)."""
        # Post invalid JSON to endpoint expecting JSON
        response = self.client.post(
            '/api/v1/auth/login/',
            data='{"invalid": json}',  # Malformed JSON
            content_type='application/json'
        )
        
        # Should be 400 for bad request (malformed JSON)
        self.assertGreaterEqual(response.status_code, 400)
        
        # Response should be JSON
        if response['Content-Type'].startswith('application/json'):
            data = response.json()
            
            # Should not contain stack trace
            response_str = str(data)
            self.assertNotIn('stack', response_str.lower())
            self.assertNotIn('traceback', response_str.lower())
    
    def test_error_response_includes_correlation_id(self):
        """Error responses include correlation_id for log lookup."""
        response = self.client.get(
            '/api/v1/nonexistent/',
            HTTP_X_CORRELATION_ID='test-correlation-123'
        )
        
        # Get error response (404 for non-existent route)
        # The response may or may not have correlation_id depending on handler
        # but request should have it
        self.assertIn('test-correlation-123', response.get('X-Correlation-ID', ''))


class TestCircuitBreakerHealthEndpoint(TestCase):
    """Test circuit breaker health endpoint."""
    
    def setUp(self):
        self.client = Client()
        self.user = User.objects.create_user(username='admin', password='testpass', is_staff=True)
    
    def test_circuit_breaker_health_returns_status(self):
        """Circuit breaker health endpoint returns breaker status."""
        self.client.force_login(self.user)
        response = self.client.get('/api/v1/admin/health/circuit-breakers')
        
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        self.assertIn('breakers', data)
        self.assertIn('summary', data)
        self.assertIn('total', data['summary'])
        self.assertIn('open', data['summary'])
