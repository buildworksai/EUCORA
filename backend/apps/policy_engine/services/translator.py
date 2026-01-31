# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Translator service.

Translates application policies to execution plane configurations (Intune, Jamf, SCCM).
"""
import logging
from typing import Dict

from ..models import ApplicationPolicy

logger = logging.getLogger(__name__)


class PolicyTranslator:
    """Translate application policies to execution plane configurations."""

    def translate(self, policy: ApplicationPolicy, target_plane: str) -> Dict:
        """
        Translate policy to target execution plane configuration.

        Args:
            policy: ApplicationPolicy instance
            target_plane: Target execution plane ("intune", "jamf", "sccm")

        Returns:
            Dictionary with execution plane-specific configuration

        Raises:
            ValueError: If target_plane is unknown
        """
        if target_plane == "intune":
            return self._translate_to_intune(policy)
        elif target_plane == "jamf":
            return self._translate_to_jamf(policy)
        elif target_plane == "sccm":
            return self._translate_to_sccm(policy)
        else:
            raise ValueError(f"Unknown target plane: {target_plane}")

    def _translate_to_intune(self, policy: ApplicationPolicy) -> Dict:
        """Translate to Intune Win32 app configuration."""
        settings = policy.get_settings_dict()

        config = {
            "installExperience": {
                "runAsAccount": ("system" if settings.get("installation", {}).get("require_admin", False) else "user"),
                "deviceRestartBehavior": self._map_restart_mode(settings.get("restart", {}).get("mode", "none")),
            },
            "allowAvailableUninstall": (settings.get("uninstall", {}).get("mode", "user_allowed") == "user_allowed"),
            "supersedence": {
                "enabled": settings.get("update", {}).get("mode", "auto") == "auto",
            },
        }

        # Installation settings
        install_settings = settings.get("installation", {})
        if install_settings.get("silent_install", False):
            config["installExperience"]["installExperienceType"] = "noDisplay"

        # Compliance integration
        compliance_settings = settings.get("compliance", {})
        if compliance_settings.get("required_for_compliance", False):
            config["requirementRules"] = [
                {
                    "type": "registry",
                    "operator": "exists",
                    "path": "HKEY_LOCAL_MACHINE\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall",
                }
            ]

        # Configuration enforcement
        config_settings = settings.get("configuration", {})
        if config_settings.get("enforce", False):
            config["detectionRules"] = [
                {
                    "type": "file",
                    "path": "%ProgramFiles%",
                    "operator": "exists",
                }
            ]

        return config

    def _translate_to_jamf(self, policy: ApplicationPolicy) -> Dict:
        """Translate to Jamf Pro policy configuration."""
        settings = policy.get_settings_dict()

        return {
            "general": {
                "enabled": True,
                "trigger": ("recurring" if settings.get("update", {}).get("mode", "auto") == "auto" else "manual"),
            },
            "scope": {
                "all_computers": False,
            },
            "self_service": {
                "use_for_self_service": settings.get("installation", {}).get("allow_manual", True),
            },
            "package_configuration": {
                "no_uninstall": settings.get("uninstall", {}).get("mode", "disabled") == "disabled",
            },
            "reboot": {
                "message_enabled": settings.get("restart", {}).get("mode", "prompt") == "prompt",
                "no_user_logged_in": settings.get("restart", {}).get("mode", "force") == "force",
            },
        }

    def _translate_to_sccm(self, policy: ApplicationPolicy) -> Dict:
        """Translate to SCCM application configuration."""
        settings = policy.get_settings_dict()

        return {
            "deployment_type": (
                "Required" if settings.get("installation", {}).get("require_admin", False) else "Available"
            ),
            "user_experience": {
                "user_notification": (
                    "DisplayAll" if settings.get("restart", {}).get("mode", "prompt") == "prompt" else "HideAll"
                ),
                "allow_users_to_view_and_interact_with_the_program_installation": (
                    settings.get("installation", {}).get("allow_manual", True)
                ),
            },
            "deployment_settings": {
                "allow_uninstall": (settings.get("uninstall", {}).get("mode", "user_allowed") != "disabled"),
            },
            "scheduling": {
                "auto_update": settings.get("update", {}).get("mode", "auto") == "auto",
            },
        }

    def _map_restart_mode(self, mode: str) -> str:
        """Map restart mode to Intune deviceRestartBehavior."""
        mapping = {
            "none": "none",
            "prompt": "prompt",
            "defer": "allow",
            "force": "force",
        }
        return mapping.get(mode, "none")
