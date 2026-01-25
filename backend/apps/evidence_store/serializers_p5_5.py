# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Phase P5.5: Serializers for Defense-in-Depth Security Controls
"""
from rest_framework import serializers

from .models_p5_5 import (
    BlastRadiusClass,
    DeploymentIncident,
    RiskModelVersion,
    TrustMaturityLevel,
    TrustMaturityProgress,
)


class DeploymentIncidentSerializer(serializers.ModelSerializer):
    """Full incident serializer with all fields."""

    is_resolved = serializers.BooleanField(read_only=True)
    was_high_severity = serializers.BooleanField(read_only=True)

    class Meta:
        model = DeploymentIncident
        fields = "__all__"


class DeploymentIncidentCreateSerializer(serializers.ModelSerializer):
    """Incident creation serializer."""

    class Meta:
        model = DeploymentIncident
        fields = [
            "deployment_intent_id",
            "evidence_package_id",
            "cab_approval_id",
            "severity",
            "incident_date",
            "detection_method",
            "title",
            "description",
            "was_auto_approved",
            "risk_score_at_approval",
            "risk_model_version",
            "blast_radius_class",
            "affected_user_count",
            "downtime_minutes",
            "business_impact_usd",
        ]


class RiskModelVersionSerializer(serializers.ModelSerializer):
    """Risk model version serializer."""

    class Meta:
        model = RiskModelVersion
        fields = "__all__"


class BlastRadiusClassificationSerializer(serializers.Serializer):
    """Blast radius classification result."""

    app_name = serializers.CharField()
    blast_radius_class = serializers.CharField()
    description = serializers.CharField()
    cab_quorum_required = serializers.IntegerField()
    auto_approve_allowed = serializers.BooleanField()
    business_criticality = serializers.CharField()
    user_impact_max = serializers.IntegerField()
    examples = serializers.ListField()


class TrustMaturityStatusSerializer(serializers.Serializer):
    """Current maturity status."""

    current_level = serializers.CharField()
    risk_model_version = serializers.CharField()
    risk_model_mode = serializers.CharField()
    auto_approve_thresholds = serializers.DictField()
    latest_evaluation = serializers.DictField(required=False, allow_null=True)


class TrustMaturityEvaluationSerializer(serializers.Serializer):
    """Maturity evaluation result."""

    ready_to_progress = serializers.BooleanField()
    current_level = serializers.CharField()
    next_level = serializers.CharField(required=False, allow_null=True)
    evaluation_period = serializers.DictField()
    incident_analysis = serializers.DictField()
    criteria_evaluation = serializers.ListField()
    blocking_criteria = serializers.ListField()
    recommendation = serializers.CharField(required=False)
    new_risk_model_version = serializers.CharField(required=False)
    new_thresholds = serializers.DictField(required=False)
