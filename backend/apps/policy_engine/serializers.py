# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Policy Engine serializers.

REST API serializers for application policies, settings, and templates.
"""
from rest_framework import serializers

from .models import ApplicationPolicy, PolicySetting, PolicyTemplate

# =============================================================================
# POLICY SETTING SERIALIZERS
# =============================================================================


class PolicySettingSerializer(serializers.ModelSerializer):
    """Full policy setting serializer."""

    class Meta:
        model = PolicySetting
        fields = [
            "id",
            "policy",
            "category",
            "setting_key",
            "setting_value",
            "intune_mapping",
            "jamf_mapping",
            "sccm_mapping",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PolicySettingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating policy settings."""

    class Meta:
        model = PolicySetting
        fields = ["category", "setting_key", "setting_value", "intune_mapping", "jamf_mapping", "sccm_mapping"]


# =============================================================================
# APPLICATION POLICY SERIALIZERS
# =============================================================================


class ApplicationPolicySerializer(serializers.ModelSerializer):
    """Full application policy serializer."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    application_identifier = serializers.CharField(source="application.identifier", read_only=True)
    version_str = serializers.CharField(source="application_version.version", read_only=True, allow_null=True)
    created_by_username = serializers.CharField(source="created_by.username", read_only=True, allow_null=True)
    settings = PolicySettingSerializer(many=True, read_only=True)
    settings_dict = serializers.SerializerMethodField()

    class Meta:
        model = ApplicationPolicy
        fields = [
            "id",
            "correlation_id",
            "name",
            "description",
            "application",
            "application_name",
            "application_identifier",
            "application_version",
            "version_str",
            "platform",
            "is_active",
            "is_default",
            "created_by",
            "created_by_username",
            "settings",
            "settings_dict",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at", "updated_at", "settings_dict"]

    def get_settings_dict(self, obj: ApplicationPolicy) -> dict:
        """Get settings as nested dictionary."""
        return obj.get_settings_dict()


class ApplicationPolicyListSerializer(serializers.ModelSerializer):
    """Lightweight policy serializer for lists."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    platform = serializers.CharField(read_only=True)

    class Meta:
        model = ApplicationPolicy
        fields = [
            "id",
            "correlation_id",
            "name",
            "application_name",
            "platform",
            "is_active",
            "is_default",
            "created_at",
        ]


class ApplicationPolicyCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating application policies."""

    settings = PolicySettingCreateSerializer(many=True, required=False)

    class Meta:
        model = ApplicationPolicy
        fields = [
            "name",
            "description",
            "application",
            "application_version",
            "platform",
            "is_active",
            "is_default",
            "settings",
        ]
        extra_kwargs = {
            "application_version": {"required": False, "allow_null": True},
        }

    def create(self, validated_data):
        """Create policy with nested settings."""
        settings_data = validated_data.pop("settings", [])
        policy = ApplicationPolicy.objects.create(**validated_data)
        for setting_data in settings_data:
            PolicySetting.objects.create(policy=policy, **setting_data)
        return policy


class ApplicationPolicyUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating application policies."""

    settings = PolicySettingCreateSerializer(many=True, required=False)

    class Meta:
        model = ApplicationPolicy
        fields = [
            "name",
            "description",
            "is_active",
            "is_default",
            "settings",
        ]

    def update(self, instance, validated_data):
        """Update policy and settings."""
        settings_data = validated_data.pop("settings", None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        if settings_data is not None:
            # Delete existing settings and recreate
            instance.settings.all().delete()
            for setting_data in settings_data:
                PolicySetting.objects.create(policy=instance, **setting_data)

        return instance


# =============================================================================
# POLICY TEMPLATE SERIALIZERS
# =============================================================================


class PolicyTemplateSerializer(serializers.ModelSerializer):
    """Full policy template serializer."""

    class Meta:
        model = PolicyTemplate
        fields = [
            "id",
            "name",
            "template_type",
            "description",
            "settings",
            "is_system",
            "platform",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class PolicyTemplateListSerializer(serializers.ModelSerializer):
    """Lightweight template serializer for lists."""

    class Meta:
        model = PolicyTemplate
        fields = [
            "id",
            "name",
            "template_type",
            "description",
            "platform",
            "is_system",
        ]


# =============================================================================
# VALIDATION SERIALIZERS
# =============================================================================


class PolicyValidationSerializer(serializers.Serializer):
    """Serializer for policy validation requests."""

    policy_id = serializers.UUIDField(required=False)
    settings = serializers.DictField(required=False)
    platform = serializers.CharField(required=False)


class PolicyMappingPreviewSerializer(serializers.Serializer):
    """Serializer for execution plane mapping preview requests."""

    policy_id = serializers.UUIDField(required=False)  # Optional since pk is in URL
    target_plane = serializers.ChoiceField(choices=["intune", "jamf", "sccm"], required=True)
