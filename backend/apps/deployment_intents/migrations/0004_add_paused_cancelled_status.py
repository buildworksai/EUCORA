# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Migration to add PAUSED and CANCELLED status choices to DeploymentIntent.

This migration adds proper status values for pausing and cancelling deployments,
replacing the incorrect reuse of REJECTED status for these operations.
"""
from django.db import migrations, models


class Migration(migrations.Migration):
    """Add PAUSED and CANCELLED status choices to DeploymentIntent."""

    dependencies = [
        ("deployment_intents", "0003_deploymentintent_risk_score_between_0_and_100_and_more"),
    ]

    operations = [
        migrations.AlterField(
            model_name="deploymentintent",
            name="status",
            field=models.CharField(
                choices=[
                    ("PENDING", "Pending"),
                    ("AWAITING_CAB", "Awaiting CAB Approval"),
                    ("APPROVED", "Approved"),
                    ("REJECTED", "Rejected"),
                    ("DEPLOYING", "Deploying"),
                    ("PAUSED", "Paused"),
                    ("COMPLETED", "Completed"),
                    ("FAILED", "Failed"),
                    ("CANCELLED", "Cancelled"),
                    ("ROLLED_BACK", "Rolled Back"),
                ],
                default="PENDING",
                help_text="Deployment status",
                max_length=20,
            ),
        ),
    ]
