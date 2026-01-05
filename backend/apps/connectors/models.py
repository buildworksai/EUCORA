# SPDX-License-Identifier: Apache-2.0
# Copyright (c) 2026 BuildWorks.AI
"""
Connectors models for asset inventory (CMDB).
"""
from django.db import models
from apps.core.models import TimeStampedModel


class Asset(TimeStampedModel):
    """
    Asset inventory model (CMDB).
    
    Represents devices managed by the endpoint management system.
    """
    class AssetType(models.TextChoices):
        LAPTOP = 'Laptop', 'Laptop'
        DESKTOP = 'Desktop', 'Desktop'
        VIRTUAL_MACHINE = 'Virtual Machine', 'Virtual Machine'
        MOBILE = 'Mobile', 'Mobile'
        SERVER = 'Server', 'Server'
    
    class Status(models.TextChoices):
        ACTIVE = 'Active', 'Active'
        INACTIVE = 'Inactive', 'Inactive'
        RETIRED = 'Retired', 'Retired'
        MAINTENANCE = 'Maintenance', 'Maintenance'
    
    class UserSentiment(models.TextChoices):
        POSITIVE = 'Positive', 'Positive'
        NEUTRAL = 'Neutral', 'Neutral'
        NEGATIVE = 'Negative', 'Negative'
    
    # Basic identification
    name = models.CharField(max_length=255, db_index=True, help_text='Device name/hostname')
    asset_id = models.CharField(max_length=100, unique=True, db_index=True, help_text='Unique asset identifier')
    serial_number = models.CharField(max_length=100, blank=True, db_index=True)
    
    # Classification
    type = models.CharField(max_length=20, choices=AssetType.choices, db_index=True)
    os = models.CharField(max_length=100, db_index=True, help_text='Operating system version')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE, db_index=True)
    
    # Location and ownership
    location = models.CharField(max_length=255, db_index=True, help_text='Physical or logical location')
    owner = models.CharField(max_length=255, db_index=True, help_text='Asset owner/assigned user')
    
    # Network
    ip_address = models.GenericIPAddressField(null=True, blank=True, db_index=True)
    
    # Security
    disk_encryption = models.BooleanField(default=False, help_text='Disk encryption enabled')
    firewall_enabled = models.BooleanField(default=True, help_text='Firewall enabled')
    
    # Compliance
    compliance_score = models.IntegerField(default=0, help_text='Compliance score (0-100)')
    last_checkin = models.DateTimeField(null=True, blank=True, db_index=True, help_text='Last check-in timestamp')
    
    # DEX & Green IT metrics
    dex_score = models.FloatField(null=True, blank=True, help_text='Digital Experience Score (0-10)')
    boot_time = models.IntegerField(null=True, blank=True, help_text='Boot time in seconds')
    carbon_footprint = models.FloatField(null=True, blank=True, help_text='Carbon footprint (kg CO2e per year)')
    user_sentiment = models.CharField(max_length=20, choices=UserSentiment.choices, null=True, blank=True)
    
    # Metadata
    connector_type = models.CharField(max_length=20, blank=True, help_text='Source connector (intune, jamf, sccm, landscape)')
    connector_object_id = models.CharField(max_length=255, blank=True, help_text='Platform-specific object ID')
    
    class Meta:
        indexes = [
            models.Index(fields=['type', 'status']),
            models.Index(fields=['os', 'status']),
            models.Index(fields=['location', 'status']),
            models.Index(fields=['owner', 'status']),
            models.Index(fields=['compliance_score']),
            models.Index(fields=['last_checkin']),
        ]
        ordering = ['-created_at']
        verbose_name = 'Asset'
        verbose_name_plural = 'Assets'
    
    def __str__(self):
        return f'{self.name} ({self.type}) - {self.status}'


class Application(TimeStampedModel):
    """
    Application catalog model.
    
    Represents applications that can be deployed.
    """
    class Platform(models.TextChoices):
        WINDOWS = 'Windows', 'Windows'
        MACOS = 'macOS', 'macOS'
        LINUX = 'Linux', 'Linux'
        MOBILE = 'Mobile', 'Mobile'
        MULTI_PLATFORM = 'Multi-Platform', 'Multi-Platform'
    
    class Category(models.TextChoices):
        PRODUCTIVITY = 'Productivity', 'Productivity'
        SECURITY = 'Security', 'Security'
        DEVELOPMENT = 'Development', 'Development'
        MEDIA = 'Media', 'Media'
        BROWSER = 'Browser', 'Browser'
        COMMUNICATION = 'Communication', 'Communication'
        UTILITY = 'Utility', 'Utility'
        ENTERPRISE = 'Enterprise', 'Enterprise'
    
    # Basic identification
    name = models.CharField(max_length=255, db_index=True)
    vendor = models.CharField(max_length=255, blank=True, db_index=True)
    version = models.CharField(max_length=50, db_index=True)
    
    # Classification
    platform = models.CharField(max_length=20, choices=Platform.choices, db_index=True)
    category = models.CharField(max_length=20, choices=Category.choices, default=Category.UTILITY, db_index=True)
    
    # Metadata
    description = models.TextField(blank=True)
    homepage_url = models.URLField(blank=True)
    license_type = models.CharField(max_length=100, blank=True)
    
    # Risk assessment
    default_risk_score = models.IntegerField(default=30, help_text='Default risk score (0-100)')
    
    class Meta:
        indexes = [
            models.Index(fields=['name', 'version']),
            models.Index(fields=['platform', 'category']),
            models.Index(fields=['vendor']),
        ]
        unique_together = [['name', 'version', 'platform']]
        ordering = ['name', 'version']
        verbose_name = 'Application'
        verbose_name_plural = 'Applications'
    
    def __str__(self):
        return f'{self.name} {self.version} ({self.platform})'
