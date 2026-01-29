# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
ServiceNow ITSM integration service.

Handles Change Request creation, approval tracking, and CAB workflow integration.
"""
import logging
from typing import Any, Dict, List, Optional

import requests

from apps.cab_workflow.models import CABApproval
from apps.integrations.models import ExternalSystem
from apps.integrations.services.base import IntegrationService

logger = logging.getLogger(__name__)


class ServiceNowITSMService(IntegrationService):
    """ServiceNow ITSM integration service."""

    def test_connection(self, config: Dict[str, Any]) -> Dict[str, Any]:
        """Test ServiceNow ITSM API connectivity."""
        api_url = config["api_url"]
        headers = self._get_auth_headers(config)

        # Test endpoint: Get change request table
        test_url = f"{api_url}/api/now/table/change_request"
        params = {"sysparm_limit": 1}

        try:
            response = requests.get(test_url, headers=headers, params=params, timeout=10)
            response.raise_for_status()

            return {
                "status": "success",
                "message": "Connection successful",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"ServiceNow ITSM connection test failed: {e}")
            return {"status": "failed", "message": f"Connection failed: {str(e)}"}

    def sync(self, system: ExternalSystem) -> Dict[str, Any]:
        """
        Sync change requests and approvals from ServiceNow.

        This syncs change request status and approval records.
        """
        # For ITSM, we primarily sync approval status, not create new records
        # The sync is more about updating existing CAB approvals with external CR status
        updated = 0
        failed = 0

        # Get CAB approvals that have external CR IDs
        cab_approvals = CABApproval.objects.filter(external_change_request_id__isnull=False).exclude(
            external_change_request_id=""
        )

        for approval in cab_approvals:
            try:
                cr_status = self.get_change_request_status(system, approval.external_change_request_id)

                # Update approval decision based on CR status
                if cr_status["state"] == "approved":
                    approval.decision = CABApproval.Decision.APPROVED
                elif cr_status["state"] == "rejected":
                    approval.decision = CABApproval.Decision.REJECTED
                elif cr_status["state"] in ["new", "assess", "authorize"]:
                    approval.decision = CABApproval.Decision.PENDING

                approval.save()
                updated += 1

            except Exception as e:
                logger.error(f"Failed to sync CR {approval.external_change_request_id}: {e}")
                failed += 1

        return {
            "fetched": cab_approvals.count(),
            "created": 0,
            "updated": updated,
            "failed": failed,
        }

    def fetch_assets(self, system: ExternalSystem) -> List[Dict[str, Any]]:
        """ITSM services don't fetch assets - this is a no-op."""
        return []

    def create_change_request(
        self, system: ExternalSystem, deployment_intent_id: str, evidence_pack: Dict[str, Any], risk_score: int
    ) -> Dict[str, Any]:
        """
        Create a Change Request in ServiceNow.

        Args:
            system: ExternalSystem instance
            deployment_intent_id: Deployment intent correlation ID
            evidence_pack: Evidence pack data
            risk_score: Calculated risk score

        Returns:
            Dict with 'change_request_id' and 'url'
        """
        api_url = system.api_url
        headers = self._get_auth_headers_from_system(system)

        url = f"{api_url}/api/now/table/change_request"

        # Build CR payload
        payload = {
            "short_description": f'Application Deployment: {evidence_pack.get("app_name", "Unknown")}',
            "description": self._build_cr_description(deployment_intent_id, evidence_pack, risk_score),
            "risk": self._map_risk_score(risk_score),
            "type": "standard",  # or 'normal', 'emergency' based on risk
            "category": "Application Deployment",
            "state": "new",
            "priority": self._map_priority(risk_score),
        }

        # Add custom fields from metadata
        custom_fields = system.metadata.get("custom_fields", {})
        payload.update(custom_fields)

        try:
            response = requests.post(url, headers=headers, json=payload, timeout=30)
            response.raise_for_status()
            data = response.json()

            result = data.get("result", {})
            return {
                "change_request_id": result.get("sys_id"),
                "number": result.get("number"),
                "url": f"{api_url}/nav_to.do?uri=change_request.do?sys_id={result.get('sys_id')}",
                "status": "success",
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to create ServiceNow CR: {e}")
            raise

    def get_change_request_status(self, system: ExternalSystem, change_request_id: str) -> Dict[str, Any]:
        """Get current status of a Change Request."""
        api_url = system.api_url
        headers = self._get_auth_headers_from_system(system)

        url = f"{api_url}/api/now/table/change_request/{change_request_id}"
        params = {"sysparm_fields": "sys_id,number,state,approval,work_start,work_end"}

        try:
            response = requests.get(url, headers=headers, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

            result = data.get("result", {})
            return {
                "sys_id": result.get("sys_id"),
                "number": result.get("number"),
                "state": result.get("state"),
                "approval": result.get("approval"),
                "work_start": result.get("work_start"),
                "work_end": result.get("work_end"),
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to get ServiceNow CR status: {e}")
            raise

    def _get_auth_headers_from_system(self, system: ExternalSystem) -> Dict[str, str]:
        """Get authentication headers from ExternalSystem instance."""
        config = {
            "api_url": system.api_url,
            "auth_type": system.auth_type,
            "credentials": system.credentials,
        }
        return self._get_auth_headers(config)

    def _get_auth_headers(self, config: Dict[str, Any]) -> Dict[str, str]:
        """Get authentication headers from config."""
        credentials = config.get("credentials", {})
        auth_type = config.get("auth_type", "basic")

        if auth_type == "basic":
            username = credentials.get("username")
            password = credentials.get("password")
            import base64

            auth_string = f"{username}:{password}"
            encoded = base64.b64encode(auth_string.encode()).decode()
            return {
                "Authorization": f"Basic {encoded}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        elif auth_type == "oauth2":
            token = credentials.get("access_token")
            return {
                "Authorization": f"Bearer {token}",
                "Content-Type": "application/json",
                "Accept": "application/json",
            }
        else:
            raise ValueError(f"Unsupported auth_type for ServiceNow: {auth_type}")

    def _build_cr_description(self, deployment_intent_id: str, evidence_pack: Dict[str, Any], risk_score: int) -> str:
        """Build Change Request description from evidence pack."""
        description = f"""
Deployment Intent ID: {deployment_intent_id}
Application: {evidence_pack.get('app_name', 'Unknown')}
Version: {evidence_pack.get('version', 'Unknown')}
Risk Score: {risk_score}

Evidence Pack:
- Artifact Hash: {evidence_pack.get('artifact_hash', 'N/A')}
- SBOM Generated: {evidence_pack.get('sbom_generated', False)}
- Vulnerability Scan: {evidence_pack.get('vuln_scan_status', 'N/A')}
- Test Evidence: {evidence_pack.get('test_evidence', 'N/A')}

Rollout Plan:
- Target Ring: {evidence_pack.get('target_ring', 'N/A')}
- Rollback Strategy: {evidence_pack.get('rollback_strategy', 'N/A')}
"""
        return description.strip()

    def _map_risk_score(self, risk_score: int) -> str:
        """Map risk score to ServiceNow risk field."""
        if risk_score >= 75:
            return "high"
        elif risk_score >= 50:
            return "medium"
        else:
            return "low"

    def _map_priority(self, risk_score: int) -> str:
        """Map risk score to ServiceNow priority."""
        if risk_score >= 75:
            return "1"  # Critical
        elif risk_score >= 50:
            return "2"  # High
        elif risk_score >= 25:
            return "3"  # Medium
        else:
            return "4"  # Low
