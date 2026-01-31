# E4: 1E DEX Platform Integration

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Version**: 1.0
**Date**: 2026-01-30
**Status**: Draft for Implementation
**Priority**: P2-High
**Dependencies**: E2 (Storage Configuration)

---

## Overview

Integrate with the [1E DEX Platform (TeamViewer DEX)](https://docs.1e.com/en/Content/home/home.htm) to provide real-time Digital Employee Experience (DEX) telemetry and Green IT metrics. The integration uses the 1E Consumer API with an abstraction layer supporting mock data for environments without 1E access.

---

## 1E Platform Background

### What is 1E DEX Platform?

The 1E DEX Platform (now part of TeamViewer) provides:
- **Digital Employee Experience** monitoring
- **Endpoint telemetry** collection
- **Device health** metrics
- **Boot time** performance tracking
- **Application performance** monitoring
- **Carbon footprint** estimation (Green IT)

### API Architecture

Based on the [1E SDK documentation](https://help.1e.com/SDK/en/overview.html):

- **API Type**: RESTful Consumer API
- **Endpoint**: `https://{1E-server}/Consumer/{request}`
- **Authentication**: Windows Authentication (NTLM) or Basic Auth over HTTPS
- **Data Format**: JSON

---

## Requirements

### Functional Requirements

1. **1E Connection Configuration**
   - Server URL configuration
   - Authentication method selection
   - Connection testing
   - Sync interval configuration

2. **DEX Data Sync**
   - Device DEX scores
   - Boot time metrics
   - Application responsiveness
   - User sentiment (if available)

3. **Green IT Data**
   - Carbon footprint per device
   - Power consumption estimates
   - Sustainability scoring

4. **Abstraction Layer**
   - Mock data provider for demo/dev environments
   - Seamless switching between mock and live
   - Consistent data model regardless of source

---

## Data Model

### Backend Models

```python
# backend/apps/integrations/dex/models.py

class DEXProvider(TimeStampedModel):
    """1E DEX Platform connection configuration."""

    class ProviderType(models.TextChoices):
        ONE_E = "1e", "1E DEX Platform"
        MOCK = "mock", "Mock Data Provider"

    class AuthMethod(models.TextChoices):
        NTLM = "ntlm", "Windows Authentication (NTLM)"
        BASIC = "basic", "Basic Authentication"
        API_KEY = "api_key", "API Key"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=128, default="1E DEX Platform")
    provider_type = models.CharField(max_length=16, choices=ProviderType.choices, default=ProviderType.MOCK)
    is_enabled = models.BooleanField(default=True)

    # 1E Connection
    server_url = models.URLField(blank=True, null=True)
    auth_method = models.CharField(max_length=16, choices=AuthMethod.choices, default=AuthMethod.BASIC)
    username = EncryptedCharField(max_length=256, blank=True)
    password = EncryptedCharField(max_length=256, blank=True)
    api_key = EncryptedCharField(max_length=256, blank=True)

    # Sync Configuration
    sync_interval_minutes = models.IntegerField(default=60)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=32, blank=True)
    last_sync_error = models.TextField(blank=True)

    # Data Retention
    retention_days = models.IntegerField(default=90)

    class Meta:
        verbose_name = "DEX Provider"


class DEXDeviceMetrics(TimeStampedModel):
    """Cached DEX metrics per device."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Device identification
    device_id = models.CharField(max_length=128, db_index=True)
    device_name = models.CharField(max_length=256)

    # Link to asset (if available)
    asset = models.ForeignKey(
        'evidence_store.Asset',
        on_delete=models.SET_NULL,
        null=True, blank=True,
        related_name='dex_metrics'
    )

    # DEX Scores
    dex_score = models.FloatField(null=True, blank=True)  # 0-10
    performance_score = models.FloatField(null=True, blank=True)
    stability_score = models.FloatField(null=True, blank=True)
    responsiveness_score = models.FloatField(null=True, blank=True)

    # Boot Metrics
    boot_time_seconds = models.IntegerField(null=True, blank=True)
    login_time_seconds = models.IntegerField(null=True, blank=True)

    # User Sentiment
    user_sentiment = models.CharField(max_length=32, blank=True)  # Positive, Neutral, Negative
    sentiment_score = models.FloatField(null=True, blank=True)  # -1 to 1

    # Green IT
    carbon_footprint_kg = models.FloatField(null=True, blank=True)  # Annual estimated kg CO2
    power_consumption_kwh = models.FloatField(null=True, blank=True)  # Monthly kWh

    # Metadata
    collected_at = models.DateTimeField()
    source = models.CharField(max_length=16, default="1e")  # 1e or mock

    class Meta:
        indexes = [
            models.Index(fields=['device_id', 'collected_at']),
            models.Index(fields=['asset', 'collected_at']),
        ]
        get_latest_by = 'collected_at'


class DEXAggregateMetrics(TimeStampedModel):
    """Aggregated DEX metrics for dashboards."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)

    # Aggregation period
    period_start = models.DateTimeField(db_index=True)
    period_end = models.DateTimeField()
    aggregation_type = models.CharField(max_length=16)  # hourly, daily, weekly

    # Device counts
    total_devices = models.IntegerField(default=0)
    devices_with_dex = models.IntegerField(default=0)

    # DEX Scores
    avg_dex_score = models.FloatField(null=True, blank=True)
    min_dex_score = models.FloatField(null=True, blank=True)
    max_dex_score = models.FloatField(null=True, blank=True)
    dex_score_std_dev = models.FloatField(null=True, blank=True)

    # Boot Time
    avg_boot_time = models.IntegerField(null=True, blank=True)
    p50_boot_time = models.IntegerField(null=True, blank=True)
    p95_boot_time = models.IntegerField(null=True, blank=True)

    # Sentiment Distribution
    positive_sentiment_count = models.IntegerField(default=0)
    neutral_sentiment_count = models.IntegerField(default=0)
    negative_sentiment_count = models.IntegerField(default=0)

    # Green IT
    total_carbon_kg = models.FloatField(null=True, blank=True)
    total_power_kwh = models.FloatField(null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['period_start', 'aggregation_type']),
        ]
```

---

## 1E API Client

### API Client Implementation

```python
# backend/apps/integrations/dex/clients/one_e_client.py

from typing import AsyncGenerator
import httpx
from httpx_ntlm import HttpNtlmAuth

class OneEAPIClient:
    """Client for 1E Consumer API."""

    def __init__(self, config: DEXProvider):
        self.config = config
        self.base_url = config.server_url.rstrip('/')
        self._client = None

    def _get_auth(self):
        if self.config.auth_method == DEXProvider.AuthMethod.NTLM:
            return HttpNtlmAuth(self.config.username, self.config.password)
        elif self.config.auth_method == DEXProvider.AuthMethod.BASIC:
            return httpx.BasicAuth(self.config.username, self.config.password)
        else:
            return None

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make authenticated request to 1E API."""
        async with httpx.AsyncClient(auth=self._get_auth()) as client:
            url = f"{self.base_url}/Consumer/{endpoint}"
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    async def get_devices(self, page: int = 1, page_size: int = 100) -> dict:
        """Get device list from 1E."""
        return await self._request(
            "GET",
            "Devices",
            params={"page": page, "pageSize": page_size}
        )

    async def get_device_metrics(self, device_id: str) -> dict:
        """Get DEX metrics for a specific device."""
        return await self._request("GET", f"Devices/{device_id}/Experience")

    async def get_experience_scores(
        self,
        start_date: str = None,
        end_date: str = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream experience scores for all devices."""
        page = 1
        while True:
            result = await self._request(
                "GET",
                "Experience/Scores",
                params={
                    "page": page,
                    "pageSize": 100,
                    "startDate": start_date,
                    "endDate": end_date,
                }
            )

            if not result.get("data"):
                break

            for device in result["data"]:
                yield device

            page += 1

    async def get_sustainability_metrics(self) -> dict:
        """Get Green IT / sustainability metrics."""
        return await self._request("GET", "Sustainability/Metrics")

    async def health_check(self) -> bool:
        """Check 1E API connectivity."""
        try:
            await self._request("GET", "System/Health")
            return True
        except Exception:
            return False
```

### Mock Data Provider

```python
# backend/apps/integrations/dex/clients/mock_client.py

import random
from datetime import datetime, timedelta

class MockDEXClient:
    """Mock DEX data provider for development/demo."""

    async def get_experience_scores(
        self,
        start_date: str = None,
        end_date: str = None,
    ) -> AsyncGenerator[dict, None]:
        """Generate mock DEX scores."""
        # Generate realistic mock data
        for i in range(500):  # 500 mock devices
            yield {
                "device_id": f"MOCK-DEV-{i:05d}",
                "device_name": f"Device-{i:05d}",
                "dex_score": round(random.uniform(5.0, 9.5), 2),
                "performance_score": round(random.uniform(5.0, 9.5), 2),
                "stability_score": round(random.uniform(6.0, 9.8), 2),
                "responsiveness_score": round(random.uniform(4.0, 9.0), 2),
                "boot_time_seconds": random.randint(15, 120),
                "login_time_seconds": random.randint(5, 45),
                "user_sentiment": random.choice(["Positive", "Neutral", "Negative"]),
                "sentiment_score": round(random.uniform(-1, 1), 2),
                "carbon_footprint_kg": round(random.uniform(50, 200), 1),
                "power_consumption_kwh": round(random.uniform(20, 80), 1),
                "collected_at": datetime.utcnow().isoformat(),
            }

    async def health_check(self) -> bool:
        return True
```

---

## Sync Service

```python
# backend/apps/integrations/dex/services/sync.py

from celery import shared_task

class DEXSyncService:
    """Service for syncing DEX data from 1E or mock provider."""

    def __init__(self, provider: DEXProvider):
        self.provider = provider
        self.client = self._get_client()

    def _get_client(self):
        if self.provider.provider_type == DEXProvider.ProviderType.ONE_E:
            return OneEAPIClient(self.provider)
        return MockDEXClient()

    async def sync(self) -> SyncResult:
        """Run full sync of DEX data."""
        start_time = datetime.utcnow()
        metrics_synced = 0
        errors = []

        try:
            async for device_data in self.client.get_experience_scores():
                try:
                    await self._upsert_device_metrics(device_data)
                    metrics_synced += 1
                except Exception as e:
                    errors.append(f"Device {device_data.get('device_id')}: {str(e)}")

            # Update aggregate metrics
            await self._update_aggregates()

            # Update sync status
            self.provider.last_sync_at = datetime.utcnow()
            self.provider.last_sync_status = "success"
            self.provider.last_sync_error = ""
            await self.provider.asave()

        except Exception as e:
            self.provider.last_sync_status = "failed"
            self.provider.last_sync_error = str(e)
            await self.provider.asave()
            raise

        return SyncResult(
            duration=datetime.utcnow() - start_time,
            metrics_synced=metrics_synced,
            errors=errors,
        )

    async def _upsert_device_metrics(self, data: dict):
        """Create or update device metrics."""
        await DEXDeviceMetrics.objects.aupdate_or_create(
            device_id=data['device_id'],
            defaults={
                'device_name': data.get('device_name', ''),
                'dex_score': data.get('dex_score'),
                'performance_score': data.get('performance_score'),
                'stability_score': data.get('stability_score'),
                'responsiveness_score': data.get('responsiveness_score'),
                'boot_time_seconds': data.get('boot_time_seconds'),
                'login_time_seconds': data.get('login_time_seconds'),
                'user_sentiment': data.get('user_sentiment', ''),
                'sentiment_score': data.get('sentiment_score'),
                'carbon_footprint_kg': data.get('carbon_footprint_kg'),
                'power_consumption_kwh': data.get('power_consumption_kwh'),
                'collected_at': data.get('collected_at', datetime.utcnow()),
                'source': self.provider.provider_type,
            }
        )


@shared_task
def sync_dex_data():
    """Celery task to sync DEX data."""
    provider = DEXProvider.objects.filter(is_enabled=True).first()
    if not provider:
        return

    service = DEXSyncService(provider)
    asyncio.run(service.sync())
```

---

## API Endpoints

```python
# backend/apps/integrations/dex/urls.py

# Provider Configuration
GET    /api/v1/dex/provider/                    # Get DEX provider config
PUT    /api/v1/dex/provider/                    # Update provider config
POST   /api/v1/dex/provider/test/               # Test connection
POST   /api/v1/dex/provider/sync/               # Trigger manual sync

# DEX Data
GET    /api/v1/dex/metrics/                     # Get device DEX metrics
GET    /api/v1/dex/metrics/{device_id}/         # Get specific device metrics
GET    /api/v1/dex/aggregates/                  # Get aggregate metrics
GET    /api/v1/dex/dashboard/                   # Dashboard summary data

# Green IT
GET    /api/v1/dex/green-it/summary/            # Green IT summary
GET    /api/v1/dex/green-it/trends/             # Carbon footprint trends
```

---

## Enhanced DEX Dashboard

### Frontend Components

```tsx
// frontend/src/routes/DEXDashboard.tsx

Enhanced features:
1. Real-time DEX score with trend indicator
2. Boot time distribution histogram
3. Sentiment pie chart with drill-down
4. Green IT carbon footprint tracking
5. Device health heatmap
6. Top/bottom performers table
7. Trend analysis (7d, 30d, 90d)
8. Export to CSV/PDF
```

### Dashboard Widgets

```tsx
// New widgets for DEX Dashboard

1. DEXScoreGauge
   - Animated gauge showing average DEX score
   - Trend indicator (up/down/stable)
   - Industry benchmark comparison

2. BootTimeHistogram
   - Distribution of boot times
   - Color-coded by performance tier
   - P50/P95 markers

3. SentimentBreakdown
   - Pie chart with positive/neutral/negative
   - Trend over time
   - Drill-down to individual responses

4. GreenITSummary
   - Total carbon footprint
   - Power consumption
   - Year-over-year comparison
   - Sustainability score

5. DeviceHealthMap
   - Grid visualization of device health
   - Color-coded by DEX score
   - Click to see device details

6. PerformanceTrends
   - Line chart over time
   - Multiple metrics overlay
   - Anomaly detection markers
```

---

## Configuration UI

### Settings Integration Tab Update

```tsx
// Add to IntegrationsTab.tsx

<IntegrationCard
  name="1E DEX Platform"
  description="Digital Employee Experience monitoring and Green IT metrics"
  icon={<MonitorCheck />}
  status={dexProvider?.last_sync_status}
  lastSync={dexProvider?.last_sync_at}
>
  <Form onSubmit={handleSave}>
    <Select name="provider_type" label="Provider Type">
      <SelectItem value="1e">1E DEX Platform</SelectItem>
      <SelectItem value="mock">Mock Data (Demo)</SelectItem>
    </Select>

    {providerType === '1e' && (
      <>
        <Input name="server_url" label="1E Server URL" />
        <Select name="auth_method" label="Authentication">
          <SelectItem value="ntlm">Windows (NTLM)</SelectItem>
          <SelectItem value="basic">Basic Auth</SelectItem>
        </Select>
        <Input name="username" label="Username" />
        <Input name="password" label="Password" type="password" />
        <Input name="sync_interval" label="Sync Interval (minutes)" type="number" />
      </>
    )}

    <div className="flex gap-2">
      <Button type="button" variant="outline" onClick={testConnection}>
        Test Connection
      </Button>
      <Button type="submit">Save Configuration</Button>
    </div>
  </Form>
</IntegrationCard>
```

---

## Deliverables

1. `backend/apps/integrations/dex/` Django app with 1E client
2. Mock data provider for demo environments
3. Enhanced DEX Dashboard with Green IT metrics
4. Settings integration tab for 1E configuration
5. Celery task for periodic sync
6. API documentation in `docs/api/dex-api.yaml`
7. Integration guide in `docs/runbooks/1e-integration.md`
