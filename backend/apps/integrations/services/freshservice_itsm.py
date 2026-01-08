# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Freshservice ITSM integration service.

Handles Change Request creation and approval tracking.
"""
import requests
import logging
from typing import Dict, List, Any
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService
from apps.cab_workflow.models import CABApproval

logger = logging.getLogger(__name__)


class FreshserviceITSMService(IntegrationService):
    """Freshservice ITSM integration service."""
    
    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test Freshservice ITSM API connectivity."""
        api_url = config['api_url']
        headers = self._get_auth_headers(config)
        
        # Test endpoint: Get changes
        test_url = f"{api_url}/api/v2/changes"
        params = {'per_page': 1}
        
        try:
            response = requests.get(test_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()
            
            return {
                'status': 'success',
                'message': 'Connection successful',
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Freshservice ITSM connection test failed: {e}')
            return {
                'status': 'failed',
                'message': f'Connection failed: {str(e)}'
            }
    
    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """Sync change request status from Freshservice."""
        updated = 0
        failed = 0
        
        # Get CAB approvals with Freshservice change IDs
        cab_approvals = CABApproval.objects.filter(
            external_change_request_id__isnull=False
        ).exclude(external_change_request_id='')
        
        for approval in cab_approvals:
            try:
                change_status = self.get_change_status(system, approval.external_change_request_id)
                
                # Map Freshservice status to CAB approval decision
                status = change_status.get('status', 0)
                if status == 5:  # Implemented/Approved
                    approval.decision = CABApproval.Decision.APPROVED
                elif status == 6:  # Rejected
                    approval.decision = CABApproval.Decision.REJECTED
                else:
                    approval.decision = CABApproval.Decision.PENDING
                
                approval.save()
                updated += 1
                
            except Exception as e:
                logger.error(f'Failed to sync Freshservice change {approval.external_change_request_id}: {e}')
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
        """Create a Change Request in Freshservice."""
        api_url = system.api_url
        headers = self._get_auth_headers_from_system(system)
        
        url = f"{api_url}/api/v2/changes"
        
        # Build change payload
        payload = {
            'subject': f'Application Deployment: {evidence_pack.get("app_name", "Unknown")}',
            'description': self._build_change_description(deployment_intent_id, evidence_pack, risk_score),
            'priority': self._map_priority(risk_score),
            'risk': self._map_risk(risk_score),
            'change_type': 1,  # Minor (adjust based on risk)
            'status': 1,  # Open
            'category': 'Application Deployment',
        }
        
        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            change = data.get('change', {})
            return {
                'change_request_id': str(change.get('id')),
                'number': change.get('display_id'),
                'url': f"{api_url}/changes/{change.get('id')}",
                'status': 'success',
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to create Freshservice change: {e}')
            raise
    
    def get_change_status(
        self,
        system: ExternalSystem,
        change_id: str
    ) -> Dict[str, Any]:
        """Get current status of a Freshservice change."""
        api_url = system.api_url
        headers = self._get_auth_headers_from_system(system)
        
        url = f"{api_url}/api/v2/changes/{change_id}"
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            change = data.get('change', {})
            return {
                'id': change.get('id'),
                'display_id': change.get('display_id'),
                'status': change.get('status'),
                'priority': change.get('priority'),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f'Failed to get Freshservice change status: {e}')
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
        api_key = credentials.get('api_key')
        
        if not api_key:
            raise ValueError('Freshservice API key not found in credentials')
        
        return {
            'Authorization': f'Basic {api_key}:X',
            'Content-Type': 'application/json',
        }
    
    def _build_change_description(
        self,
        deployment_intent_id: str,
        evidence_pack: Dict[str, Any],
        risk_score: int
    ) -> str:
        """Build Freshservice change description."""
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
    
    def _map_priority(self, risk_score: int) -> int:
        """Map risk score to Freshservice priority (1-4)."""
        if risk_score >= 75:
            return 4  # Urgent
        elif risk_score >= 50:
            return 3  # High
        elif risk_score >= 25:
            return 2  # Medium
        else:
            return 1  # Low
    
    def _map_risk(self, risk_score: int) -> int:
        """Map risk score to Freshservice risk (1-5)."""
        if risk_score >= 75:
            return 5  # Very High
        elif risk_score >= 50:
            return 4  # High
        elif risk_score >= 25:
            return 3  # Medium
        else:
            return 2  # Low

