# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
# Generated migration for integrations app

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ExternalSystem',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('correlation_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True, help_text='Unique correlation ID for audit trail and tracing')),
                ('name', models.CharField(help_text='Display name for this integration', max_length=255)),
                ('type', models.CharField(choices=[('entra_id', 'Microsoft Entra ID'), ('active_directory', 'Active Directory'), ('servicenow_cmdb', 'ServiceNow CMDB'), ('jira_assets', 'Jira Assets'), ('freshservice_cmdb', 'Freshservice CMDB'), ('servicenow_itsm', 'ServiceNow ITSM'), ('jira_service_management', 'Jira Service Management'), ('freshservice_itsm', 'Freshservice ITSM'), ('apple_business_manager', 'Apple Business Manager'), ('android_enterprise', 'Android Enterprise'), ('datadog', 'Datadog'), ('splunk', 'Splunk'), ('elastic', 'Elastic (ELK Stack)'), ('trivy', 'Trivy'), ('grype', 'Grype'), ('snyk', 'Snyk'), ('defender_for_endpoint', 'Microsoft Defender for Endpoint')], help_text='Type of external system', max_length=50)),
                ('is_enabled', models.BooleanField(default=False, help_text='Whether this integration is active')),
                ('api_url', models.URLField(help_text='Base URL for the external system API')),
                ('auth_type', models.CharField(choices=[('oauth2', 'OAuth 2.0'), ('basic', 'Basic Authentication'), ('certificate', 'Certificate-based'), ('token', 'API Token'), ('server_token', 'Server Token (ABM)')], default='token', help_text='Authentication method', max_length=50)),
                ('credentials', models.JSONField(default=dict, help_text='Vault path reference for encrypted credentials (never store plaintext)')),
                ('sync_interval_minutes', models.IntegerField(default=60, help_text='How often to sync data from this system (in minutes)')),
                ('last_sync_at', models.DateTimeField(blank=True, help_text='Timestamp of last successful sync', null=True)),
                ('last_sync_status', models.CharField(blank=True, choices=[('success', 'Success'), ('failed', 'Failed'), ('partial', 'Partial'), ('running', 'Running')], help_text='Status of last sync operation', max_length=50, null=True)),
                ('metadata', models.JSONField(default=dict, help_text='System-specific configuration (field mappings, filters, etc.)')),
                ('is_demo', models.BooleanField(default=False, help_text='Whether this is demo/test integration data')),
            ],
            options={
                'verbose_name': 'External System Integration',
                'verbose_name_plural': 'External System Integrations',
                'db_table': 'integrations_external_system',
            },
        ),
        migrations.CreateModel(
            name='IntegrationSyncLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True, db_index=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('correlation_id', models.UUIDField(default=uuid.uuid4, editable=False, unique=True, db_index=True, help_text='Unique correlation ID for audit trail and tracing')),
                ('sync_started_at', models.DateTimeField(help_text='When the sync operation started')),
                ('sync_completed_at', models.DateTimeField(blank=True, help_text='When the sync operation completed', null=True)),
                ('status', models.CharField(choices=[('success', 'Success'), ('failed', 'Failed'), ('partial', 'Partial'), ('running', 'Running'), ('cancelled', 'Cancelled')], default='running', help_text='Final status of the sync operation', max_length=50)),
                ('records_fetched', models.IntegerField(default=0, help_text='Number of records fetched from external system')),
                ('records_created', models.IntegerField(default=0, help_text='Number of new records created in local database')),
                ('records_updated', models.IntegerField(default=0, help_text='Number of existing records updated in local database')),
                ('records_failed', models.IntegerField(default=0, help_text='Number of records that failed to sync')),
                ('error_message', models.TextField(blank=True, help_text='Error message if sync failed')),
                ('error_details', models.JSONField(default=dict, help_text='Detailed error information (stack trace, API response, etc.)')),
                ('duration_seconds', models.FloatField(blank=True, help_text='Sync duration in seconds', null=True)),
                ('system', models.ForeignKey(help_text='External system that was synced', on_delete=django.db.models.deletion.CASCADE, related_name='sync_logs', to='integrations.externalsystem')),
            ],
            options={
                'verbose_name': 'Integration Sync Log',
                'verbose_name_plural': 'Integration Sync Logs',
                'db_table': 'integrations_sync_log',
                'ordering': ['-sync_started_at'],
            },
        ),
        migrations.AddIndex(
            model_name='externalsystem',
            index=models.Index(fields=['type', 'is_enabled'], name='integrations_type_is_en_idx'),
        ),
        migrations.AddIndex(
            model_name='externalsystem',
            index=models.Index(fields=['last_sync_at'], name='integrations_last_syn_idx'),
        ),
        migrations.AddIndex(
            model_name='externalsystem',
            index=models.Index(fields=['is_demo'], name='integrations_is_demo_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationsynclog',
            index=models.Index(fields=['system', '-sync_started_at'], name='integrations_system_sync_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationsynclog',
            index=models.Index(fields=['status', '-sync_started_at'], name='integrations_status_sync_idx'),
        ),
        migrations.AddIndex(
            model_name='integrationsynclog',
            index=models.Index(fields=['correlation_id'], name='integrations_correlat_idx'),
        ),
    ]

