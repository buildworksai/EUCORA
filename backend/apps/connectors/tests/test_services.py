# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for connectors services.
"""
import pytest
from apps.connectors.services import PowerShellConnectorService
from unittest.mock import patch, MagicMock
import subprocess


class TestPowerShellConnectorService:
    """Test PowerShell connector service."""
    
    def setup_method(self):
        """Set up test service."""
        self.service = PowerShellConnectorService(base_path='/app')
    
    @patch('apps.connectors.services.Path.exists')
    @patch('subprocess.run')
    def test_health_check_success(self, mock_run, mock_exists):
        """Test successful health check."""
        # Mock script exists
        mock_exists.return_value = True
        
        # Mock successful PowerShell execution
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"status": "healthy", "version": "1.0.0"}'
        mock_run.return_value = mock_result
        
        result = self.service.health_check('intune')
        
        assert result['status'] == 'healthy'
        assert 'details' in result
    
    @patch('apps.connectors.services.Path.exists')
    @patch('subprocess.run')
    def test_health_check_failure(self, mock_run, mock_exists):
        """Test failed health check."""
        # Mock script exists
        mock_exists.return_value = True
        
        # Mock failed PowerShell execution
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = 'Connection failed'
        mock_run.return_value = mock_result
        
        result = self.service.health_check('intune')
        
        assert result['status'] == 'unhealthy'
        assert 'Connection failed' in result['message']
    
    @patch('apps.connectors.services.Path.exists')
    @patch('subprocess.run')
    def test_health_check_timeout(self, mock_run, mock_exists):
        """Test health check timeout."""
        # Mock script exists
        mock_exists.return_value = True
        
        # Mock timeout
        mock_run.side_effect = subprocess.TimeoutExpired('pwsh', 30)
        
        result = self.service.health_check('intune')
        
        assert result['status'] == 'unhealthy'
        assert 'timed out' in result['message']
    
    def test_health_check_unknown_connector(self):
        """Test health check with unknown connector type."""
        result = self.service.health_check('unknown')
        
        assert result['status'] == 'unhealthy'
        assert 'Unknown connector' in result['message']

    @patch('apps.connectors.services.Path.exists')
    def test_health_check_missing_script(self, mock_exists):
        """Test health check when script does not exist."""
        mock_exists.return_value = False
        result = self.service.health_check('intune')
        assert result['status'] == 'unhealthy'
        assert 'Script not found' in result['message']

    @patch('apps.connectors.services.Path.exists')
    @patch('subprocess.run')
    def test_health_check_invalid_json(self, mock_run, mock_exists):
        """Test health check with non-JSON output."""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'OK'
        mock_run.return_value = mock_result

        result = self.service.health_check('intune')

        assert result['status'] == 'healthy'
        assert result['details'] == {}
    
    @patch('apps.connectors.services.Path.exists')
    @patch('subprocess.run')
    def test_deploy_success(self, mock_run, mock_exists):
        """Test successful deployment."""
        # Mock script exists
        mock_exists.return_value = True
        
        # Mock successful deployment
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = '{"status": "success", "object_id": "12345"}'
        mock_run.return_value = mock_result
        
        result = self.service.deploy('intune', {
            'deployment_intent_id': 'test-id',
            'artifact_path': 'artifacts/test.msi',
            'target_ring': 'LAB',
            'app_name': 'TestApp',
            'version': '1.0.0',
        })
        
        assert result['status'] == 'success'
        assert result['connector_object_id'] == '12345'
    
    @patch('apps.connectors.services.Path.exists')
    @patch('subprocess.run')
    def test_deploy_failure(self, mock_run, mock_exists):
        """Test failed deployment."""
        # Mock script exists
        mock_exists.return_value = True
        
        # Mock failed deployment
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_result.stderr = 'Deployment failed'
        mock_run.return_value = mock_result
        
        result = self.service.deploy('intune', {
            'deployment_intent_id': 'test-id',
            'artifact_path': 'artifacts/test.msi',
            'target_ring': 'LAB',
            'app_name': 'TestApp',
            'version': '1.0.0',
        })
        
        assert result['status'] == 'failed'
        assert 'Deployment failed' in result['message']

    def test_deploy_unknown_connector(self):
        """Test deployment with unknown connector type."""
        result = self.service.deploy('unknown', {
            'deployment_intent_id': 'test-id',
            'artifact_path': 'artifacts/test.msi',
            'target_ring': 'LAB',
            'app_name': 'TestApp',
            'version': '1.0.0',
        })

        assert result['status'] == 'failed'
        assert 'Unknown connector' in result['message']

    @patch('apps.connectors.services.Path.exists')
    def test_deploy_missing_script(self, mock_exists):
        """Test deployment when script does not exist."""
        mock_exists.return_value = False
        result = self.service.deploy('intune', {
            'deployment_intent_id': 'test-id',
            'artifact_path': 'artifacts/test.msi',
            'target_ring': 'LAB',
            'app_name': 'TestApp',
            'version': '1.0.0',
        })
        assert result['status'] == 'failed'
        assert 'Script not found' in result['message']

    @patch('apps.connectors.services.Path.exists')
    @patch('subprocess.run')
    def test_deploy_invalid_json(self, mock_run, mock_exists):
        """Test deployment when PowerShell output is not JSON."""
        mock_exists.return_value = True
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_result.stdout = 'OK'
        mock_run.return_value = mock_result

        result = self.service.deploy('intune', {
            'deployment_intent_id': 'test-id',
            'artifact_path': 'artifacts/test.msi',
            'target_ring': 'LAB',
            'app_name': 'TestApp',
            'version': '1.0.0',
        })

        assert result['status'] == 'success'
        assert result['details'] == {}

    @patch('apps.connectors.services.Path.exists')
    @patch('subprocess.run')
    def test_deploy_timeout(self, mock_run, mock_exists):
        """Test deployment timeout handling."""
        mock_exists.return_value = True
        mock_run.side_effect = subprocess.TimeoutExpired('pwsh', 300)

        result = self.service.deploy('intune', {
            'deployment_intent_id': 'test-id',
            'artifact_path': 'artifacts/test.msi',
            'target_ring': 'LAB',
            'app_name': 'TestApp',
            'version': '1.0.0',
        })

        assert result['status'] == 'failed'
        assert 'timed out' in result['message']

    @patch('apps.connectors.services.Path.exists')
    @patch('subprocess.run')
    def test_deploy_exception(self, mock_run, mock_exists):
        """Test deployment error handling on unexpected exception."""
        mock_exists.return_value = True
        mock_run.side_effect = Exception('boom')

        result = self.service.deploy('intune', {
            'deployment_intent_id': 'test-id',
            'artifact_path': 'artifacts/test.msi',
            'target_ring': 'LAB',
            'app_name': 'TestApp',
            'version': '1.0.0',
        })

        assert result['status'] == 'failed'
        assert 'Deployment error' in result['message']
