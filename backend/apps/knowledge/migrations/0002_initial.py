# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Initial migration for Knowledge app.
"""
import uuid

import django.db.models.deletion
import django.utils.timezone
import pgvector.django
from django.conf import settings
from django.db import migrations, models

import apps.core.encryption


class Migration(migrations.Migration):
    """Initial migration."""

    initial = True

    dependencies = [
        ("knowledge", "0001_enable_pgvector"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("application_portfolio", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="EmbeddingConfig",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                (
                    "provider",
                    models.CharField(
                        choices=[
                            ("openai", "OpenAI"),
                            ("cohere", "Cohere"),
                            ("local", "Local (Sentence Transformers)"),
                        ],
                        max_length=32,
                    ),
                ),
                ("model_name", models.CharField(max_length=128)),
                ("dimensions", models.IntegerField()),
                ("api_key", apps.core.encryption.EncryptedCharField(blank=True, max_length=512)),
                ("api_endpoint", models.URLField(blank=True, null=True)),
                ("is_active", models.BooleanField(default=True)),
                ("is_default", models.BooleanField(default=False)),
            ],
            options={
                "verbose_name": "Embedding Configuration",
                "verbose_name_plural": "Embedding Configurations",
            },
        ),
        migrations.CreateModel(
            name="KnowledgeVector",
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
                (
                    "source_type",
                    models.CharField(
                        choices=[
                            ("policy_document", "Policy Document"),
                            ("deployment", "Deployment Record"),
                            ("cab_decision", "CAB Decision"),
                            ("incident", "Incident Report"),
                            ("runbook", "Operational Runbook"),
                            ("application", "Application Metadata"),
                            ("vulnerability", "Vulnerability Record"),
                        ],
                        max_length=64,
                    ),
                ),
                ("source_id", models.UUIDField()),
                ("source_chunk_index", models.IntegerField(default=0)),
                ("content", models.TextField()),
                ("content_hash", models.CharField(db_index=True, max_length=64)),
                ("embedding", pgvector.django.VectorField(dimensions=1536)),
                ("embedding_model", models.CharField(max_length=64)),
                ("category", models.CharField(blank=True, max_length=64)),
                ("tags", models.JSONField(default=list)),
                ("source_created_at", models.DateTimeField(blank=True, null=True)),
                (
                    "application",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        to="application_portfolio.application",
                    ),
                ),
            ],
            options={
                "verbose_name": "Knowledge Vector",
                "verbose_name_plural": "Knowledge Vectors",
            },
        ),
        migrations.AddConstraint(
            model_name="embeddingconfig",
            constraint=models.UniqueConstraint(
                condition=models.Q(("is_default", True)),
                fields=("is_default",),
                name="unique_default_embedding_config",
            ),
        ),
        migrations.AddIndex(
            model_name="knowledgevector",
            index=pgvector.django.HnswIndex(
                fields=["embedding"],
                m=16,
                ef_construction=64,
                name="knowledge_embedding_hnsw_idx",
                opclasses=["vector_cosine_ops"],
            ),
        ),
        migrations.AddIndex(
            model_name="knowledgevector",
            index=models.Index(fields=["source_type", "source_id"], name="knowledgevector_source_type_source_id_idx"),
        ),
        migrations.AddIndex(
            model_name="knowledgevector",
            index=models.Index(fields=["category"], name="knowledgevector_category_idx"),
        ),
        migrations.AddIndex(
            model_name="knowledgevector",
            index=models.Index(fields=["application"], name="knowledgevector_application_id_idx"),
        ),
    ]
