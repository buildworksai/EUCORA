# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Migration to fix Vendor.identifier unique constraint issue.

The previous default="" caused IntegrityError when creating multiple vendors
without explicit identifiers. This migration uses a callable default that
generates unique identifiers.

Also adds blank=True to ImportJob file fields for consistency.
"""
import uuid

from django.db import migrations, models


def generate_vendor_identifier():
    """Generate a unique vendor identifier using UUID."""
    return f"vendor-{uuid.uuid4().hex[:12]}"


class Migration(migrations.Migration):
    """Fix Vendor.identifier and ImportJob file field defaults."""

    dependencies = [
        ("license_management", "0003_alter_licensealert_detected_at"),
    ]

    operations = [
        # Fix Vendor.identifier to use callable default
        migrations.AlterField(
            model_name="vendor",
            name="identifier",
            field=models.CharField(
                db_index=True,
                default=generate_vendor_identifier,
                help_text="Unique vendor identifier (slug)",
                max_length=100,
                unique=True,
            ),
        ),
        # Add blank=True to ImportJob file fields
        migrations.AlterField(
            model_name="importjob",
            name="file_name",
            field=models.CharField(
                blank=True,
                default="",
                help_text="Original file name",
                max_length=255,
            ),
        ),
        migrations.AlterField(
            model_name="importjob",
            name="file_hash",
            field=models.CharField(
                blank=True,
                default="",
                help_text="SHA-256 of uploaded file",
                max_length=64,
            ),
        ),
        migrations.AlterField(
            model_name="importjob",
            name="file_ref",
            field=models.CharField(
                blank=True,
                default="",
                help_text="MinIO path to uploaded file",
                max_length=500,
            ),
        ),
    ]
