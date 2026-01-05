# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Evidence Store models for artifact management.
"""
from django.db import models
from apps.core.models import TimeStampedModel, CorrelationIdModel


class EvidencePack(TimeStampedModel, CorrelationIdModel):
    """
    Evidence pack with immutable artifact storage.
    """
    app_name = models.CharField(max_length=255)
    version = models.CharField(max_length=50)
    artifact_hash = models.CharField(max_length=64, help_text='SHA-256 hash of artifact')
    artifact_path = models.CharField(max_length=500, help_text='MinIO object path')
    sbom_data = models.JSONField(help_text='Software Bill of Materials (SPDX/CycloneDX)')
    vulnerability_scan_results = models.JSONField(help_text='Vulnerability scan results')
    rollback_plan = models.TextField(help_text='Rollback plan documentation')
    is_validated = models.BooleanField(default=False, help_text='Whether evidence pack is validated')
    
    class Meta:
        indexes = [
            models.Index(fields=['app_name', 'version']),
            models.Index(fields=['artifact_hash']),
        ]
        verbose_name = 'Evidence Pack'
        verbose_name_plural = 'Evidence Packs'
    
    def __str__(self):
        return f'{self.app_name} {self.version} - {self.artifact_hash[:8]}'
