# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Pre-configured policy templates.

These templates provide common deployment policy configurations for different
application types and use cases.
"""

POLICY_TEMPLATES = {
    "enterprise_required": {
        "name": "Enterprise Required",
        "description": "Mandatory enterprise application with strict controls",
        "template_type": "enterprise",
        "settings": {
            "installation": {
                "require_admin": True,
                "silent_install": True,
                "block_manual": True,
            },
            "uninstall": {
                "mode": "disabled",
            },
            "update": {
                "mode": "auto",
                "notify_user": False,
            },
            "configuration": {
                "enforce": True,
                "detect_drift": True,
                "remediate_drift": True,
            },
            "restart": {
                "mode": "prompt",
                "deferral_hours": 4,
            },
            "compliance": {
                "required_for_compliance": True,
                "conditional_access": True,
            },
        },
    },
    "security_critical": {
        "name": "Security-Critical",
        "description": "Security tools that must always be present and running",
        "template_type": "security",
        "settings": {
            "installation": {
                "require_admin": True,
                "silent_install": True,
                "block_manual": True,
            },
            "uninstall": {
                "mode": "disabled",
            },
            "update": {
                "mode": "auto",
                "force_update": True,
            },
            "configuration": {
                "enforce": True,
                "remediate_drift": True,
            },
            "restart": {
                "mode": "force",
                "grace_period_minutes": 15,
            },
            "compliance": {
                "required_for_compliance": True,
                "conditional_access": True,
                "block_on_failure": True,
            },
        },
    },
    "self_service": {
        "name": "Self-Service Optional",
        "description": "Optional application available in company portal",
        "template_type": "optional",
        "settings": {
            "installation": {
                "require_admin": False,
                "silent_install": True,
                "allow_manual": True,
            },
            "uninstall": {
                "mode": "user_allowed",
            },
            "update": {
                "mode": "notify",
            },
            "configuration": {
                "enforce": False,
                "allow_user_config": True,
            },
            "restart": {
                "mode": "none",
            },
            "compliance": {
                "required_for_compliance": False,
            },
        },
    },
    "productivity": {
        "name": "Productivity Suite",
        "description": "Office applications with managed updates",
        "template_type": "productivity",
        "settings": {
            "installation": {
                "require_admin": True,
                "silent_install": True,
                "block_manual": False,
            },
            "uninstall": {
                "mode": "admin_only",
            },
            "update": {
                "mode": "auto",
                "notify_user": True,
            },
            "configuration": {
                "enforce": True,
                "detect_drift": True,
            },
            "restart": {
                "mode": "defer",
                "deferral_hours": 8,
            },
            "compliance": {
                "required_for_compliance": True,
            },
        },
    },
    "browser": {
        "name": "Web Browser",
        "description": "Browser with extension management",
        "template_type": "browser",
        "settings": {
            "installation": {
                "require_admin": True,
                "silent_install": True,
                "block_manual": True,
            },
            "uninstall": {
                "mode": "admin_only",
            },
            "update": {
                "mode": "auto",
                "force_update": True,
            },
            "configuration": {
                "enforce": True,
                "remediate_drift": True,
            },
            "restart": {
                "mode": "prompt",
                "deferral_hours": 2,
            },
            "compliance": {
                "required_for_compliance": False,
            },
        },
    },
    "development": {
        "name": "Development Tool",
        "description": "Development tools with flexible configuration",
        "template_type": "development",
        "settings": {
            "installation": {
                "require_admin": False,
                "silent_install": False,
                "allow_manual": True,
            },
            "uninstall": {
                "mode": "user_allowed",
            },
            "update": {
                "mode": "notify",
            },
            "configuration": {
                "enforce": False,
                "allow_user_config": True,
            },
            "restart": {
                "mode": "none",
            },
            "compliance": {
                "required_for_compliance": False,
            },
        },
    },
}


def seed_policy_templates():
    """
    Seed policy templates into the database.

    Creates system templates if they don't exist.
    """
    from .models import PolicyTemplate

    created_count = 0
    for template_id, template_data in POLICY_TEMPLATES.items():
        template, created = PolicyTemplate.objects.get_or_create(
            name=template_data["name"],
            defaults={
                "template_type": template_data["template_type"],
                "description": template_data["description"],
                "settings": template_data["settings"],
                "is_system": True,
                "platform": "",  # All platforms
            },
        )
        if created:
            created_count += 1
            print(f"Created policy template: {template.name}")
        else:
            # Update existing template settings
            template.settings = template_data["settings"]
            template.save(update_fields=["settings"])

    print(f"Seeded {created_count} new policy templates")
    return created_count
