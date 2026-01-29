# Generated migration for P5.2: CAB Workflow Gates
# SPDX-License-Identifier: Apache-2.0

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('cab_workflow', '0004_cabapproval_cab_workflo_decisio_29d224_idx_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='CABApprovalRequest',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('deployment_intent_id', models.CharField(help_text='Correlation to deployment intent', max_length=255)),
                ('correlation_id', models.CharField(help_text='Unique identifier for audit trail', max_length=255, unique=True)),
                ('evidence_package_id', models.CharField(help_text='ID of associated evidence package', max_length=255)),
                ('risk_score', models.DecimalField(decimal_places=2, help_text='Risk score from evidence package (0-100)', max_digits=5)),
                ('submitted_at', models.DateTimeField(auto_now_add=True)),
                ('status', models.CharField(choices=[('submitted', 'Submitted for Review'), ('auto_approved', 'Auto-Approved (Low Risk)'), ('under_review', 'Under CAB Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('conditional', 'Conditionally Approved'), ('exception_required', 'Exception Required (Risk > 75)')], default='submitted', max_length=50)),
                ('approval_decision', models.CharField(blank=True, choices=[('approved', 'Approved'), ('rejected', 'Rejected'), ('conditional', 'Conditionally Approved')], max_length=50, null=True)),
                ('approval_rationale', models.TextField(blank=True, help_text='Reason for approval/rejection decision')),
                ('approval_conditions', models.JSONField(default=dict, help_text='Conditions if conditionally approved')),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('notes', models.TextField(blank=True, help_text='Additional notes from submitter')),
                ('approved_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='cab_decisions', to=settings.AUTH_USER_MODEL)),
                ('submitted_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cab_submissions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'CAB Approval Request',
                'verbose_name_plural': 'CAB Approval Requests',
                'db_table': 'cab_workflow_cabaprovalrequest',
                'ordering': ['-submitted_at'],
            },
        ),
        migrations.CreateModel(
            name='CABException',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('deployment_intent_id', models.CharField(help_text='What exception applies to', max_length=255)),
                ('correlation_id', models.CharField(help_text='Unique identifier for audit trail', max_length=255, unique=True)),
                ('reason', models.TextField(help_text='Why exception is needed')),
                ('risk_justification', models.TextField(help_text='Why risk is acceptable despite threshold')),
                ('compensating_controls', models.JSONField(default=list, help_text="List of compensating controls (e.g., ['Additional monitoring', 'Rollback plan'])")),
                ('requested_at', models.DateTimeField(auto_now_add=True)),
                ('approval_decision', models.CharField(blank=True, choices=[('approved', 'Approved'), ('rejected', 'Rejected')], max_length=50, null=True)),
                ('approval_rationale', models.TextField(blank=True, help_text='Security Reviewer rationale')),
                ('approved_at', models.DateTimeField(blank=True, null=True)),
                ('expires_at', models.DateTimeField(help_text='Exception automatically expires (no permanent exceptions)')),
                ('status', models.CharField(choices=[('pending', 'Pending Security Review'), ('approved', 'Approved'), ('rejected', 'Rejected'), ('expired', 'Expired')], default='pending', max_length=50)),
                ('approved_by', models.ForeignKey(blank=True, help_text='Security Reviewer who approved', null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='exception_approvals', to=settings.AUTH_USER_MODEL)),
                ('requested_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='exception_requests', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'CAB Exception',
                'verbose_name_plural': 'CAB Exceptions',
                'db_table': 'cab_workflow_cabexception',
                'ordering': ['-requested_at'],
            },
        ),
        migrations.CreateModel(
            name='CABApprovalDecision',
            fields=[
                ('id', models.UUIDField(default=uuid.uuid4, primary_key=True, serialize=False)),
                ('cab_request_id', models.CharField(help_text='ID of CABApprovalRequest being decided', max_length=255)),
                ('correlation_id', models.CharField(help_text='Audit trail identifier', max_length=255)),
                ('decision', models.CharField(choices=[('approved', 'Approved'), ('rejected', 'Rejected'), ('conditional', 'Conditionally Approved')], max_length=50)),
                ('rationale', models.TextField(help_text='Why this decision was made')),
                ('decided_at', models.DateTimeField(auto_now_add=True)),
                ('conditions', models.JSONField(default=dict, help_text='Conditions if decision is conditional')),
                ('decided_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='cab_decisions_made', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'CAB Approval Decision',
                'verbose_name_plural': 'CAB Approval Decisions',
                'db_table': 'cab_workflow_cabapprovaldecision',
                'ordering': ['-decided_at'],
            },
        ),
        migrations.AddIndex(
            model_name='cabapprovalrequest',
            index=models.Index(fields=['deployment_intent_id', '-submitted_at'], name='cab_workflow_deploym_idx'),
        ),
        migrations.AddIndex(
            model_name='cabapprovalrequest',
            index=models.Index(fields=['status'], name='cab_workflow_status_idx'),
        ),
        migrations.AddIndex(
            model_name='cabapprovalrequest',
            index=models.Index(fields=['risk_score'], name='cab_workflow_risksco_idx'),
        ),
        migrations.AddIndex(
            model_name='cabexception',
            index=models.Index(fields=['deployment_intent_id', '-requested_at'], name='cab_workflow_deploym_idx2'),
        ),
        migrations.AddIndex(
            model_name='cabexception',
            index=models.Index(fields=['status', 'expires_at'], name='cab_workflow_status_idx2'),
        ),
        migrations.AddIndex(
            model_name='cabapprovaldecision',
            index=models.Index(fields=['cab_request_id', '-decided_at'], name='cab_workflow_cab_req_idx'),
        ),
        migrations.AddIndex(
            model_name='cabapprovaldecision',
            index=models.Index(fields=['decision', '-decided_at'], name='cab_workflow_decision_idx'),
        ),
    ]
