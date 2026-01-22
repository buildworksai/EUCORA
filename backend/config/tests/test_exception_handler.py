# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for error sanitization and exception handling.
"""
import pytest
from django.test import TestCase, RequestFactory
from django.http import Http404
from rest_framework.exceptions import ValidationError, AuthenticationFailed, PermissionDenied
from rest_framework.response import Response
from rest_framework import status
from config.exception_handler import custom_exception_handler


class TestExceptionHandlerSanitization(TestCase):
    """Test DRF exception handler sanitization."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_validation_error_includes_details(self):
        """Validation errors include field details."""
        request = self.factory.post('/')
        request.correlation_id = 'test-123'
        
        exc = ValidationError({'username': 'This field is required.'})
        context = {'request': request, 'view': None}
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, 400)
        self.assertIn('correlation_id', response.data)
        self.assertEqual(response.data['correlation_id'], 'test-123')
    
    def test_server_error_sanitizes_response(self):
        """Server errors (500+) are sanitized."""
        request = self.factory.post('/')
        request.correlation_id = 'test-456'
        
        exc = Exception('Database connection failed: user=postgres password=secret')
        context = {'request': request, 'view': None}
        
        response = custom_exception_handler(exc, context)
        
        # Response should be 500
        self.assertGreaterEqual(response.status_code, 500)
        
        # Should not contain sensitive info
        response_str = str(response.data)
        self.assertNotIn('password', response_str)
        self.assertNotIn('secret', response_str)
        
        # Should include correlation_id
        self.assertEqual(response.data['correlation_id'], 'test-456')
        
        # Should have generic error message
        self.assertIn('error', response.data)
        self.assertIn('Internal server error', response.data['error'])
    
    def test_authentication_error_returns_401(self):
        """Authentication errors return 401."""
        request = self.factory.get('/')
        request.correlation_id = 'test-789'
        
        exc = AuthenticationFailed('Invalid token')
        context = {'request': request, 'view': None}
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, 401)
        self.assertIn('correlation_id', response.data)
    
    def test_permission_error_returns_403(self):
        """Permission errors return 403."""
        request = self.factory.get('/')
        request.correlation_id = 'test-999'
        
        exc = PermissionDenied('You do not have permission')
        context = {'request': request, 'view': None}
        
        response = custom_exception_handler(exc, context)
        
        self.assertEqual(response.status_code, 403)
        self.assertIn('correlation_id', response.data)
    
    def test_unhandled_exception_returns_500(self):
        """Unhandled exceptions return 500 with correlation_id."""
        request = self.factory.post('/')
        request.correlation_id = 'unhandled-123'
        
        exc = TypeError('Unsupported operand type')
        context = {'request': request, 'view': None}
        
        response = custom_exception_handler(exc, context)
        
        self.assertGreaterEqual(response.status_code, 500)
        self.assertEqual(response.data['correlation_id'], 'unhandled-123')
        self.assertIn('error', response.data)


class TestErrorResponseFormat(TestCase):
    """Test error response format and consistency."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_error_response_always_has_correlation_id(self):
        """All error responses include correlation_id."""
        request = self.factory.get('/')
        request.correlation_id = 'consistency-test-123'
        
        errors = [
            ValidationError('Field error'),
            AuthenticationFailed('Auth failed'),
            PermissionDenied('No permission'),
        ]
        
        context = {'request': request, 'view': None}
        
        for exc in errors:
            response = custom_exception_handler(exc, context)
            self.assertIn('correlation_id', response.data)
            self.assertEqual(response.data['correlation_id'], 'consistency-test-123')
    
    def test_error_response_structure(self):
        """Error responses have consistent structure."""
        request = self.factory.post('/')
        request.correlation_id = 'structure-test'
        
        exc = ValidationError('Test error')
        context = {'request': request, 'view': None}
        
        response = custom_exception_handler(exc, context)
        
        # Should have 'error' or 'errors' field
        self.assertTrue(
            'error' in response.data or 'errors' in response.data,
            'Response should have error or errors field'
        )
        
        # Should have correlation_id
        self.assertIn('correlation_id', response.data)


class TestMissingCorrelationId(TestCase):
    """Test handling when correlation_id is missing."""
    
    def setUp(self):
        self.factory = RequestFactory()
    
    def test_handler_works_without_correlation_id(self):
        """Exception handler works if request doesn't have correlation_id."""
        request = self.factory.post('/')
        # Don't set correlation_id
        
        exc = ValidationError('Test error')
        context = {'request': request, 'view': None}
        
        # Should not raise error
        response = custom_exception_handler(exc, context)
        
        # Should still have correlation_id (set to None)
        self.assertIn('correlation_id', response.data)
        self.assertIsNone(response.data['correlation_id'])
    
    def test_handler_works_without_request(self):
        """Exception handler works if request is None."""
        exc = ValidationError('Test error')
        context = {'request': None, 'view': None}
        
        # Should not raise error
        response = custom_exception_handler(exc, context)
        
        # Should have correlation_id set to None
        self.assertIn('correlation_id', response.data)
        self.assertIsNone(response.data['correlation_id'])
