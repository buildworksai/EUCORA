# Generated manually to add reconciliation engine models
# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("connectors", "0002_add_is_demo"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="ConnectorInstance",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "connector_type",
                    models.CharField(
                        choices=[
                            ("intune", "Microsoft Intune"),
                            ("jamf", "Jamf Pro"),
                            ("sccm", "Microsoft SCCM"),
                            ("landscape", "Canonical Landscape"),
                            ("ansible", "Ansible/AWX"),
                            ("entra", "Microsoft Entra ID"),
                        ],
                        db_index=True,
                        help_text="Type of connector",
                        max_length=20,
                    ),
                ),
                ("name", models.CharField(help_text="Display name for this instance", max_length=255)),
                ("description", models.TextField(blank=True, help_text="Instance description")),
                (
                    "config_encrypted",
                    models.BinaryField(blank=True, help_text="Encrypted configuration/credentials", null=True),
                ),
                (
                    "config_schema_version",
                    models.CharField(default="1.0", help_text="Schema version for config", max_length=20),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("active", "Active"),
                            ("inactive", "Inactive"),
                            ("error", "Error"),
                            ("maintenance", "Maintenance"),
                        ],
                        db_index=True,
                        default="inactive",
                        max_length=20,
                    ),
                ),
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
                ("health_message", models.TextField(blank=True, help_text="Last health check message")),
                ("health_checked_at", models.DateTimeField(blank=True, null=True)),
                ("last_sync_at", models.DateTimeField(blank=True, help_text="Last successful sync", null=True)),
                ("last_sync_status", models.CharField(blank=True, max_length=20)),
                ("next_sync_at", models.DateTimeField(blank=True, help_text="Scheduled next sync", null=True)),
                ("sync_interval_minutes", models.IntegerField(default=60, help_text="Sync interval in minutes")),
                ("auto_sync_enabled", models.BooleanField(default=True, help_text="Enable automatic sync")),
                (
                    "auto_remediate",
                    models.BooleanField(default=False, help_text="Automatically remediate drift (R1 only)"),
                ),
                (
                    "scope_filter",
                    models.JSONField(blank=True, default=dict, help_text="Scope filter for this connector"),
                ),
                ("is_demo", models.BooleanField(db_index=True, default=False)),
                (
                    "created_by",
                    models.ForeignKey(
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="created_connectors",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "connector_instance",
                "ordering": ["connector_type", "name"],
            },
        ),
        migrations.CreateModel(
            name="SyncJob",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "correlation_id",
                    models.CharField(db_index=True, help_text="Correlation ID for tracing", max_length=100),
                ),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "job_type",
                    models.CharField(
                        choices=[
                            ("full_sync", "Full Sync"),
                            ("delta_sync", "Delta Sync"),
                            ("push", "Push to Execution Plane"),
                            ("reconcile", "Reconciliation"),
                        ],
                        db_index=True,
                        help_text="Type of sync operation",
                        max_length=20,
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
                            ("cancelled", "Cancelled"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("total_records", models.IntegerField(default=0, help_text="Total records to process")),
                ("records_processed", models.IntegerField(default=0, help_text="Records processed so far")),
                ("records_created", models.IntegerField(default=0)),
                ("records_updated", models.IntegerField(default=0)),
                ("records_deleted", models.IntegerField(default=0)),
                ("records_failed", models.IntegerField(default=0)),
                ("errors", models.JSONField(blank=True, default=list, help_text="List of errors")),
                ("warnings", models.JSONField(blank=True, default=list, help_text="List of warnings")),
                ("summary", models.JSONField(blank=True, default=dict, help_text="Job summary")),
                ("drift_events_created", models.IntegerField(default=0, help_text="New drift events detected")),
                (
                    "trigger_type",
                    models.CharField(
                        default="manual", help_text="How job was triggered (manual, scheduled, webhook)", max_length=20
                    ),
                ),
                (
                    "connector",
                    models.ForeignKey(
                        help_text="Connector instance",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sync_jobs",
                        to="connectors.connectorinstance",
                    ),
                ),
                (
                    "triggered_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="triggered_sync_jobs",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "connector_sync_job",
                "ordering": ["-started_at"],
            },
        ),
        migrations.CreateModel(
            name="DriftEvent",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "entity_type",
                    models.CharField(
                        db_index=True, help_text="Type of entity (app, assignment, policy, device)", max_length=50
                    ),
                ),
                ("entity_id", models.CharField(db_index=True, help_text="Entity identifier", max_length=255)),
                ("entity_name", models.CharField(blank=True, help_text="Entity display name", max_length=255)),
                (
                    "drift_type",
                    models.CharField(
                        choices=[
                            ("missing", "Missing in Execution Plane"),
                            ("extra", "Extra in Execution Plane"),
                            ("modified", "Modified"),
                            ("stale", "Stale Data"),
                        ],
                        db_index=True,
                        help_text="Type of drift",
                        max_length=20,
                    ),
                ),
                ("desired_state", models.JSONField(help_text="Expected/desired state")),
                ("actual_state", models.JSONField(help_text="Actual state in execution plane")),
                ("diff_summary", models.JSONField(blank=True, default=dict, help_text="Summary of differences")),
                ("detected_at", models.DateTimeField(auto_now_add=True, db_index=True)),
                ("last_seen_at", models.DateTimeField(auto_now=True)),
                (
                    "remediation_status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("in_progress", "In Progress"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("skipped", "Skipped"),
                            ("requires_approval", "Requires Approval"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=20,
                    ),
                ),
                ("remediation_attempts", models.IntegerField(default=0)),
                ("last_remediation_at", models.DateTimeField(blank=True, null=True)),
                ("remediation_error", models.TextField(blank=True)),
                ("resolved_at", models.DateTimeField(blank=True, db_index=True, null=True)),
                ("resolution_notes", models.TextField(blank=True)),
                (
                    "severity",
                    models.CharField(
                        default="medium", help_text="Drift severity (low, medium, high, critical)", max_length=20
                    ),
                ),
                (
                    "requires_cab_approval",
                    models.BooleanField(default=False, help_text="Requires CAB approval for remediation"),
                ),
                (
                    "connector",
                    models.ForeignKey(
                        help_text="Connector instance",
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="drift_events",
                        to="connectors.connectorinstance",
                    ),
                ),
                (
                    "resolved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="resolved_drift_events",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "sync_job",
                    models.ForeignKey(
                        blank=True,
                        help_text="Sync job that detected this drift",
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="drift_events",
                        to="connectors.syncjob",
                    ),
                ),
            ],
            options={
                "db_table": "connector_drift_event",
                "ordering": ["-detected_at"],
            },
        ),
        # Add indexes
        migrations.AddIndex(
            model_name="connectorinstance",
            index=models.Index(fields=["connector_type", "status"], name="connector_i_connect_idx"),
        ),
        migrations.AddIndex(
            model_name="connectorinstance",
            index=models.Index(fields=["health_status"], name="connector_i_health__idx"),
        ),
        migrations.AddIndex(
            model_name="connectorinstance",
            index=models.Index(fields=["next_sync_at"], name="connector_i_next_sy_idx"),
        ),
        migrations.AddIndex(
            model_name="syncjob",
            index=models.Index(fields=["connector", "status"], name="connector_s_connect_idx"),
        ),
        migrations.AddIndex(
            model_name="syncjob",
            index=models.Index(fields=["job_type", "status"], name="connector_s_job_typ_idx"),
        ),
        migrations.AddIndex(
            model_name="syncjob",
            index=models.Index(fields=["started_at"], name="connector_s_started_idx"),
        ),
        migrations.AddIndex(
            model_name="syncjob",
            index=models.Index(fields=["status", "started_at"], name="connector_s_status_idx"),
        ),
        migrations.AddIndex(
            model_name="driftevent",
            index=models.Index(fields=["connector", "drift_type"], name="connector_d_connect_idx"),
        ),
        migrations.AddIndex(
            model_name="driftevent",
            index=models.Index(fields=["entity_type", "entity_id"], name="connector_d_entity__idx"),
        ),
        migrations.AddIndex(
            model_name="driftevent",
            index=models.Index(fields=["remediation_status"], name="connector_d_remedia_idx"),
        ),
        migrations.AddIndex(
            model_name="driftevent",
            index=models.Index(fields=["detected_at"], name="connector_d_detecte_idx"),
        ),
        migrations.AddIndex(
            model_name="driftevent",
            index=models.Index(fields=["resolved_at"], name="connector_d_resolve_idx"),
        ),
        migrations.AddIndex(
            model_name="driftevent",
            index=models.Index(fields=["severity", "remediation_status"], name="connector_d_severit_idx"),
        ),
    ]
