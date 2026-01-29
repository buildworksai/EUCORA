# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Phase P5.5: Blast Radius Classification Service

Classifies deployments by potential impact scope:
- CRITICAL_INFRASTRUCTURE: Never auto-approve
- BUSINESS_CRITICAL: Strict approval gates
- PRODUCTIVITY_TOOLS: Moderate gates
- NON_CRITICAL: Liberal gates

Future: CMDB integration for automatic classification
Current: Manual classification with validation rules

Implementation Date: 2026-01-23
"""
import logging
from typing import Any, Dict, Optional

from django.utils import timezone

from apps.evidence_store.models_p5_5 import BlastRadiusClass

logger = logging.getLogger(__name__)


class BlastRadiusClassifier:
    """
    Classify deployments by blast radius (impact scope).

    Phase 1 (Greenfield): Manual classification with validation
    Phase 2 (CMDB Integration): Automatic classification from CMDB attributes

    Classification factors:
    - Application category (from metadata or CMDB)
    - Privilege level (admin/system/user)
    - User count (enterprise-wide vs department vs team)
    - Business criticality tier (from CMDB)
    - Service tier (Tier 0/1/2/3 from AD schema)
    """

    # Classification rules (can be overridden by CMDB)
    CLASSIFICATION_RULES = {
        "CRITICAL_INFRASTRUCTURE": {
            "keywords": [
                "security",
                "antivirus",
                "firewall",
                "vpn",
                "active directory",
                "domain controller",
                "pki",
                "certificate",
                "encryption",
                "authentication",
                "os patch",
                "windows update",
                "kernel",
            ],
            "privilege_required": ["admin", "system", "kernel"],
            "business_criticality_min": "HIGH",
            "description": "Security tools, OS components, identity/auth systems",
        },
        "BUSINESS_CRITICAL": {
            "keywords": [
                "erp",
                "crm",
                "financial",
                "trading",
                "billing",
                "payroll",
                "salesforce",
                "sap",
                "oracle",
                "dynamics",
                "customer-facing",
                "revenue",
                "compliance",
            ],
            "user_count_min": 1000,
            "business_criticality_min": "HIGH",
            "description": "ERP, financial systems, customer-facing applications",
        },
        "PRODUCTIVITY_TOOLS": {
            "keywords": [
                "office",
                "microsoft 365",
                "slack",
                "zoom",
                "teams",
                "outlook",
                "chrome",
                "firefox",
                "adobe",
                "pdf",
                "editor",
                "collaboration",
                "communication",
            ],
            "user_count_min": 100,
            "description": "Office productivity, collaboration tools",
        },
        "NON_CRITICAL": {
            "keywords": [
                "utility",
                "game",
                "wallpaper",
                "screensaver",
                "calculator",
                "notepad",
                "optional",
                "personal",
            ],
            "description": "Optional utilities, personal productivity",
        },
    }

    def classify_deployment(
        self,
        app_name: str,
        app_category: Optional[str] = None,
        requires_admin: bool = False,
        target_user_count: Optional[int] = None,
        business_criticality: Optional[str] = None,
        cmdb_data: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Classify deployment by blast radius.

        Args:
            app_name: Application name
            app_category: Category from metadata (optional)
            requires_admin: Whether admin privileges required
            target_user_count: Number of users targeted
            business_criticality: Business criticality tier (HIGH/MEDIUM/LOW)
            cmdb_data: CMDB attributes (future integration)

        Returns:
            str: Blast radius class (CRITICAL_INFRASTRUCTURE, BUSINESS_CRITICAL, etc.)
        """
        # Priority 1: CMDB classification (if available)
        if cmdb_data:
            cmdb_class = self._classify_from_cmdb(cmdb_data)
            if cmdb_class:
                logger.info(f"Classified {app_name} as {cmdb_class} (from CMDB)")
                return cmdb_class

        # Priority 2: Rule-based classification
        app_name_lower = app_name.lower()
        app_category_lower = (app_category or "").lower()

        # Check for CRITICAL_INFRASTRUCTURE
        if self._matches_critical_infrastructure(app_name_lower, app_category_lower, requires_admin):
            logger.info(f"Classified {app_name} as CRITICAL_INFRASTRUCTURE")
            return "CRITICAL_INFRASTRUCTURE"

        # Check for BUSINESS_CRITICAL
        if self._matches_business_critical(app_name_lower, app_category_lower, business_criticality, target_user_count):
            logger.info(f"Classified {app_name} as BUSINESS_CRITICAL")
            return "BUSINESS_CRITICAL"

        # Check for PRODUCTIVITY_TOOLS
        if self._matches_productivity_tools(app_name_lower, app_category_lower, target_user_count):
            logger.info(f"Classified {app_name} as PRODUCTIVITY_TOOLS")
            return "PRODUCTIVITY_TOOLS"

        # Default: NON_CRITICAL
        logger.info(f"Classified {app_name} as NON_CRITICAL (default)")
        return "NON_CRITICAL"

    def _classify_from_cmdb(self, cmdb_data: Dict[str, Any]) -> Optional[str]:
        """
        Classify from CMDB attributes (future implementation).

        Expected CMDB fields:
        - business_criticality: HIGH/MEDIUM/LOW
        - service_tier: Tier0/Tier1/Tier2/Tier3
        - regulatory_scope: PCI/HIPAA/SOX/etc.
        - impact_scope: ENTERPRISE/DEPARTMENT/TEAM
        - rto_minutes: Recovery Time Objective
        """
        # Placeholder for CMDB integration
        # TODO: Implement CMDB API integration in Phase P6

        service_tier = cmdb_data.get("service_tier", "").upper()
        if service_tier in ["TIER0", "TIER1"]:
            return "CRITICAL_INFRASTRUCTURE"

        business_criticality = cmdb_data.get("business_criticality", "").upper()
        impact_scope = cmdb_data.get("impact_scope", "").upper()

        if business_criticality == "HIGH" and impact_scope == "ENTERPRISE":
            return "BUSINESS_CRITICAL"

        if impact_scope in ["DEPARTMENT", "TEAM"]:
            return "PRODUCTIVITY_TOOLS"

        return None  # Fall back to rule-based classification

    def _matches_critical_infrastructure(self, app_name: str, app_category: str, requires_admin: bool) -> bool:
        """Check if deployment matches critical infrastructure criteria."""
        rules = self.CLASSIFICATION_RULES["CRITICAL_INFRASTRUCTURE"]

        # Keyword match
        for keyword in rules["keywords"]:
            if keyword in app_name or keyword in app_category:
                return True

        # Privilege escalation + security/OS/system category
        if requires_admin and ("security" in app_category or "os" in app_category or "system" in app_category):
            return True

        return False

    def _matches_business_critical(
        self, app_name: str, app_category: str, business_criticality: Optional[str], target_user_count: Optional[int]
    ) -> bool:
        """Check if deployment matches business critical criteria."""
        rules = self.CLASSIFICATION_RULES["BUSINESS_CRITICAL"]

        # Explicit business criticality = HIGH
        if business_criticality and business_criticality.upper() == "HIGH":
            return True

        # Enterprise-wide deployments (>10k users) are business critical
        if target_user_count and target_user_count >= 10000:
            return True

        # Keyword match + large user base
        for keyword in rules["keywords"]:
            if keyword in app_name or keyword in app_category:
                if target_user_count and target_user_count >= rules["user_count_min"]:
                    return True
                # Keyword match alone (without user count) suggests business critical
                if keyword in [
                    "erp",
                    "crm",
                    "financial",
                    "trading",
                    "billing",
                    "sap",
                    "oracle",
                    "salesforce",
                    "dynamics",
                ]:
                    return True

        return False

    def _matches_productivity_tools(self, app_name: str, app_category: str, target_user_count: Optional[int]) -> bool:
        """Check if deployment matches productivity tools criteria."""
        rules = self.CLASSIFICATION_RULES["PRODUCTIVITY_TOOLS"]

        # Exclude apps that are clearly non-critical ONLY if low/no user count
        # (High user count elevates even NON_CRITICAL apps to PRODUCTIVITY_TOOLS)
        if target_user_count is None or target_user_count < rules["user_count_min"]:
            non_critical_keywords = self.CLASSIFICATION_RULES["NON_CRITICAL"]["keywords"]
            for keyword in non_critical_keywords:
                if keyword in app_name or keyword in app_category:
                    return False  # More specific match, skip productivity tools

        # Keyword match
        for keyword in rules["keywords"]:
            if keyword in app_name or keyword in app_category:
                return True

        # Category-based
        if app_category in ["productivity", "collaboration", "communication"]:
            return True

        # Large user count alone can elevate to productivity tools
        if target_user_count and target_user_count >= rules["user_count_min"]:
            return True

        return False

    def get_classification_details(self, blast_radius_class: str) -> Dict[str, Any]:
        """
        Get detailed information about a blast radius class.

        Returns CAB requirements, auto-approve policies, examples.
        """
        try:
            br_class = BlastRadiusClass.objects.get(name=blast_radius_class)
            return {
                "name": br_class.name,
                "description": br_class.description,
                "cab_quorum_required": br_class.cab_quorum_required,
                "auto_approve_allowed": br_class.auto_approve_allowed,
                "business_criticality": br_class.business_criticality,
                "user_impact_max": br_class.user_impact_max,
                "examples": br_class.example_applications,
            }
        except BlastRadiusClass.DoesNotExist:
            return {
                "name": blast_radius_class,
                "description": "Classification details not configured",
                "cab_quorum_required": 1,
                "auto_approve_allowed": False,
            }

    def validate_manual_classification(self, app_name: str, proposed_class: str, justification: str) -> Dict[str, Any]:
        """
        Validate manual blast radius classification.

        Requires justification if classification seems incorrect.
        """
        auto_class = self.classify_deployment(app_name=app_name)

        if auto_class == proposed_class:
            return {
                "valid": True,
                "auto_classification": auto_class,
                "proposed_classification": proposed_class,
                "requires_justification": False,
            }

        # Classification override detected
        # Allow, but require justification and log for audit
        logger.warning(
            f"Manual classification override for {app_name}: "
            f"Auto={auto_class}, Proposed={proposed_class}, "
            f"Justification: {justification}"
        )

        return {
            "valid": bool(justification),  # Require non-empty justification
            "auto_classification": auto_class,
            "proposed_classification": proposed_class,
            "requires_justification": True,
            "justification": justification,
            "warning": (f"Manual override detected. Automatic classification suggested: {auto_class}"),
        }
