# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""Initial migration for license_management."""
import uuid
from decimal import Decimal

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Initial migration for license_management app."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        # Vendor model
        migrations.CreateModel(
            name="Vendor",
            fields=[
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
                ("name", models.CharField(max_length=255)),
                ("vendor_code", models.CharField(max_length=50, unique=True)),
                ("contact_email", models.EmailField(blank=True, max_length=254)),
                ("website_url", models.URLField(blank=True)),
                ("notes", models.TextField(blank=True)),
                ("is_active", models.BooleanField(default=True)),
            ],
            options={
                "verbose_name": "Vendor",
                "verbose_name_plural": "Vendors",
                "ordering": ["name"],
            },
        ),
        # LicenseSKU model
        migrations.CreateModel(
            name="LicenseSKU",
            fields=[
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
                ("sku_code", models.CharField(max_length=100)),
                ("name", models.CharField(max_length=255)),
                ("description", models.TextField(blank=True)),
                (
                    "license_model_type",
                    models.CharField(
                        choices=[
                            ("user_subscription", "User Subscription"),
                            ("device_subscription", "Device Subscription"),
                            ("concurrent", "Concurrent"),
                            ("site", "Site License"),
                            ("perpetual", "Perpetual"),
                            ("consumption", "Consumption-based"),
                        ],
                        default="user_subscription",
                        max_length=50,
                    ),
                ),
                (
                    "computation_rule",
                    models.JSONField(
                        blank=True,
                        default=dict,
                        help_text="JSON rules for consumption computation",
                    ),
                ),
                ("is_active", models.BooleanField(default=True)),
                (
                    "vendor",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="skus",
                        to="license_management.vendor",
                    ),
                ),
            ],
            options={
                "verbose_name": "License SKU",
                "verbose_name_plural": "License SKUs",
                "ordering": ["vendor__name", "name"],
            },
        ),
        migrations.AddConstraint(
            model_name="licensesku",
            constraint=models.UniqueConstraint(
                fields=("vendor", "sku_code"),
                name="unique_vendor_sku_code",
            ),
        ),
        # Entitlement model
        migrations.CreateModel(
            name="Entitlement",
            fields=[
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
                ("contract_ref", models.CharField(max_length=255)),
                ("quantity", models.PositiveIntegerField()),
                ("effective_date", models.DateField()),
                ("expiry_date", models.DateField()),
                ("purchase_order", models.CharField(blank=True, max_length=100)),
                ("cost_center", models.CharField(blank=True, max_length=100)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending Approval"),
                            ("active", "Active"),
                            ("expired", "Expired"),
                            ("terminated", "Terminated"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("notes", models.TextField(blank=True)),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_entitlements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="created_entitlements",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "sku",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="entitlements",
                        to="license_management.licensesku",
                    ),
                ),
            ],
            options={
                "verbose_name": "Entitlement",
                "verbose_name_plural": "Entitlements",
                "ordering": ["-effective_date"],
            },
        ),
        migrations.AddIndex(
            model_name="entitlement",
            index=models.Index(
                fields=["sku", "status"],
                name="lm_entitlement_sku_status_idx",
            ),
        ),
        # LicensePool model
        migrations.CreateModel(
            name="LicensePool",
            fields=[
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
                ("name", models.CharField(max_length=255)),
                (
                    "scope_type",
                    models.CharField(
                        choices=[
                            ("global", "Global"),
                            ("business_unit", "Business Unit"),
                            ("site", "Site"),
                            ("department", "Department"),
                            ("project", "Project"),
                        ],
                        default="global",
                        max_length=50,
                    ),
                ),
                ("scope_id", models.CharField(blank=True, max_length=100)),
                ("allocated_quantity", models.PositiveIntegerField(default=0)),
                ("consumed_quantity", models.PositiveIntegerField(default=0)),
                ("reserved_quantity", models.PositiveIntegerField(default=0)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "sku",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="pools",
                        to="license_management.licensesku",
                    ),
                ),
            ],
            options={
                "verbose_name": "License Pool",
                "verbose_name_plural": "License Pools",
                "ordering": ["sku__name", "name"],
            },
        ),
        migrations.AddIndex(
            model_name="licensepool",
            index=models.Index(
                fields=["sku", "scope_type", "scope_id"],
                name="lm_pool_sku_scope_idx",
            ),
        ),
        # Assignment model
        migrations.CreateModel(
            name="Assignment",
            fields=[
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
                    "principal_type",
                    models.CharField(
                        choices=[
                            ("user", "User"),
                            ("device", "Device"),
                            ("group", "Group"),
                            ("service_principal", "Service Principal"),
                        ],
                        default="user",
                        max_length=50,
                    ),
                ),
                ("principal_id", models.CharField(db_index=True, max_length=255)),
                ("principal_name", models.CharField(blank=True, max_length=255)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("suspended", "Suspended"),
                            ("revoked", "Revoked"),
                            ("expired", "Expired"),
                        ],
                        default="active",
                        max_length=20,
                    ),
                ),
                ("assigned_at", models.DateTimeField(auto_now_add=True)),
                ("revoked_at", models.DateTimeField(blank=True, null=True)),
                ("revocation_reason", models.TextField(blank=True)),
                (
                    "assigned_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="license_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "pool",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="assignments",
                        to="license_management.licensepool",
                    ),
                ),
                (
                    "revoked_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="revoked_assignments",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Assignment",
                "verbose_name_plural": "Assignments",
                "ordering": ["-assigned_at"],
            },
        ),
        migrations.AddIndex(
            model_name="assignment",
            index=models.Index(
                fields=["pool", "principal_type", "principal_id"],
                name="lm_assignment_pool_principal_idx",
            ),
        ),
        # ConsumptionSignal model
        migrations.CreateModel(
            name="ConsumptionSignal",
            fields=[
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
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source_system", models.CharField(db_index=True, max_length=100)),
                ("raw_id", models.CharField(max_length=255)),
                ("timestamp", models.DateTimeField(db_index=True)),
                (
                    "principal_type",
                    models.CharField(
                        choices=[
                            ("user", "User"),
                            ("device", "Device"),
                            ("group", "Group"),
                            ("service_principal", "Service Principal"),
                        ],
                        max_length=50,
                    ),
                ),
                ("principal_id", models.CharField(db_index=True, max_length=255)),
                ("principal_name", models.CharField(blank=True, max_length=255)),
                (
                    "confidence",
                    models.DecimalField(
                        decimal_places=2,
                        default=Decimal("1.0"),
                        max_digits=3,
                    ),
                ),
                ("raw_payload", models.JSONField(blank=True, default=dict)),
                ("is_processed", models.BooleanField(default=False)),
                ("processed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "sku",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="consumption_signals",
                        to="license_management.licensesku",
                    ),
                ),
            ],
            options={
                "verbose_name": "Consumption Signal",
                "verbose_name_plural": "Consumption Signals",
                "ordering": ["-timestamp"],
            },
        ),
        migrations.AddConstraint(
            model_name="consumptionsignal",
            constraint=models.UniqueConstraint(
                fields=("source_system", "raw_id"),
                name="unique_source_raw_id",
            ),
        ),
        # ConsumptionUnit model
        migrations.CreateModel(
            name="ConsumptionUnit",
            fields=[
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
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "principal_type",
                    models.CharField(
                        choices=[
                            ("user", "User"),
                            ("device", "Device"),
                            ("group", "Group"),
                            ("service_principal", "Service Principal"),
                        ],
                        max_length=50,
                    ),
                ),
                ("principal_id", models.CharField(db_index=True, max_length=255)),
                ("principal_name", models.CharField(blank=True, max_length=255)),
                ("first_seen_at", models.DateTimeField()),
                ("last_seen_at", models.DateTimeField()),
                ("signal_count", models.PositiveIntegerField(default=1)),
                ("is_active", models.BooleanField(default=True)),
                (
                    "assignment",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="consumption_units",
                        to="license_management.assignment",
                    ),
                ),
                (
                    "sku",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="consumption_units",
                        to="license_management.licensesku",
                    ),
                ),
            ],
            options={
                "verbose_name": "Consumption Unit",
                "verbose_name_plural": "Consumption Units",
                "ordering": ["-last_seen_at"],
            },
        ),
        migrations.AddConstraint(
            model_name="consumptionunit",
            constraint=models.UniqueConstraint(
                fields=("sku", "principal_type", "principal_id"),
                name="unique_sku_principal",
            ),
        ),
        # ReconciliationRun model
        migrations.CreateModel(
            name="ReconciliationRun",
            fields=[
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
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                        ],
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("skus_processed", models.PositiveIntegerField(default=0)),
                ("snapshots_created", models.PositiveIntegerField(default=0)),
                ("alerts_generated", models.PositiveIntegerField(default=0)),
                ("error_message", models.TextField(blank=True)),
                (
                    "triggered_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="reconciliation_runs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Reconciliation Run",
                "verbose_name_plural": "Reconciliation Runs",
                "ordering": ["-started_at"],
            },
        ),
        # ConsumptionSnapshot model
        migrations.CreateModel(
            name="ConsumptionSnapshot",
            fields=[
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
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("reconciled_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("entitled_quantity", models.PositiveIntegerField()),
                ("allocated_quantity", models.PositiveIntegerField()),
                ("consumed_quantity", models.PositiveIntegerField()),
                ("available_quantity", models.IntegerField()),
                (
                    "utilization_percent",
                    models.DecimalField(decimal_places=2, max_digits=6),
                ),
                (
                    "evidence_pack_ref",
                    models.CharField(
                        default=uuid.uuid4,
                        max_length=255,
                        unique=True,
                    ),
                ),
                ("evidence_pack_hash", models.CharField(max_length=64)),
                ("snapshot_data", models.JSONField(default=dict)),
                (
                    "pool",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="snapshots",
                        to="license_management.licensepool",
                    ),
                ),
                (
                    "reconciliation_run",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="snapshots",
                        to="license_management.reconciliationrun",
                    ),
                ),
                (
                    "sku",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="snapshots",
                        to="license_management.licensesku",
                    ),
                ),
            ],
            options={
                "verbose_name": "Consumption Snapshot",
                "verbose_name_plural": "Consumption Snapshots",
                "ordering": ["-reconciled_at"],
            },
        ),
        migrations.AddIndex(
            model_name="consumptionsnapshot",
            index=models.Index(
                fields=["sku", "reconciled_at"],
                name="lm_snapshot_sku_reconciled_idx",
            ),
        ),
        # LicenseAlert model
        migrations.CreateModel(
            name="LicenseAlert",
            fields=[
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
                    "alert_type",
                    models.CharField(
                        choices=[
                            ("over_allocation", "Over-Allocation"),
                            ("under_utilization", "Under-Utilization"),
                            ("expiry_warning", "Expiry Warning"),
                            ("consumption_spike", "Consumption Spike"),
                            ("drift_detected", "Drift Detected"),
                            ("reconciliation_error", "Reconciliation Error"),
                        ],
                        max_length=50,
                    ),
                ),
                (
                    "severity",
                    models.CharField(
                        choices=[
                            ("low", "Low"),
                            ("medium", "Medium"),
                            ("high", "High"),
                            ("critical", "Critical"),
                        ],
                        max_length=20,
                    ),
                ),
                ("title", models.CharField(max_length=255)),
                ("message", models.TextField()),
                ("metadata", models.JSONField(blank=True, default=dict)),
                ("acknowledged", models.BooleanField(default=False)),
                ("acknowledged_at", models.DateTimeField(blank=True, null=True)),
                ("resolution_notes", models.TextField(blank=True)),
                (
                    "acknowledged_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="acknowledged_alerts",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "pool",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alerts",
                        to="license_management.licensepool",
                    ),
                ),
                (
                    "sku",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="alerts",
                        to="license_management.licensesku",
                    ),
                ),
            ],
            options={
                "verbose_name": "License Alert",
                "verbose_name_plural": "License Alerts",
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="licensealert",
            index=models.Index(
                fields=["acknowledged", "severity"],
                name="lm_alert_ack_severity_idx",
            ),
        ),
        # ImportJob model
        migrations.CreateModel(
            name="ImportJob",
            fields=[
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
                    "created_at",
                    models.DateTimeField(
                        db_index=True,
                        default=django.utils.timezone.now,
                        editable=False,
                    ),
                ),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("source_type", models.CharField(max_length=50)),
                ("filename", models.CharField(blank=True, max_length=255)),
                ("file_hash", models.CharField(blank=True, max_length=64)),
                ("status", models.CharField(default="pending", max_length=20)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("records_processed", models.PositiveIntegerField(default=0)),
                ("records_succeeded", models.PositiveIntegerField(default=0)),
                ("records_failed", models.PositiveIntegerField(default=0)),
                ("error_details", models.JSONField(blank=True, default=list)),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="import_jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "verbose_name": "Import Job",
                "verbose_name_plural": "Import Jobs",
                "ordering": ["-created_at"],
            },
        ),
    ]
