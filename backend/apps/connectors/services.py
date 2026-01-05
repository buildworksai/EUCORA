# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
PowerShell connector service for execution plane integration.
"""
import subprocess
import json
import logging
from typing import Dict, Any
from pathlib import Path

logger = logging.getLogger(__name__)


class PowerShellConnectorService:
    """Service for invoking PowerShell connectors."""
    
    # Map connector types to script paths
    CONNECTOR_SCRIPTS = {
        'intune': 'scripts/connectors/Invoke-IntuneConnector.ps1',
        'jamf': 'scripts/connectors/Invoke-JamfConnector.ps1',
        'sccm': 'scripts/connectors/Invoke-SCCMConnector.ps1',
        'landscape': 'scripts/connectors/Invoke-LandscapeConnector.ps1',
        'ansible': 'scripts/connectors/Invoke-AnsibleConnector.ps1',
    }
    
    def __init__(self, base_path: str = '/app'):
        """
        Initialize PowerShell connector service.
        
        Args:
            base_path: Base path for PowerShell scripts (default: /app for Docker)
        """
        self.base_path = Path(base_path)
    
    def health_check(self, connector_type: str) -> Dict[str, Any]:
        """
        Check connector health by invoking PowerShell script.
        
        Args:
            connector_type: Connector type (intune, jamf, sccm, landscape, ansible)
        
        Returns:
            {
                'status': 'healthy' | 'unhealthy',
                'message': str,
                'details': dict
            }
        """
        if connector_type not in self.CONNECTOR_SCRIPTS:
            return {
                'status': 'unhealthy',
                'message': f'Unknown connector type: {connector_type}',
                'details': {}
            }
        
        script_path = self.base_path / self.CONNECTOR_SCRIPTS[connector_type]
        
        if not script_path.exists():
            logger.warning(f'PowerShell script not found: {script_path}')
            return {
                'status': 'unhealthy',
                'message': f'Script not found: {script_path}',
                'details': {'script_path': str(script_path)}
            }
        
        try:
            # Invoke PowerShell script with -Action HealthCheck
            result = subprocess.run(
                ['pwsh', '-File', str(script_path), '-Action', 'HealthCheck'],
                capture_output=True,
                text=True,
                timeout=30,
                check=False,
            )
            
            if result.returncode == 0:
                # Parse JSON output from PowerShell
                try:
                    output = json.loads(result.stdout)
                    return {
                        'status': 'healthy',
                        'message': f'{connector_type.upper()} connector is operational',
                        'details': output
                    }
                except json.JSONDecodeError:
                    return {
                        'status': 'healthy',
                        'message': result.stdout.strip() or f'{connector_type.upper()} connector is operational',
                        'details': {}
                    }
            else:
                logger.error(
                    f'PowerShell health check failed: {result.stderr}',
                    extra={'connector_type': connector_type, 'exit_code': result.returncode}
                )
                return {
                    'status': 'unhealthy',
                    'message': f'Health check failed: {result.stderr.strip()}',
                    'details': {'exit_code': result.returncode}
                }
                
        except subprocess.TimeoutExpired:
            logger.error(f'PowerShell health check timed out for {connector_type}')
            return {
                'status': 'unhealthy',
                'message': 'Health check timed out (30s)',
                'details': {}
            }
        except Exception as e:
            logger.error(f'PowerShell health check error: {e}')
            return {
                'status': 'unhealthy',
                'message': f'Health check error: {str(e)}',
                'details': {}
            }
    
    def deploy(self, connector_type: str, deployment_params: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deploy via PowerShell connector.
        
        Args:
            connector_type: Connector type (intune, jamf, sccm, landscape, ansible)
            deployment_params: Deployment parameters
                {
                    'deployment_intent_id': str,
                    'artifact_path': str,
                    'target_ring': str,
                    'app_name': str,
                    'version': str,
                }
        
        Returns:
            {
                'status': 'success' | 'failed',
                'message': str,
                'connector_object_id': str | None,
                'details': dict
            }
        """
        if connector_type not in self.CONNECTOR_SCRIPTS:
            return {
                'status': 'failed',
                'message': f'Unknown connector type: {connector_type}',
                'connector_object_id': None,
                'details': {}
            }
        
        script_path = self.base_path / self.CONNECTOR_SCRIPTS[connector_type]
        
        if not script_path.exists():
            logger.warning(f'PowerShell script not found: {script_path}')
            return {
                'status': 'failed',
                'message': f'Script not found: {script_path}',
                'connector_object_id': None,
                'details': {'script_path': str(script_path)}
            }
        
        try:
            # Build PowerShell command with parameters
            ps_params = [
                'pwsh', '-File', str(script_path),
                '-Action', 'Deploy',
                '-DeploymentIntentId', deployment_params['deployment_intent_id'],
                '-ArtifactPath', deployment_params['artifact_path'],
                '-TargetRing', deployment_params['target_ring'],
                '-AppName', deployment_params['app_name'],
                '-Version', deployment_params['version'],
            ]
            
            # Invoke PowerShell script
            result = subprocess.run(
                ps_params,
                capture_output=True,
                text=True,
                timeout=300,  # 5 minutes for deployment
                check=False,
            )
            
            if result.returncode == 0:
                # Parse JSON output from PowerShell
                try:
                    output = json.loads(result.stdout)
                    return {
                        'status': 'success',
                        'message': f'Deployment initiated via {connector_type.upper()}',
                        'connector_object_id': output.get('object_id'),
                        'details': output
                    }
                except json.JSONDecodeError:
                    return {
                        'status': 'success',
                        'message': result.stdout.strip() or f'Deployment initiated via {connector_type.upper()}',
                        'connector_object_id': None,
                        'details': {}
                    }
            else:
                logger.error(
                    f'PowerShell deployment failed: {result.stderr}',
                    extra={
                        'connector_type': connector_type,
                        'deployment_intent_id': deployment_params['deployment_intent_id'],
                        'exit_code': result.returncode
                    }
                )
                return {
                    'status': 'failed',
                    'message': f'Deployment failed: {result.stderr.strip()}',
                    'connector_object_id': None,
                    'details': {'exit_code': result.returncode}
                }
                
        except subprocess.TimeoutExpired:
            logger.error(
                f'PowerShell deployment timed out for {connector_type}',
                extra={'deployment_intent_id': deployment_params['deployment_intent_id']}
            )
            return {
                'status': 'failed',
                'message': 'Deployment timed out (5 minutes)',
                'connector_object_id': None,
                'details': {}
            }
        except Exception as e:
            logger.error(f'PowerShell deployment error: {e}')
            return {
                'status': 'failed',
                'message': f'Deployment error: {str(e)}',
                'connector_object_id': None,
                'details': {}
            }


# Singleton instance
_connector_service = None


def get_connector_service() -> PowerShellConnectorService:
    """Get PowerShell connector service singleton instance."""
    global _connector_service
    if _connector_service is None:
        _connector_service = PowerShellConnectorService()
    return _connector_service
