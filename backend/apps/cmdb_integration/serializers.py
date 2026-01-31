# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Serializers for CMDB Integration API.
"""
from rest_framework import serializers

from .models import (
    CMDBConnection,
    CMDBDataQualityReport,
    CMDBDiscrepancy,
    CMDBSyncRecord,
    CMDBTableMapping,
    CMDBValidationRule,
)


class CMDBConnectionSerializer(serializers.ModelSerializer):
    """Serializer for CMDB connections."""

    class Meta:
        model = CMDBConnection
        fields = [
            "id",
            "name",
            "instance_url",
            "auth_type",
            "credentials",
            "is_active",
            "last_sync",
            "last_sync_status",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "last_sync", "last_sync_status", "created_at", "updated_at"]

    def to_representation(self, instance: CMDBConnection) -> dict:
        """Mask sensitive credentials in response."""
        data = super().to_representation(instance)
        # Mask credentials for security
        if data.get("credentials"):
            data["credentials"] = {k: "***" for k in data["credentials"].keys()}
        return data


class CMDBConnectionCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating CMDB connections with credentials."""

    class Meta:
        model = CMDBConnection
        fields = [
            "name",
            "instance_url",
            "auth_type",
            "credentials",
            "is_active",
        ]


class CMDBTableMappingSerializer(serializers.ModelSerializer):
    """Serializer for CMDB table mappings."""

    connection_name = serializers.CharField(source="connection.name", read_only=True)

    class Meta:
        model = CMDBTableMapping
        fields = [
            "id",
            "connection",
            "connection_name",
            "source_type",
            "source_table",
            "cmdb_table",
            "field_mappings",
            "sync_enabled",
            "sync_direction",
            "priority",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CMDBValidationRuleSerializer(serializers.ModelSerializer):
    """Serializer for CMDB validation rules."""

    class Meta:
        model = CMDBValidationRule
        fields = [
            "id",
            "name",
            "description",
            "cmdb_table",
            "field_name",
            "rule_type",
            "rule_config",
            "severity",
            "is_active",
            "auto_fix",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CMDBSyncRecordSerializer(serializers.ModelSerializer):
    """Serializer for CMDB sync records."""

    connection_name = serializers.CharField(source="connection.name", read_only=True)
    duration_seconds = serializers.FloatField(read_only=True)
    initiated_by_username = serializers.CharField(source="initiated_by.username", read_only=True)
    discrepancy_count = serializers.SerializerMethodField()

    class Meta:
        model = CMDBSyncRecord
        fields = [
            "id",
            "correlation_id",
            "connection",
            "connection_name",
            "sync_type",
            "status",
            "started_at",
            "completed_at",
            "duration_seconds",
            "records_processed",
            "records_created",
            "records_updated",
            "records_skipped",
            "validation_errors",
            "errors",
            "quality_score",
            "initiated_by",
            "initiated_by_username",
            "discrepancy_count",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "correlation_id",
            "duration_seconds",
            "records_processed",
            "records_created",
            "records_updated",
            "records_skipped",
            "validation_errors",
            "errors",
            "quality_score",
            "created_at",
        ]

    def get_discrepancy_count(self, obj: CMDBSyncRecord) -> int:
        """Get count of discrepancies for this sync."""
        return obj.discrepancies.count()


class CMDBSyncStartSerializer(serializers.Serializer):
    """Serializer for starting a CMDB sync."""

    connection_id = serializers.UUIDField()
    sync_type = serializers.ChoiceField(choices=CMDBSyncRecord.SyncType.choices, default="incremental")
    tables = serializers.ListField(child=serializers.CharField(), required=False, default=list)


class CMDBDiscrepancySerializer(serializers.ModelSerializer):
    """Serializer for CMDB discrepancies."""

    sync_record_id = serializers.UUIDField(source="sync_record.id", read_only=True)
    resolved_by_username = serializers.CharField(source="resolved_by.username", read_only=True)

    class Meta:
        model = CMDBDiscrepancy
        fields = [
            "id",
            "sync_record",
            "sync_record_id",
            "ci_sys_id",
            "ci_name",
            "ci_class",
            "discrepancy_type",
            "field_name",
            "source_value",
            "cmdb_value",
            "source_system",
            "recommended_action",
            "confidence_score",
            "status",
            "resolved_by",
            "resolved_by_username",
            "resolved_at",
            "resolution_notes",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "sync_record",
            "ci_sys_id",
            "ci_name",
            "ci_class",
            "discrepancy_type",
            "field_name",
            "source_value",
            "cmdb_value",
            "source_system",
            "recommended_action",
            "confidence_score",
            "created_at",
        ]


class CMDBDiscrepancyResolveSerializer(serializers.Serializer):
    """Serializer for resolving discrepancies."""

    action = serializers.ChoiceField(choices=["approve", "reject", "ignore"])
    resolution_notes = serializers.CharField(required=False, default="")


class CMDBDiscrepancyBulkResolveSerializer(serializers.Serializer):
    """Serializer for bulk resolving discrepancies."""

    discrepancy_ids = serializers.ListField(child=serializers.UUIDField())
    action = serializers.ChoiceField(choices=["approve", "reject", "ignore"])
    resolution_notes = serializers.CharField(required=False, default="")


class CMDBDataQualityReportSerializer(serializers.ModelSerializer):
    """Serializer for CMDB data quality reports."""

    connection_name = serializers.CharField(source="connection.name", read_only=True)

    class Meta:
        model = CMDBDataQualityReport
        fields = [
            "id",
            "correlation_id",
            "connection",
            "connection_name",
            "sync_record",
            "overall_score",
            "completeness_score",
            "accuracy_score",
            "consistency_score",
            "timeliness_score",
            "total_cis",
            "cis_with_issues",
            "critical_issues",
            "warnings",
            "table_scores",
            "created_at",
        ]
        read_only_fields = ["id", "correlation_id", "created_at"]


class CMDBQualityScoreSerializer(serializers.Serializer):
    """Serializer for quality score dashboard."""

    overall_score = serializers.FloatField()
    completeness_score = serializers.FloatField()
    accuracy_score = serializers.FloatField()
    consistency_score = serializers.FloatField()
    timeliness_score = serializers.FloatField()
    total_cis = serializers.IntegerField()
    cis_with_issues = serializers.IntegerField()
    pending_discrepancies = serializers.IntegerField()
    last_sync = serializers.DateTimeField()
    trend = serializers.DictField()


class CMDBSyncHistorySerializer(serializers.Serializer):
    """Serializer for sync history summary."""

    date = serializers.DateField()
    syncs = serializers.IntegerField()
    records_processed = serializers.IntegerField()
    discrepancies_found = serializers.IntegerField()
    average_quality_score = serializers.FloatField()
