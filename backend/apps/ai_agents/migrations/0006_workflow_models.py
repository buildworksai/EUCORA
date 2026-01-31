# Generated manually for E8: AI Agent Workflows
# SPDX-License-Identifier: Apache-2.0

import uuid

import django.db.models.deletion
import django.utils.timezone
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_agents", "0005_aimodel_agentexecution_modeldriftmetric_and_more"),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name="WorkflowDefinition",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                (
                    "agent_type",
                    models.CharField(
                        choices=[
                            ("amani", "Ask Amani (General Assistant)"),
                            ("packaging", "Packaging Assistant"),
                            ("cab_evidence", "CAB Evidence Generator"),
                            ("risk_explainer", "Risk Score Explainer"),
                            ("deployment", "Deployment Advisor"),
                            ("compliance", "Compliance Analyzer"),
                            ("incident", "Incident Responder"),
                        ],
                        db_index=True,
                        max_length=32,
                    ),
                ),
                ("name", models.CharField(max_length=128)),
                ("description", models.TextField()),
                ("steps", models.JSONField(default=list, help_text="List of step definitions")),
                (
                    "required_policies",
                    models.JSONField(
                        default=list, help_text="Policy categories to retrieve (e.g., ['application', 'security'])"
                    ),
                ),
                (
                    "risk_level",
                    models.CharField(
                        choices=[
                            ("R1", "R1 - Low Risk (Autonomous)"),
                            ("R2", "R2 - Medium Risk (Policy-Dependent)"),
                            ("R3", "R3 - High Risk (Mandatory Approval)"),
                        ],
                        db_index=True,
                        default="R2",
                        max_length=4,
                    ),
                ),
                ("is_active", models.BooleanField(db_index=True, default=True)),
            ],
            options={
                "verbose_name": "Workflow Definition",
                "verbose_name_plural": "Workflow Definitions",
            },
        ),
        migrations.CreateModel(
            name="WorkflowExecution",
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
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("input_data", models.JSONField(default=dict, help_text="Input data for workflow execution")),
                ("output_data", models.JSONField(default=dict, help_text="Final output data from workflow")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("awaiting_approval", "Awaiting Approval"),
                            ("approved", "Approved"),
                            ("rejected", "Rejected"),
                            ("completed", "Completed"),
                            ("failed", "Failed"),
                            ("cancelled", "Cancelled"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=32,
                    ),
                ),
                (
                    "current_step_index",
                    models.IntegerField(default=0, help_text="Index of current step being executed"),
                ),
                (
                    "policy_context",
                    models.JSONField(default=list, help_text="Retrieved policy chunks used in workflow execution"),
                ),
                ("approved_at", models.DateTimeField(blank=True, null=True)),
                ("rejection_reason", models.TextField(blank=True)),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "approved_by",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="approved_workflow_executions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "initiated_by",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="workflow_executions",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
                (
                    "workflow",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="executions",
                        to="ai_agents.workflowdefinition",
                    ),
                ),
            ],
            options={
                "verbose_name": "Workflow Execution",
                "verbose_name_plural": "Workflow Executions",
                "ordering": ["-created_at"],
            },
        ),
        migrations.CreateModel(
            name="WorkflowStep",
            fields=[
                ("created_at", models.DateTimeField(db_index=True, default=django.utils.timezone.now, editable=False)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("step_index", models.IntegerField(help_text="Index of this step in workflow definition")),
                ("name", models.CharField(max_length=128)),
                ("description", models.TextField()),
                (
                    "step_type",
                    models.CharField(
                        choices=[
                            ("ai_action", "AI Action"),
                            ("approval_gate", "Approval Gate"),
                            ("user_input", "User Input"),
                        ],
                        max_length=32,
                    ),
                ),
                ("input_data", models.JSONField(default=dict, help_text="Input data for this step")),
                ("output_data", models.JSONField(default=dict, help_text="Output data from this step")),
                (
                    "policies_considered",
                    models.JSONField(default=list, help_text="Policy chunks considered for this step"),
                ),
                ("prompt_used", models.TextField(blank=True, help_text="Prompt sent to LLM")),
                ("llm_response", models.TextField(blank=True, help_text="Response from LLM")),
                ("tokens_used", models.IntegerField(default=0, help_text="Tokens consumed")),
                (
                    "status",
                    models.CharField(
                        choices=[
                            ("pending", "Pending"),
                            ("running", "Running"),
                            ("awaiting_input", "Awaiting User Input"),
                            ("awaiting_approval", "Awaiting Approval"),
                            ("completed", "Completed"),
                            ("skipped", "Skipped"),
                            ("failed", "Failed"),
                        ],
                        db_index=True,
                        default="pending",
                        max_length=32,
                    ),
                ),
                ("error_message", models.TextField(blank=True, help_text="Error message if step failed")),
                ("started_at", models.DateTimeField(blank=True, null=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                (
                    "execution",
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="steps",
                        to="ai_agents.workflowexecution",
                    ),
                ),
            ],
            options={
                "verbose_name": "Workflow Step",
                "verbose_name_plural": "Workflow Steps",
                "ordering": ["step_index"],
            },
        ),
        migrations.AddIndex(
            model_name="workflowdefinition",
            index=models.Index(fields=["agent_type", "is_active"], name="ai_agents_w_agent_t_123abc_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowdefinition",
            index=models.Index(fields=["risk_level", "is_active"], name="ai_agents_w_risk_le_456def_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowexecution",
            index=models.Index(fields=["initiated_by", "created_at"], name="ai_agents_w_initiat_789ghi_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowexecution",
            index=models.Index(fields=["status", "created_at"], name="ai_agents_w_status__jklmno_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowexecution",
            index=models.Index(fields=["workflow", "status"], name="ai_agents_w_workflow_pqrstu_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowstep",
            index=models.Index(fields=["execution", "step_index"], name="ai_agents_w_executi_vwxyz1_idx"),
        ),
        migrations.AddIndex(
            model_name="workflowstep",
            index=models.Index(fields=["status", "created_at"], name="ai_agents_w_status__234567_idx"),
        ),
        migrations.AlterUniqueTogether(
            name="workflowstep",
            unique_together={("execution", "step_index")},
        ),
    ]
