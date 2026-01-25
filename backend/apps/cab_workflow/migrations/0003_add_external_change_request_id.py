# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Generated migration to add external_change_request_id to CABApproval

from django.db import migrations, models


def add_external_change_request_id_if_not_exists(apps, schema_editor):
    """Add external_change_request_id column if it doesn't exist."""
    # Skip - this is handled by AddField operation in Django's migration framework
    # This function exists for backward compatibility with existing databases
    pass


def remove_external_change_request_id_if_exists(apps, schema_editor):
    """Remove external_change_request_id column if it exists."""
    # Skip - this is handled by RemoveField operation in Django's migration framework
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("cab_workflow", "0002_add_is_demo"),
    ]

    operations = [
        # Add field to Django's state tracking
        migrations.AddField(
            model_name="cabapproval",
            name="external_change_request_id",
            field=models.CharField(
                blank=True,
                help_text="External change request ID (ServiceNow CR, Jira issue key, etc.)",
                max_length=255,
                null=True,
            ),
        ),
    ]
