# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Initial migration for Policy Documents app.
"""
import uuid

import django.db.models.deletion
import django.utils.timezone
import pgvector.django
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    """Initial migration."""

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("knowledge", "0002_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="DocumentCategory",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=128, unique=True)),
                (
                    "category_type",
                    models.CharField(
                        choices=[
                            ("compliance", "Compliance Policies"),
                            ("security", "Security Policies"),
                            ("operational", "Operational Policies"),
                            ("governance", "Governance Policies"),
                            ("application", "Application Policies"),
                            ("custom", "Custom Category"),
                        ],
                        max_length=32,
                    ),
                ),
                ("description", models.TextField(blank=True)),
                ("icon", models.CharField(blank=True, max_length=64)),
                ("color", models.CharField(blank=True, max_length=32)),
                ("is_system", models.BooleanField(default=False)),
                (
                    "created_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "verbose_name": "Document Category",
                "verbose_name_plural": "Document Categories",
            },
        ),
        migrations.CreateModel(
            name="PolicyDocument",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                (
                    "correlation_id",
                    models.UUIDField(
                        db_index=True,
                        default=uuid.uuid4,
                        editable=False,
                        help_text="Unique correlation ID for audit trail and tracing",
                        unique=True,
                    ),
                ),
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("title", models.CharField(max_length=256)),
                ("description", models.TextField(blank=True)),
                ("tags", models.JSONField(default=list)),
                ("file_name", models.CharField(max_length=256)),
                ("file_type", models.CharField(max_length=32)),
                ("file_size", models.BigIntegerField()),
                ("storage_path", models.CharField(max_length=512)),
                ("content_hash", models.CharField(db_index=True, max_length=64)),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("draft", "Draft"),
                            ("processing", "Processing"),
                            ("active", "Active"),
                            ("deprecated", "Deprecated"),
                            ("archived", "Archived"),
                            ("failed", "Processing Failed"),
                        ],
                        default="draft",
                        max_length=32,
                    ),
                ),
                ("processing_error", models.TextField(blank=True)),
                ("chunk_count", models.IntegerField(default=0)),
                ("version", models.IntegerField(default=1)),
                ("effective_date", models.DateField(blank=True, null=True)),
                ("review_date", models.DateField(blank=True, null=True)),
                ("author", models.CharField(blank=True, max_length=256)),
                (
                    "category",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.PROTECT, to="policy_documents.documentcategory"
                    ),
                ),
                (
                    "parent_document",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="versions",
                        to="policy_documents.policydocument",
                    ),
                ),
                (
                    "uploaded_by",
                    models.ForeignKey(
                        blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL
                    ),
                ),
            ],
            options={
                "verbose_name": "Policy Document",
                "verbose_name_plural": "Policy Documents",
            },
        ),
        migrations.CreateModel(
            name="DocumentChunk",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ("chunk_index", models.IntegerField()),
                ("content", models.TextField()),
                ("content_hash", models.CharField(max_length=64)),
                ("heading", models.CharField(blank=True, max_length=256)),
                ("page_number", models.IntegerField(blank=True, null=True)),
                ("start_char", models.IntegerField()),
                ("end_char", models.IntegerField()),
                ("embedding", pgvector.django.VectorField(dimensions=1536, null=True)),
                ("embedding_model", models.CharField(blank=True, max_length=64)),
                (
                    "document",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="chunks",
                        to="policy_documents.policydocument",
                    ),
                ),
            ],
            options={
                "verbose_name": "Document Chunk",
                "verbose_name_plural": "Document Chunks",
            },
        ),
        migrations.AddIndex(
            model_name="policydocument",
            index=models.Index(fields=["category", "status"], name="policydocum_categor_idx"),
        ),
        migrations.AddIndex(
            model_name="policydocument",
            index=models.Index(fields=["status", "created_at"], name="policydocum_status_created_idx"),
        ),
        migrations.AddIndex(
            model_name="documentchunk",
            index=models.Index(fields=["document", "chunk_index"], name="documentchu_document_chunk_idx"),
        ),
    ]
