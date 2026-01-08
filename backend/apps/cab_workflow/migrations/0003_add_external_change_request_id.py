# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Generated migration to add external_change_request_id to CABApproval

from django.db import migrations, models


def add_external_change_request_id_if_not_exists(apps, schema_editor):
    """Add external_change_request_id column if it doesn't exist."""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='cab_workflow_cabapproval' 
            AND column_name='external_change_request_id'
        """)
        if not cursor.fetchone():
            # Column doesn't exist, add it
            cursor.execute("""
                ALTER TABLE cab_workflow_cabapproval 
                ADD COLUMN external_change_request_id VARCHAR(255) NULL
            """)


def remove_external_change_request_id_if_exists(apps, schema_editor):
    """Remove external_change_request_id column if it exists."""
    db_alias = schema_editor.connection.alias
    with schema_editor.connection.cursor() as cursor:
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name='cab_workflow_cabapproval' 
            AND column_name='external_change_request_id'
        """)
        if cursor.fetchone():
            # Column exists, remove it
            cursor.execute("""
                ALTER TABLE cab_workflow_cabapproval 
                DROP COLUMN external_change_request_id
            """)


class Migration(migrations.Migration):

    dependencies = [
        ('cab_workflow', '0002_add_is_demo'),
    ]

    operations = [
        migrations.RunPython(
            add_external_change_request_id_if_not_exists,
            reverse_code=remove_external_change_request_id_if_exists,
        ),
    ]


