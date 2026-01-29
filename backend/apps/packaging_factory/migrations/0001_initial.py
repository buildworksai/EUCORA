# Generated manually for P8 Packaging Factory
import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="PackagingPipeline",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("package_name", models.CharField(db_index=True, max_length=255)),
                ("package_version", models.CharField(max_length=100)),
                (
                    "platform",
                    models.CharField(
                        choices=[("windows", "Windows"), ("macos", "macOS"), ("linux", "Linux")],
                        db_index=True,
                        max_length=20,
                    ),
                ),
                (
                    "package_type",
                    models.CharField(
                        choices=[
                            ("MSI", "MSI Installer"),
                            ("MSIX", "MSIX Package"),
                            ("EXE", "Executable"),
                            ("PKG", "macOS Package"),
                            ("DMG", "macOS Disk Image"),
                            ("DEB", "Debian Package"),
                            ("RPM", "RPM Package"),
                        ],
                        max_length=20,
                    ),
                ),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("PENDING", "Pending"),
                            ("INTAKE", "Intake"),
                            ("BUILD", "Build"),
                            ("SIGN", "Sign"),
                            ("SBOM", "SBOM Generation"),
                            ("SCAN", "Vulnerability Scan"),
                            ("POLICY", "Policy Decision"),
                            ("STORE", "Store"),
                            ("COMPLETED", "Completed"),
                            ("FAILED", "Failed"),
                        ],
                        db_index=True,
                        default="PENDING",
                        max_length=20,
                    ),
                ),
                ("current_stage", models.CharField(blank=True, max_length=50, null=True)),
                ("source_artifact_url", models.URLField(max_length=1000)),
                ("source_artifact_hash", models.CharField(max_length=64)),
                ("output_artifact_url", models.URLField(blank=True, max_length=1000, null=True)),
                ("output_artifact_hash", models.CharField(blank=True, max_length=64, null=True)),
                ("sbom_format", models.CharField(blank=True, max_length=50, null=True)),
                ("sbom_url", models.URLField(blank=True, max_length=1000, null=True)),
                ("sbom_generated_at", models.DateTimeField(blank=True, null=True)),
                ("scan_tool", models.CharField(blank=True, max_length=100, null=True)),
                ("scan_results", models.JSONField(blank=True, default=dict)),
                ("scan_completed_at", models.DateTimeField(blank=True, null=True)),
                ("critical_count", models.IntegerField(default=0)),
                ("high_count", models.IntegerField(default=0)),
                ("medium_count", models.IntegerField(default=0)),
                ("low_count", models.IntegerField(default=0)),
                (
                    "policy_decision",
                    models.CharField(
                        blank=True,
                        choices=[
                            ("PASS", "Pass - No blocking issues"),
                            ("FAIL", "Fail - Blocking vulnerabilities found"),
                            ("EXCEPTION", "Exception - Approved with compensating controls"),
                        ],
                        max_length=20,
                        null=True,
                    ),
                ),
                ("policy_reason", models.TextField(blank=True, null=True)),
                ("exception_id", models.UUIDField(blank=True, null=True)),
                ("signing_certificate", models.CharField(blank=True, max_length=255, null=True)),
                ("signature_url", models.URLField(blank=True, max_length=1000, null=True)),
                ("signed_at", models.DateTimeField(blank=True, null=True)),
                ("build_id", models.CharField(blank=True, max_length=255, null=True)),
                ("builder_identity", models.CharField(blank=True, max_length=255, null=True)),
                ("source_repo", models.URLField(blank=True, max_length=1000, null=True)),
                ("source_commit", models.CharField(blank=True, max_length=40, null=True)),
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("error_stage", models.CharField(blank=True, max_length=50, null=True)),
                ("correlation_id", models.CharField(blank=True, db_index=True, max_length=255, null=True)),
                (
                    "created_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT,
                        related_name="packaging_pipelines",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
            options={
                "db_table": "packaging_pipeline",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="PackagingStageLog",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("stage_name", models.CharField(db_index=True, max_length=50)),
                ("status", models.CharField(max_length=20)),
                ("started_at", models.DateTimeField(default=django.utils.timezone.now)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("output", models.TextField(blank=True, null=True)),
                ("error_message", models.TextField(blank=True, null=True)),
                ("metadata", models.JSONField(blank=True, default=dict)),
                (
                    "pipeline",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="stage_logs",
                        to="packaging_factory.packagingpipeline",
                    ),
                ),
            ],
            options={
                "db_table": "packaging_stage_log",
                "ordering": ["started_at"],
            },
        ),
        migrations.AddIndex(
            model_name="packagingpipeline",
            index=models.Index(fields=["package_name", "package_version"], name="packaging_p_package_idx"),
        ),
        migrations.AddIndex(
            model_name="packagingpipeline",
            index=models.Index(fields=["status", "created_at"], name="packaging_p_status_idx"),
        ),
        migrations.AddIndex(
            model_name="packagingpipeline",
            index=models.Index(fields=["policy_decision"], name="packaging_p_policy_idx"),
        ),
        migrations.AddIndex(
            model_name="packagingstagelog",
            index=models.Index(fields=["pipeline", "stage_name"], name="packaging_s_pipeline_idx"),
        ),
    ]
