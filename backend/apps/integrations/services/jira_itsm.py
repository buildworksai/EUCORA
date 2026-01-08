# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Jira Service Management integration service.

Handles Change Request creation and approval tracking via Jira issues.
"""
import requests
import logging
from typing import Dict, List, Any
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService
from apps.cab_workflow.models import CABApproval

logger = logging.getLogger(__name__)


class JiraServiceManagementService(IntegrationService):
    """Jira Service Management integration service."""
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Jira Service Management API connectivity."""
        api_url = config['api_url']
        headers = self._get_auth_headers(config)
        
        # Test endpoint: Get current user
        test_url = f"{api_url}/rest/api/3/myself"
        
        try:
            response = requests.get(test_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            return {
                'status': 'success',
                'message': 'Connection successful',
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Jira Service Management connection test failed: {e}')
            return {
                'status': 'failed',
                'message': f'Connection failed: {str(e)}'
            }
    
    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Sync change request status from Jira."""
        updated = 0
        failed = 0
        
        # Get CAB approvals with Jira issue keys
        cab_approvals = CABApproval.objects.filter(
            external_change_request_id__isnull=False
        ).exclude(external_change_request_id='')
        
        for approval in cab_approvals:
            try:
                issue_status = self.get_issue_status(system, approval.external_change_request_id)
                
                # Map Jira status to CAB approval decision
                jira_status = issue_status.get('status', {}).get('name', '').lower()
                if 'approved' in jira_status or 'done' in jira_status:
                    approval.decision = CABApproval.Decision.APPROVED
                elif 'rejected' in jira_status or 'cancelled' in jira_status:
                    approval.decision = CABApproval.Decision.REJECTED
                else:
                    approval.decision = CABApproval.Decision.PENDING
                
                approval.save()
                updated += 1
                
            except Exception as e:
                logger.error(f'Failed to sync Jira issue {approval.external_change_request_id}: {e}')
                failed += 1
        
        return {
            'fetched': cab_approvals.count(),
            'created': 0,
            'updated': updated,
            'failed': failed,
        }
    
    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """ITSM services don't fetch assets."""
        return []
    
    def create_change_request(
        self,
        system: ExternalSystem,
        deployment_intent_id: str,
        evidence_pack: Dict[str, Any],
        risk_score: int
    ) -> Dict[str, Any]:
        """Create a Change Request issue in Jira."""
        api_url = system.api_url
        headers = self._get_auth_headers_from_system(system)
        
        # Get project key and issue type from metadata
        project_key = system.metadata.get('project_key')
        issue_type = system.metadata.get('issue_type', 'Change')
        
        if not project_key:
            raise ValueError('Jira project_key not configured in metadata')
        
        url = f"{api_url}/rest/api/3/issue"
        
        # Build issue payload
        payload = {
            'fields': {
                'project': {'key': project_key},
                'summary': f'Application Deployment: {evidence_pack.get("app_name", "Unknown")}',
                'description': {
                    'type': 'doc',
                    'version': 1,
                    'content': [
                        {
                            'type': 'paragraph',
                            'content': [
                                {'type': 'text', 'text': self._build_issue_description(deployment_intent_id, evidence_pack, risk_score)}
                            ]
                        }
                    ]
                },
                'issuetype': {'name': issue_type},
                'priority': {'name': self._map_priority(risk_score)},
                'labels': ['deployment', 'automated'],
            }
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            issue_key = data.get('key')
            return {
                'change_request_id': issue_key,
                'number': issue_key,
                'url': f"{api_url}/browse/{issue_key}",
                'status': 'success',
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to create Jira issue: {e}')
            raise
    
    def get_issue_status(
        self,
        system: ExternalSystem,
        issue_key: str
    ) -> Dict[str, Any]:
        """Get current status of a Jira issue."""
        api_url = system.api_url
        headers = self._get_auth_headers_from_system(system)
        
        url = f"{api_url}/rest/api/3/issue/{issue_key}"
        params = {'fields': 'status,priority,assignee'}
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            return {
                'key': data.get('key'),
                'status': data.get('fields', {}).get('status', {}),
                'priority': data.get('fields', {}).get('priority', {}),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to get Jira issue status: {e}')
            raise
    
    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            'api_url': system.api_url,
            'auth_type': system.auth_type,
            'credentials': system.credentials,
        }
        return self._get_auth_headers(config)
    
    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers from config."""
        credentials = config.get('credentials', {})
        auth_type = config.get('auth_type', 'basic')
        
        if auth_type == 'basic':
            username = credentials.get('username')
            password = credentials.get('password')
            import base64
            auth_string = f'{username}:{password}'
            encoded = base64.b64encode(auth_string.encode()).decode()
            return {
                'Authorization': f'Basic {encoded}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        elif auth_type == 'token':
            token = credentials.get('api_token')
            return {
                'Authorization': f'Bearer {token}',
                'Content-Type': 'application/json',
                'Accept': 'application/json',
            }
        else:
            raise ValueError(f'Unsupported auth_type for Jira: {auth_type}')
    
    def _build_issue_description(
        self,
        deployment_intent_id: str,
        evidence_pack: Dict[str, Any],
        risk_score: int
    ) -> str:
        """Build Jira issue description."""
        return f"""
Deployment Intent ID: {deployment_intent_id}
Application: {evidence_pack.get('app_name', 'Unknown')}
Version: {evidence_pack.get('version', 'Unknown')}
Risk Score: {risk_score}

Evidence Pack:
- Artifact Hash: {evidence_pack.get('artifact_hash', 'N/A')}
- SBOM Generated: {evidence_pack.get('sbom_generated', False)}
- Vulnerability Scan: {evidence_pack.get('vuln_scan_status', 'N/A')}

Rollout Plan:
- Target Ring: {evidence_pack.get('target_ring', 'N/A')}
- Rollback Strategy: {evidence_pack.get('rollback_strategy', 'N/A')}
""".strip()
    
    def _map_priority(self, risk_score: int) -> str:
        """Map risk score to Jira priority."""
        if risk_score >= 75:
            return 'Highest'
        elif risk_score >= 50:
            return 'High'
        elif risk_score >= 25:
            return 'Medium'
        else:
            return 'Low'

