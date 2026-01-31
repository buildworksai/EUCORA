# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Tests for ApplicationPolicy, PolicySetting, and PolicyTemplate models.
"""
import pytest
from django.contrib.auth import get_user_model

from apps.application_portfolio.models import Application, ApplicationVersion, Publisher
from apps.policy_engine.models import ApplicationPolicy, PolicySetting, PolicyTemplate

User = get_user_model()


@pytest.mark.django_db
class TestApplicationPolicy:
    """Test ApplicationPolicy model."""

    def setup_method(self):
        """Set up test data."""
        self.user = User.objects.create_user(username="testuser", email="test@example.com")
        self.publisher = Publisher.objects.create(name="Test Publisher", identifier="test.pub")
        self.application = Application.objects.create(
            name="Test App",
            identifier="com.test.app",
            publisher=self.publisher,
        )
        self.version = ApplicationVersion.objects.create(application=self.application, version="1.0.0", is_latest=True)

    def test_create_application_policy(self):
        """Test creating an application policy."""
        policy = ApplicationPolicy.objects.create(
            name="Test Policy",
            description="Test description",
            application=self.application,
            platform="windows",
            is_active=True,
            created_by=self.user,
        )
        assert policy.name == "Test Policy"
        assert policy.application == self.application
        assert policy.platform == "windows"
        assert policy.is_active is True
        assert policy.correlation_id is not None

    def test_create_policy_with_version(self):
        """Test creating a policy for a specific version."""
        policy = ApplicationPolicy.objects.create(
            name="Version Policy",
            application=self.application,
            application_version=self.version,
            platform="macos",
            created_by=self.user,
        )
        assert policy.application_version == self.version

    def test_get_settings_dict(self):
        """Test getting settings as dictionary."""
        policy = ApplicationPolicy.objects.create(
            name="Test Policy",
            application=self.application,
            platform="windows",
            created_by=self.user,
        )
        PolicySetting.objects.create(
            policy=policy,
            category=PolicySetting.SettingCategory.INSTALLATION,
            setting_key="require_admin",
            setting_value=True,
        )
        PolicySetting.objects.create(
            policy=policy,
            category=PolicySetting.SettingCategory.UNINSTALL,
            setting_key="mode",
            setting_value="disabled",
        )

        settings = policy.get_settings_dict()
        assert "installation" in settings
        assert settings["installation"]["require_admin"] is True
        assert settings["uninstall"]["mode"] == "disabled"

    def test_unique_together_constraint(self):
        """Test unique_together constraint."""
        # Create first policy with no version
        policy1 = ApplicationPolicy.objects.create(  # noqa: F841
            name="Policy 1",
            application=self.application,
            application_version=None,
            platform="windows",
            created_by=self.user,
        )

        # Should not allow duplicate (same app, version=None, platform)
        # Note: Django's unique_together allows None values, so we need to test differently
        # Instead, test that we can't create duplicate with same app/version/platform
        policy2 = ApplicationPolicy.objects.create(  # noqa: F841
            name="Policy 2",
            application=self.application,
            application_version=self.version,  # Different version
            platform="windows",
            created_by=self.user,
        )
        # This should succeed since version is different

        # Now try to create duplicate with same version
        with pytest.raises(Exception):  # IntegrityError
            ApplicationPolicy.objects.create(
                name="Policy 3",
                application=self.application,
                application_version=self.version,  # Same version
                platform="windows",
                created_by=self.user,
            )


@pytest.mark.django_db
class TestPolicySetting:
    """Test PolicySetting model."""

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

    def test_create_policy_setting(self):
        """Test creating a policy setting."""
        setting = PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.INSTALLATION,
            setting_key="require_admin",
            setting_value=True,
            intune_mapping={"runAsAccount": "system"},
        )
        assert setting.category == PolicySetting.SettingCategory.INSTALLATION
        assert setting.setting_key == "require_admin"
        assert setting.setting_value is True
        assert setting.intune_mapping == {"runAsAccount": "system"}

    def test_unique_together_constraint(self):
        """Test unique_together constraint."""
        PolicySetting.objects.create(
            policy=self.policy,
            category=PolicySetting.SettingCategory.INSTALLATION,
            setting_key="require_admin",
            setting_value=True,
        )

        # Should not allow duplicate
        with pytest.raises(Exception):  # IntegrityError
            PolicySetting.objects.create(
                policy=self.policy,
                category=PolicySetting.SettingCategory.INSTALLATION,
                setting_key="require_admin",
                setting_value=False,
            )


@pytest.mark.django_db
class TestPolicyTemplate:
    """Test PolicyTemplate model."""

    def test_create_policy_template(self):
        """Test creating a policy template."""
        template = PolicyTemplate.objects.create(
            name="Enterprise Template",
            template_type=PolicyTemplate.TemplateType.ENTERPRISE,
            description="Enterprise policy template",
            settings={
                "installation": {"require_admin": True},
                "uninstall": {"mode": "disabled"},
            },
            is_system=True,
        )
        assert template.name == "Enterprise Template"
        assert template.template_type == PolicyTemplate.TemplateType.ENTERPRISE
        assert template.is_system is True
        assert "installation" in template.settings

    def test_template_str(self):
        """Test template string representation."""
        template = PolicyTemplate.objects.create(
            name="Test Template",
            template_type=PolicyTemplate.TemplateType.SECURITY,
            description="Test",
            settings={},
        )
        assert "Test Template" in str(template)
        assert "security" in str(template).lower()
