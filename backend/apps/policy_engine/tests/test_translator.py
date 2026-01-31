# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for PolicyTranslator service.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.application_portfolio.models import Application, Publisher
from apps.policy_engine.models import ApplicationPolicy, PolicySetting
from apps.policy_engine.services.translator import PolicyTranslator

User = get_user_model()


@pytest.mark.django_db
class TestPolicyTranslator:
    """Test PolicyTranslator service."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.publisher = Publisher.objects.create(name="Test Publisher", identifier="test.pub")
        self.application = Application.objects.create(
            name="Test App",
            identifier="com.test.app",
            publisher=self.publisher,
        )
        self.policy = ApplicationPolicy.objects.create(
            name="Test Policy",
            application=self.application,
            platform="windows",
            created_by=self.user,
        )
        self.translator = PolicyTranslator()

    def test_translate_to_intune(self):
        """Test translating policy to Intune configuration."""
        PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.INSTALLATION,
            setting_key="require_admin",
            setting_value=True,
        )
        PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.RESTART,
            setting_key="mode",
            setting_value="prompt",
        )
        PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.UNINSTALL,
            setting_key="mode",
            setting_value="user_allowed",
        )

        mapping = self.translator.translate(self.policy, "intune")

        assert "installExperience" in mapping
        assert mapping["installExperience"]["runAsAccount"] == "system"
        assert mapping["installExperience"]["deviceRestartBehavior"] == "prompt"
        assert mapping["allowAvailableUninstall"] is True

    def test_translate_to_jamf(self):
        """Test translating policy to Jamf configuration."""
        PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.UPDATE,
            setting_key="mode",
            setting_value="auto",
        )
        PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.UNINSTALL,
            setting_key="mode",
            setting_value="disabled",
        )
        PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.RESTART,
            setting_key="mode",
            setting_value="force",
        )

        mapping = self.translator.translate(self.policy, "jamf")

        assert "general" in mapping
        assert mapping["general"]["trigger"] == "recurring"
        assert mapping["package_configuration"]["no_uninstall"] is True
        assert mapping["reboot"]["no_user_logged_in"] is True

    def test_translate_to_sccm(self):
        """Test translating policy to SCCM configuration."""
        PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.INSTALLATION,
            setting_key="require_admin",
            setting_value=True,
        )
        PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.RESTART,
            setting_key="mode",
            setting_value="prompt",
        )

        mapping = self.translator.translate(self.policy, "sccm")

        assert "deployment_type" in mapping
        assert mapping["deployment_type"] == "Required"
        assert "user_experience" in mapping
        assert mapping["user_experience"]["user_notification"] == "DisplayAll"

    def test_translate_unknown_plane(self):
        """Test translating to unknown execution plane."""
        with pytest.raises(ValueError, match="Unknown target plane"):
            self.translator.translate(self.policy, "unknown")

    def test_map_restart_mode(self):
        """Test restart mode mapping."""
        assert self.translator._map_restart_mode("none") == "none"
        assert self.translator._map_restart_mode("prompt") == "prompt"
        assert self.translator._map_restart_mode("defer") == "allow"
        assert self.translator._map_restart_mode("force") == "force"
        assert self.translator._map_restart_mode("unknown") == "none"
