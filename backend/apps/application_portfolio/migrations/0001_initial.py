# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Initial migration for application_portfolio."""
import uuid
from decimal import Decimal

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Initial migration for application_portfolio app."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("core", "0001_initial"),
    ]

    operations = [
        # Publisher model
        migrations.CreateModel(
            name="Publisher",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255, unique=True)),
                ("identifier", models.CharField(max_length=255, unique=True)),
                ("website", models.URLField(blank=True)),
                ("support_url", models.URLField(blank=True)),
                ("is_verified", models.BooleanField(default=False)),
                (
                    "trust_score",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.50"),
                        max_digits=3,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
            ],
            options={
                "db_table": "app_portfolio_publisher",
                "ordering": ["name"],
            },
        ),
        # Application model
        migrations.CreateModel(
            name="Application",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("name", models.CharField(max_length=255)),
                ("identifier", models.CharField(max_length=255, unique=True)),
                ("description", models.TextField(blank=True)),
                ("category", models.CharField(blank=True, max_length=100)),
                ("tags", models.JSONField(blank=True, default=list)),
                ("homepage_url", models.URLField(blank=True)),
                ("documentation_url", models.URLField(blank=True)),
                ("icon_url", models.URLField(blank=True)),
                ("team", models.CharField(blank=True, max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("pending_review", "Pending Review"),
                            ("published", "Published"),
                            ("deprecated", "Deprecated"),
                            ("archived", "Archived"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("supported_platforms", models.JSONField(default=list)),
                ("risk_score", models.IntegerField(default=0)),
                ("requires_cab_approval", models.BooleanField(default=False)),
                ("is_privileged", models.BooleanField(db_index=True, default=False)),
                ("is_internal", models.BooleanField(default=False)),
                ("is_active", models.BooleanField(db_index=True, default=True)),
                (
                    "owner",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="owned_applications",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "publisher",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="applications",
                        to="application_portfolio.publisher",
                    ),
                ),
            ],
            options={
                "db_table": "app_portfolio_application",
                "ordering": ["name"],
            },
        ),
        migrations.AddIndex(
            model_name="application",
            index=models.Index(
                fields=["publisher", "status"],
                name="app_portfol_publish_c59c88_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="application",
            index=models.Index(
                fields=["category", "status"],
                name="app_portfol_categor_4fba91_idx",
            ),
        ),
        # ApplicationVersion model
        migrations.CreateModel(
            name="ApplicationVersion",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("version", models.CharField(max_length=50)),
                ("version_code", models.IntegerField(default=0)),
                ("release_notes", models.TextField(blank=True)),
                ("release_date", models.DateField(blank=True, null=True)),
                ("is_latest", models.BooleanField(db_index=True, default=False)),
                ("is_security_update", models.BooleanField(default=False)),
                ("deprecation_date", models.DateField(blank=True, null=True)),
                ("end_of_life_date", models.DateField(blank=True, null=True)),
                ("min_os_versions", models.JSONField(blank=True, default=dict)),
                ("system_requirements", models.JSONField(blank=True, default=dict)),
                ("dependencies", models.JSONField(blank=True, default=dict)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="versions",
                        to="application_portfolio.application",
                    ),
                ),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_versions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "app_portfolio_version",
                "ordering": ["-version_code", "-created_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="applicationversion",
            constraint=models.UniqueConstraint(
                fields=("application", "version"),
                name="unique_app_version",
            ),
        ),
        migrations.AddIndex(
            model_name="applicationversion",
            index=models.Index(
                fields=["application", "is_latest"],
                name="app_portfol_applica_36eaa7_idx",
            ),
        ),
        # PackageArtifact model
        migrations.CreateModel(
            name="PackageArtifact",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "correlation_id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "platform",
                    models.CharField(
                        choices=[
                            ("windows", "Windows"),
                            ("macos", "macOS"),
                            ("linux", "Linux"),
                            ("ios", "iOS"),
                            ("ipados", "iPadOS"),
                            ("android", "Android"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("architecture", models.CharField(default="x64", max_length=20)),
                (
                    "package_type",
                    models.CharField(
                        choices=[
                            ("intunewin", "Intune Win32"),
                            ("msix", "MSIX"),
                            ("msi", "MSI"),
                            ("exe", "EXE"),
                            ("pkg", "macOS PKG"),
                            ("dmg", "macOS DMG"),
                            ("deb", "Debian Package"),
                            ("rpm", "RPM Package"),
                            ("ipa", "iOS IPA"),
                            ("apk", "Android APK"),
                        ],
                        max_length=20,
                    ),
                ),
                ("file_name", models.CharField(max_length=255)),
                ("file_size", models.BigIntegerField(default=0)),
                ("file_hash_sha256", models.CharField(max_length=64)),
                ("storage_ref", models.CharField(max_length=500)),
                ("is_signed", models.BooleanField(default=False)),
                ("signature_type", models.CharField(blank=True, max_length=50)),
                ("signer_identity", models.CharField(blank=True, max_length=255)),
                ("signature_timestamp", models.DateTimeField(blank=True, null=True)),
                ("sbom_ref", models.CharField(blank=True, max_length=500)),
                ("sbom_format", models.CharField(blank=True, max_length=20)),
                (
                    "scan_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("in_progress", "In Progress"),
                            ("passed", "Passed"),
                            ("failed", "Failed"),
                            ("exception", "Exception Approved"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("scan_completed_at", models.DateTimeField(blank=True, null=True)),
                ("vulnerability_count_critical", models.IntegerField(default=0)),
                ("vulnerability_count_high", models.IntegerField(default=0)),
                ("vulnerability_count_medium", models.IntegerField(default=0)),
                ("vulnerability_count_low", models.IntegerField(default=0)),
                ("scan_report_ref", models.CharField(blank=True, max_length=500)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("uploading", "Uploading"),
                            ("processing", "Processing"),
                            ("scanning", "Scanning"),
                            ("ready", "Ready"),
                            ("failed", "Failed"),
                            ("quarantined", "Quarantined"),
                        ],
                        db_index=True,
                        default="uploading",
                        max_length=20,
                    ),
                ),
                ("install_command", models.TextField(blank=True)),
                ("uninstall_command", models.TextField(blank=True)),
                ("detection_rules", models.JSONField(blank=True, default=dict)),
                ("requirement_rules", models.JSONField(blank=True, default=dict)),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="uploaded_artifacts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "version",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="artifacts",
                        to="application_portfolio.applicationversion",
                    ),
                ),
            ],
            options={
                "db_table": "app_portfolio_artifact",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="packageartifact",
            index=models.Index(
                fields=["version", "platform"],
                name="app_portfol_version_0d5c74_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="packageartifact",
            index=models.Index(
                fields=["scan_status", "status"],
                name="app_portfol_scan_st_71f3e9_idx",
            ),
        ),
        # DeploymentIntent model
        migrations.CreateModel(
            name="DeploymentIntent",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "correlation_id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        unique=True,
                    ),
                ),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                (
                    "target_ring",
                    models.CharField(
                        choices=[
                            ("ring_0", "Ring 0 - Lab"),
                            ("ring_1", "Ring 1 - Canary"),
                            ("ring_2", "Ring 2 - Pilot"),
                            ("ring_3", "Ring 3 - Department"),
                            ("ring_4", "Ring 4 - Global"),
                        ],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                ("target_scope", models.JSONField(default=dict)),
                ("target_device_count", models.IntegerField(default=0)),
                ("scheduled_start", models.DateTimeField(blank=True, null=True)),
                ("scheduled_end", models.DateTimeField(blank=True, null=True)),
                ("deadline", models.DateTimeField(blank=True, null=True)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("pending_approval", "Pending CAB Approval"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("scheduled", "Scheduled"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                            ("rolled_back", "Rolled Back"),
                        ],
                        db_index=True,
                        default="draft",
                        max_length=20,
                    ),
                ),
                ("risk_score", models.IntegerField(default=0)),
                ("risk_model_version", models.CharField(default="v1.0", max_length=20)),
                ("requires_cab_approval", models.BooleanField(default=False)),
                ("cab_request_id", models.UUIDField(blank=True, null=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("approval_notes", models.TextField(blank=True)),
                ("evidence_pack_ref", models.CharField(blank=True, max_length=500)),
                ("evidence_pack_hash", models.CharField(blank=True, max_length=64)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("rollout_config", models.JSONField(blank=True, default=dict)),
                ("rollback_plan", models.JSONField(blank=True, default=dict)),
                ("rollback_triggered", models.BooleanField(default=False)),
                ("rollback_at", models.DateTimeField(blank=True, null=True)),
                ("rollback_reason", models.TextField(blank=True)),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_deployments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "artifact",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="deployment_intents",
                        to="application_portfolio.packageartifact",
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_deployments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "app_portfolio_deployment_intent",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="deploymentintent",
            index=models.Index(
                fields=["artifact", "target_ring", "status"],
                name="app_portfol_artifac_c2a96a_idx",
            ),
        ),
        migrations.AddIndex(
            model_name="deploymentintent",
            index=models.Index(
                fields=["status", "scheduled_start"],
                name="app_portfol_status_8d0d3b_idx",
            ),
        ),
        # DeploymentMetric model
        migrations.CreateModel(
            name="DeploymentMetric",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("recorded_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("devices_targeted", models.IntegerField(default=0)),
                ("devices_pending", models.IntegerField(default=0)),
                ("devices_in_progress", models.IntegerField(default=0)),
                ("devices_succeeded", models.IntegerField(default=0)),
                ("devices_failed", models.IntegerField(default=0)),
                ("devices_not_applicable", models.IntegerField(default=0)),
                (
                    "success_rate",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=5,
                    ),
                ),
                ("avg_install_time_seconds", models.IntegerField(default=0)),
                ("time_to_compliance_avg_seconds", models.IntegerField(default=0)),
                ("error_summary", models.JSONField(blank=True, default=dict)),
                (
                    "deployment",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="metrics",
                        to="application_portfolio.deploymentintent",
                    ),
                ),
            ],
            options={
                "db_table": "app_portfolio_deployment_metric",
                "ordering": ["-recorded_at"],
            },
        ),
        migrations.AddIndex(
            model_name="deploymentmetric",
            index=models.Index(
                fields=["deployment", "recorded_at"],
                name="app_portfol_deploym_cff7e6_idx",
            ),
        ),
        # ApplicationHealth model
        migrations.CreateModel(
            name="ApplicationHealth",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("recorded_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                (
                    "health_status",
                    models.CharField(
                        choices=[
                            ("healthy", "Healthy"),
                            ("degraded", "Degraded"),
                            ("unhealthy", "Unhealthy"),
                            ("unknown", "Unknown"),
                        ],
                        db_index=True,
                        default="unknown",
                        max_length=20,
                    ),
                ),
                ("health_message", models.TextField(blank=True)),
                ("total_installations", models.IntegerField(default=0)),
                ("healthy_installations", models.IntegerField(default=0)),
                ("unhealthy_installations", models.IntegerField(default=0)),
                ("unknown_installations", models.IntegerField(default=0)),
                ("version_distribution", models.JSONField(blank=True, default=dict)),
                (
                    "compliance_status",
                    models.CharField(
                        choices=[
                            ("compliant", "Compliant"),
                            ("non_compliant", "Non-Compliant"),
                            ("unknown", "Unknown"),
                        ],
                        default="unknown",
                        max_length=20,
                    ),
                ),
                (
                    "compliance_score",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("0.00"),
                        max_digits=5,
                    ),
                ),
                ("active_incidents", models.IntegerField(default=0)),
                ("open_vulnerabilities", models.IntegerField(default=0)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="health_records",
                        to="application_portfolio.application",
                    ),
                ),
            ],
            options={
                "db_table": "app_portfolio_health",
                "ordering": ["-recorded_at"],
            },
        ),
        migrations.AddIndex(
            model_name="applicationhealth",
            index=models.Index(
                fields=["application", "recorded_at"],
                name="app_portfol_applica_2eea45_idx",
            ),
        ),
        # ApplicationDependency model
        migrations.CreateModel(
            name="ApplicationDependency",
            fields=[
                (
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "id",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                    ),
                ),
                ("dependency_type", models.CharField(default="runtime", max_length=50)),
                ("min_version", models.CharField(blank=True, max_length=50)),
                ("max_version", models.CharField(blank=True, max_length=50)),
                ("is_required", models.BooleanField(default=True)),
                ("notes", models.TextField(blank=True)),
                (
                    "application",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dependencies",
                        to="application_portfolio.application",
                    ),
                ),
                (
                    "depends_on",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="dependents",
                        to="application_portfolio.application",
                    ),
                ),
            ],
            options={
                "db_table": "app_portfolio_dependency",
                "ordering": ["application__name", "depends_on__name"],
            },
        ),
        migrations.AddConstraint(
            model_name="applicationdependency",
            constraint=models.UniqueConstraint(
                fields=("application", "depends_on"),
                name="unique_app_dependency",
            ),
        ),
    ]
