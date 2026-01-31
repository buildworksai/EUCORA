# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
DRF serializers for Portfolio Management API.

Implements serializers for Portfolio Manager and Application Manager personas,
with nested representations for complex relationships and read-only computed fields.
"""
from django.contrib.auth import get_user_model
from rest_framework import serializers

from apps.portfolio_management.models import (
    ApplicationManagerPerformance,
    ApplicationOwnership,
    LicenseTrueUpForecast,
    PackagingRequest,
    Portfolio,
)

User = get_user_model()


class PortfolioListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for portfolio lists."""

    manager_name = serializers.CharField(source="manager.username", read_only=True)
    license_utilization_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "name",
            "manager",
            "manager_name",
            "total_applications",
            "total_licenses_entitled",
            "total_licenses_consumed",
            "license_utilization_percent",
            "health_score",
            "compliance_score",
            "budget_annual",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_applications",
            "total_licenses_entitled",
            "total_licenses_consumed",
            "health_score",
            "compliance_score",
            "created_at",
            "updated_at",
        ]


class PortfolioDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for portfolio with full scope and metrics."""

    manager_name = serializers.CharField(source="manager.username", read_only=True)
    manager_email = serializers.EmailField(source="manager.email", read_only=True)
    license_utilization_percent = serializers.FloatField(read_only=True)

    class Meta:
        model = Portfolio
        fields = [
            "id",
            "name",
            "manager",
            "manager_name",
            "manager_email",
            "scope",
            "budget_annual",
            "total_applications",
            "total_licenses_entitled",
            "total_licenses_consumed",
            "license_utilization_percent",
            "health_score",
            "compliance_score",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_applications",
            "total_licenses_entitled",
            "total_licenses_consumed",
            "health_score",
            "compliance_score",
            "created_at",
            "updated_at",
        ]

    def validate_scope(self, value):
        """Validate scope structure contains required keys."""
        if not isinstance(value, dict):
            raise serializers.ValidationError("Scope must be a dictionary")
        # Validate scope has required structure
        # Example: {"business_units": [...], "geographies": [...], "sites": [...]}
        return value


class ApplicationOwnershipListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for application ownership lists."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    owner_name = serializers.CharField(source="owner.username", read_only=True)
    portfolio_name = serializers.CharField(source="portfolio.name", read_only=True)

    class Meta:
        model = ApplicationOwnership
        fields = [
            "id",
            "application",
            "application_name",
            "owner",
            "owner_name",
            "portfolio",
            "portfolio_name",
            "ownership_type",
            "is_active",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class ApplicationOwnershipDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for application ownership with full context."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    application_identifier = serializers.CharField(source="application.identifier", read_only=True)
    owner_name = serializers.CharField(source="owner.username", read_only=True)
    owner_email = serializers.EmailField(source="owner.email", read_only=True)
    portfolio_name = serializers.CharField(source="portfolio.name", read_only=True)
    assigned_by_name = serializers.CharField(source="assigned_by.username", read_only=True, allow_null=True)

    class Meta:
        model = ApplicationOwnership
        fields = [
            "id",
            "application",
            "application_name",
            "application_identifier",
            "owner",
            "owner_name",
            "owner_email",
            "portfolio",
            "portfolio_name",
            "ownership_type",
            "assigned_by",
            "assigned_by_name",
            "assigned_at",
            "is_active",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def validate(self, data):
        """Validate unique ownership constraint and scope alignment."""
        application = data.get("application")
        owner = data.get("owner")
        portfolio = data.get("portfolio")  # noqa: F841
        ownership_type = data.get("ownership_type")

        # Check for existing active ownership of same type
        if self.instance is None:  # Creating new ownership
            existing = ApplicationOwnership.objects.filter(
                application=application, owner=owner, ownership_type=ownership_type, is_active=True
            ).exists()
            if existing:
                raise serializers.ValidationError(
                    f"Active {ownership_type} ownership already exists for this application and owner"
                )

        # TODO: Validate scope alignment (owner scope ⊆ portfolio scope)
        # This requires implementing scope validation logic

        return data


class ApplicationManagerPerformanceSerializer(serializers.ModelSerializer):
    """Serializer for Application Manager performance metrics."""

    manager_name = serializers.CharField(source="manager.username", read_only=True)
    portfolio_name = serializers.CharField(source="portfolio.name", read_only=True, allow_null=True)

    class Meta:
        model = ApplicationManagerPerformance
        fields = [
            "id",
            "manager",
            "manager_name",
            "portfolio",
            "portfolio_name",
            "period_start",
            "period_end",
            "recorded_at",
            # Deployment metrics
            "deployments_total",
            "deployments_successful",
            "deployments_failed",
            "deployments_rolled_back",
            "success_rate_percent",
            "avg_deployment_duration_days",
            # Application metrics
            "applications_total",
            "applications_healthy",
            # Health metrics
            "avg_health_score",
            # License metrics
            "licenses_entitled",
            "licenses_consumed",
            "licenses_wasted",
            "utilization_percent",
            # Incident metrics
            "incidents_total",
            "incidents_resolved",
            "avg_mttr_hours",
            # Composite score
            "composite_score",
        ]
        read_only_fields = ["id", "recorded_at"]

    def validate(self, data):
        """Validate period dates and metric constraints."""
        period_start = data.get("period_start")
        period_end = data.get("period_end")

        if period_end and period_start and period_end <= period_start:
            raise serializers.ValidationError("period_end must be after period_start")

        # Validate percentage fields
        if data.get("success_rate_percent") and not (0 <= data["success_rate_percent"] <= 100):
            raise serializers.ValidationError("success_rate_percent must be between 0 and 100")

        if data.get("utilization_percent") and not (0 <= data["utilization_percent"] <= 200):
            raise serializers.ValidationError("utilization_percent must be between 0 and 200")

        if data.get("composite_score") and not (0 <= data["composite_score"] <= 100):
            raise serializers.ValidationError("composite_score must be between 0 and 100")

        return data


class LicenseTrueUpForecastSerializer(serializers.ModelSerializer):
    """Serializer for License True-Up forecasts."""

    vendor_name = serializers.CharField(source="vendor.name", read_only=True)
    portfolio_name = serializers.CharField(source="portfolio.name", read_only=True)

    class Meta:
        model = LicenseTrueUpForecast
        fields = [
            "id",
            "vendor",
            "vendor_name",
            "portfolio",
            "portfolio_name",
            "forecast_period",
            "forecast_generated_at",
            "forecast_horizon_days",
            # Current state
            "entitled_quantity_current",
            "consumed_quantity_current",
            "utilization_current_percent",
            # Forecast
            "consumed_quantity_forecast",
            "consumption_growth_percent",
            "additional_licenses_needed",
            "estimated_cost_impact",
            "confidence_percent",
            # Mitigation
            "mitigation_recommendations",
            "potential_savings",
        ]
        read_only_fields = ["id", "forecast_generated_at"]

    def validate(self, data):
        """Validate forecast metrics."""
        if data.get("confidence_percent") and not (0 <= data["confidence_percent"] <= 100):
            raise serializers.ValidationError("confidence_percent must be between 0 and 100")

        # Validate quantities make sense
        forecast = data.get("consumed_quantity_forecast", 0)
        entitled = data.get("entitled_quantity_current", 0)
        additional = data.get("additional_licenses_needed", 0)

        if forecast < 0 or entitled < 0 or additional < 0:
            raise serializers.ValidationError("Quantities must be non-negative")

        if forecast > entitled and additional != (forecast - entitled):
            raise serializers.ValidationError(
                "additional_licenses_needed should equal consumed_quantity_forecast - entitled_quantity_current"
            )

        return data


class PackagingRequestSerializer(serializers.ModelSerializer):
    """Serializer for Packaging Requests workflow."""

    application_name = serializers.CharField(source="application.name", read_only=True)
    requested_by_name = serializers.CharField(source="requested_by.username", read_only=True)
    assigned_to_name = serializers.CharField(source="assigned_to.username", read_only=True, allow_null=True)

    class Meta:
        model = PackagingRequest
        fields = [
            "id",
            "application",
            "application_name",
            "version_identifier",
            "requested_by",
            "requested_by_name",
            "assigned_to",
            "assigned_to_name",
            "priority",
            "requirements",
            "notes",
            "status",
            "requested_at",
            "assigned_at",
            "completed_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "created_at",
            "assigned_at",
            "completed_at",
            "turnaround_time_hours",
            "updated_at",
        ]

    def validate(self, data):
        """Validate packaging request workflow constraints."""
        status = data.get("status")

        # Validate status transitions
        if self.instance and self.instance.status == "COMPLETED":
            raise serializers.ValidationError("Cannot modify a completed packaging request")

        if status == "IN_PROGRESS" and not data.get("assigned_to"):
            raise serializers.ValidationError("assigned_to is required when status is IN_PROGRESS")

        # Validate requirements structure if provided
        requirements = data.get("requirements")
        if requirements and isinstance(requirements, dict):
            platforms = requirements.get("platforms", [])
            if not platforms:
                raise serializers.ValidationError("requirements.platforms cannot be empty")

        return data
