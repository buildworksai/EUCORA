# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Remediation Service.

Generates remediation plans for vulnerabilities.
"""
import logging
from typing import Any, Dict, List

from apps.secops_agent.models import Vulnerability, VulnerabilityInstance

logger = logging.getLogger(__name__)


class RemediationService:
    """Service for generating remediation plans."""

    def generate_plan(
        self,
        vulnerability: Vulnerability,
        instances: List[VulnerabilityInstance],
        remediation_type: str = "patch",
    ) -> Dict[str, Any]:
        """
        Generate remediation plan for vulnerability.

        Args:
            vulnerability: Vulnerability instance
            instances: List of affected vulnerability instances
            remediation_type: Type of remediation (patch, config, compensating, upgrade)

        Returns:
            Remediation plan data
        """
        # Determine risk level based on severity
        risk_level = "R1"
        if vulnerability.severity == "critical":
            risk_level = "R3"
        elif vulnerability.severity == "high":
            risk_level = "R2"

        # Generate steps based on remediation type
        steps = self._generate_steps(vulnerability, remediation_type)

        return {
            "name": f"Remediate {vulnerability.cve_id}",
            "vulnerability_id": str(vulnerability.id),
            "remediation_type": remediation_type,
            "description": f"Remediation plan for {vulnerability.cve_id}: {vulnerability.title}",
            "steps": steps,
            "risk_level": risk_level,
            "affected_instance_ids": [str(inst.id) for inst in instances],
        }

    def _generate_steps(self, vulnerability: Vulnerability, remediation_type: str) -> List[Dict[str, Any]]:
        """
        Generate remediation steps.

        Args:
            vulnerability: Vulnerability instance
            remediation_type: Type of remediation

        Returns:
            List of remediation steps
        """
        steps = []

        if remediation_type == "patch":
            steps = [
                {
                    "step_number": 1,
                    "action": "Download patch",
                    "description": f"Download patch for {vulnerability.cve_id}",
                },
                {
                    "step_number": 2,
                    "action": "Test patch",
                    "description": "Test patch in non-production environment",
                },
                {
                    "step_number": 3,
                    "action": "Deploy patch",
                    "description": "Deploy patch to affected systems",
                },
                {
                    "step_number": 4,
                    "action": "Verify remediation",
                    "description": "Verify vulnerability is remediated",
                },
            ]
        elif remediation_type == "config":
            steps = [
                {
                    "step_number": 1,
                    "action": "Review configuration",
                    "description": "Review current configuration settings",
                },
                {
                    "step_number": 2,
                    "action": "Apply configuration change",
                    "description": "Apply recommended configuration change",
                },
                {
                    "step_number": 3,
                    "action": "Verify change",
                    "description": "Verify configuration change is effective",
                },
            ]
        elif remediation_type == "compensating":
            steps = [
                {
                    "step_number": 1,
                    "action": "Implement compensating control",
                    "description": "Implement compensating control measure",
                },
                {
                    "step_number": 2,
                    "action": "Monitor effectiveness",
                    "description": "Monitor compensating control effectiveness",
                },
            ]
        elif remediation_type == "upgrade":
            steps = [
                {
                    "step_number": 1,
                    "action": "Plan upgrade",
                    "description": "Plan application/system upgrade",
                },
                {
                    "step_number": 2,
                    "action": "Test upgrade",
                    "description": "Test upgrade in non-production",
                },
                {
                    "step_number": 3,
                    "action": "Execute upgrade",
                    "description": "Execute upgrade on affected systems",
                },
                {
                    "step_number": 4,
                    "action": "Verify upgrade",
                    "description": "Verify upgrade resolves vulnerability",
                },
            ]

        return steps
