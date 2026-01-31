---
name: one-e-dex-integration
description: 1E DEX Platform (TeamViewer DEX) integration for Digital Employee Experience metrics, boot time monitoring, user sentiment, and Green IT carbon footprint tracking. Use when implementing DEX dashboards, syncing 1E data, or tracking sustainability metrics.
status: ✅ Working
last-validated: 2026-01-30
---

# 1E DEX Platform Integration

Digital Employee Experience and Green IT integration for EUCORA.

---

## Quick Reference

| Feature | Metric | API Endpoint |
|---------|--------|--------------|
| DEX Score | 0-10 scale | `/Consumer/Experience/Scores` |
| Boot Time | Seconds | `/Consumer/Devices/{id}/BootMetrics` |
| User Sentiment | Positive/Neutral/Negative | `/Consumer/Experience/Sentiment` |
| Carbon Footprint | kg CO2 annual | `/Consumer/Sustainability/Metrics` |

---

## 1E Platform Overview

The 1E DEX Platform (now TeamViewer DEX) provides:
- **Digital Employee Experience** monitoring
- **Endpoint telemetry** collection
- **Device health** metrics
- **Boot time** performance tracking
- **Application performance** monitoring
- **Carbon footprint** estimation (Green IT)

### API Authentication

```python
# 1E supports NTLM or Basic Auth
auth_methods = {
    "ntlm": HttpNtlmAuth(username, password),  # Windows environments
    "basic": httpx.BasicAuth(username, password),  # Over HTTPS
}
```

---

## Data Models

### Provider Configuration

```python
# backend/apps/integrations/dex/models.py

class DEXProvider(TimeStampedModel):
    """1E DEX Platform connection configuration."""

    class ProviderType(models.TextChoices):
        ONE_E = "1e", "1E DEX Platform"
        MOCK = "mock", "Mock Data (Demo)"

    class AuthMethod(models.TextChoices):
        NTLM = "ntlm", "Windows Authentication (NTLM)"
        BASIC = "basic", "Basic Authentication"

    name = models.CharField(max_length=128, default="1E DEX Platform")
    provider_type = models.CharField(
        max_length=16,
        choices=ProviderType.choices,
        default=ProviderType.MOCK,
    )
    is_enabled = models.BooleanField(default=True)

    # Connection
    server_url = models.URLField(blank=True, null=True)
    auth_method = models.CharField(
        max_length=16,
        choices=AuthMethod.choices,
        default=AuthMethod.BASIC,
    )
    username = EncryptedCharField(max_length=256, blank=True)
    password = EncryptedCharField(max_length=256, blank=True)

    # Sync Configuration
    sync_interval_minutes = models.IntegerField(default=60)
    last_sync_at = models.DateTimeField(null=True)
    last_sync_status = models.CharField(max_length=32, blank=True)

    # Data Retention
    retention_days = models.IntegerField(default=90)
```

### Device Metrics

```python
class DEXDeviceMetrics(TimeStampedModel):
    """DEX metrics per device."""

    device_id = models.CharField(max_length=128, db_index=True)
    device_name = models.CharField(max_length=256)

    # Link to asset
    asset = models.ForeignKey(
        'evidence_store.Asset',
        on_delete=models.SET_NULL,
        null=True, blank=True,
    )

    # DEX Scores (0-10 scale)
    dex_score = models.FloatField(null=True)
    performance_score = models.FloatField(null=True)
    stability_score = models.FloatField(null=True)
    responsiveness_score = models.FloatField(null=True)

    # Boot Metrics
    boot_time_seconds = models.IntegerField(null=True)
    login_time_seconds = models.IntegerField(null=True)

    # User Sentiment
    user_sentiment = models.CharField(max_length=32, blank=True)
    sentiment_score = models.FloatField(null=True)  # -1 to 1

    # Green IT
    carbon_footprint_kg = models.FloatField(null=True)  # Annual kg CO2
    power_consumption_kwh = models.FloatField(null=True)  # Monthly kWh

    # Metadata
    collected_at = models.DateTimeField()
    source = models.CharField(max_length=16, default="1e")

    class Meta:
        indexes = [
            models.Index(fields=['device_id', 'collected_at']),
        ]
```

### Aggregate Metrics

```python
class DEXAggregateMetrics(TimeStampedModel):
    """Aggregated DEX metrics for dashboards."""

    period_start = models.DateTimeField(db_index=True)
    period_end = models.DateTimeField()
    aggregation_type = models.CharField(max_length=16)  # hourly, daily, weekly

    # Device counts
    total_devices = models.IntegerField(default=0)
    devices_with_dex = models.IntegerField(default=0)

    # DEX Scores
    avg_dex_score = models.FloatField(null=True)
    min_dex_score = models.FloatField(null=True)
    max_dex_score = models.FloatField(null=True)

    # Boot Time
    avg_boot_time = models.IntegerField(null=True)
    p50_boot_time = models.IntegerField(null=True)
    p95_boot_time = models.IntegerField(null=True)

    # Sentiment Distribution
    positive_sentiment_count = models.IntegerField(default=0)
    neutral_sentiment_count = models.IntegerField(default=0)
    negative_sentiment_count = models.IntegerField(default=0)

    # Green IT
    total_carbon_kg = models.FloatField(null=True)
    total_power_kwh = models.FloatField(null=True)
```

---

## 1E API Client

### Client Implementation

```python
# backend/apps/integrations/dex/clients/one_e_client.py
import httpx
from httpx_ntlm import HttpNtlmAuth
from typing import AsyncGenerator

class OneEAPIClient:
    """Client for 1E Consumer API."""

    def __init__(self, config: DEXProvider):
        self.config = config
        self.base_url = config.server_url.rstrip('/')

    def _get_auth(self):
        if self.config.auth_method == DEXProvider.AuthMethod.NTLM:
            return HttpNtlmAuth(self.config.username, self.config.password)
        return httpx.BasicAuth(self.config.username, self.config.password)

    async def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        """Make authenticated request to 1E API."""
        async with httpx.AsyncClient(auth=self._get_auth()) as client:
            url = f"{self.base_url}/Consumer/{endpoint}"
            response = await client.request(method, url, **kwargs)
            response.raise_for_status()
            return response.json()

    async def get_devices(self, page: int = 1, page_size: int = 100) -> dict:
        """Get device list."""
        return await self._request(
            "GET", "Devices",
            params={"page": page, "pageSize": page_size}
        )

    async def get_experience_scores(
        self,
        start_date: str = None,
        end_date: str = None,
    ) -> AsyncGenerator[dict, None]:
        """Stream experience scores for all devices."""
        page = 1
        while True:
            result = await self._request(
                "GET", "Experience/Scores",
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
from datetime import datetime

class MockDEXClient:
    """Mock DEX data for development/demo environments."""

    async def get_experience_scores(self, **kwargs) -> AsyncGenerator[dict, None]:
        """Generate realistic mock DEX scores."""
        for i in range(500):
            yield {
                "device_id": f"MOCK-DEV-{i:05d}",
                "device_name": f"Device-{i:05d}",
                "dex_score": round(random.gauss(7.5, 1.5), 2),
                "performance_score": round(random.gauss(7.0, 1.5), 2),
                "stability_score": round(random.gauss(8.0, 1.0), 2),
                "responsiveness_score": round(random.gauss(6.5, 1.5), 2),
                "boot_time_seconds": random.randint(20, 90),
                "login_time_seconds": random.randint(5, 30),
                "user_sentiment": random.choices(
                    ["Positive", "Neutral", "Negative"],
                    weights=[0.6, 0.3, 0.1]
                )[0],
                "sentiment_score": round(random.uniform(-0.5, 1.0), 2),
                "carbon_footprint_kg": round(random.uniform(60, 180), 1),
                "power_consumption_kwh": round(random.uniform(25, 70), 1),
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
    """Sync DEX data from 1E or mock provider."""

    def __init__(self, provider: DEXProvider):
        self.provider = provider
        self.client = self._get_client()

    def _get_client(self):
        if self.provider.provider_type == DEXProvider.ProviderType.ONE_E:
            return OneEAPIClient(self.provider)
        return MockDEXClient()

    async def sync(self) -> dict:
        """Run full DEX data sync."""
        metrics_synced = 0
        errors = []

        try:
            async for device_data in self.client.get_experience_scores():
                try:
                    await self._upsert_device_metrics(device_data)
                    metrics_synced += 1
                except Exception as e:
                    errors.append(str(e))

            # Update aggregates
            await self._update_aggregates()

            # Update sync status
            self.provider.last_sync_at = timezone.now()
            self.provider.last_sync_status = "success"
            await self.provider.asave()

        except Exception as e:
            self.provider.last_sync_status = "failed"
            await self.provider.asave()
            raise

        return {"synced": metrics_synced, "errors": errors}

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
                'collected_at': data.get('collected_at', timezone.now()),
                'source': self.provider.provider_type,
            }
        )

@shared_task
def sync_dex_data():
    """Celery task to sync DEX data."""
    provider = DEXProvider.objects.filter(is_enabled=True).first()
    if provider:
        service = DEXSyncService(provider)
        asyncio.run(service.sync())
```

---

## Dashboard Metrics

### DEX Summary API

```python
# backend/apps/integrations/dex/views.py

@api_view(['GET'])
async def dex_dashboard(request):
    """Get DEX dashboard summary."""
    # Latest aggregate
    aggregate = await DEXAggregateMetrics.objects.filter(
        aggregation_type='daily'
    ).order_by('-period_start').afirst()

    if not aggregate:
        return Response({"error": "No data available"}, status=404)

    # Calculate trends
    previous = await DEXAggregateMetrics.objects.filter(
        aggregation_type='daily',
        period_start__lt=aggregate.period_start,
    ).order_by('-period_start').afirst()

    dex_trend = 0
    if previous and previous.avg_dex_score:
        dex_trend = aggregate.avg_dex_score - previous.avg_dex_score

    return Response({
        "summary": {
            "avg_dex_score": aggregate.avg_dex_score,
            "dex_trend": round(dex_trend, 2),
            "total_devices": aggregate.total_devices,
            "devices_with_dex": aggregate.devices_with_dex,
        },
        "boot_time": {
            "avg": aggregate.avg_boot_time,
            "p50": aggregate.p50_boot_time,
            "p95": aggregate.p95_boot_time,
        },
        "sentiment": {
            "positive": aggregate.positive_sentiment_count,
            "neutral": aggregate.neutral_sentiment_count,
            "negative": aggregate.negative_sentiment_count,
        },
        "green_it": {
            "total_carbon_kg": aggregate.total_carbon_kg,
            "total_power_kwh": aggregate.total_power_kwh,
        },
    })
```

---

## Frontend Dashboard

### DEX Dashboard Component

```tsx
// frontend/src/routes/DEXDashboard.tsx

export function DEXDashboard() {
  const { data, isLoading } = useQuery({
    queryKey: ['dex-dashboard'],
    queryFn: () => api.get('/api/v1/dex/dashboard/'),
  });

  if (isLoading) return <LoadingSpinner />;

  return (
    <div className="grid grid-cols-4 gap-4">
      {/* DEX Score Gauge */}
      <Card>
        <CardHeader>
          <CardTitle>DEX Score</CardTitle>
        </CardHeader>
        <CardContent>
          <DEXScoreGauge score={data.summary.avg_dex_score} />
          <TrendIndicator value={data.summary.dex_trend} />
        </CardContent>
      </Card>

      {/* Boot Time */}
      <Card>
        <CardHeader>
          <CardTitle>Boot Time</CardTitle>
        </CardHeader>
        <CardContent>
          <BootTimeHistogram
            avg={data.boot_time.avg}
            p50={data.boot_time.p50}
            p95={data.boot_time.p95}
          />
        </CardContent>
      </Card>

      {/* Sentiment */}
      <Card>
        <CardHeader>
          <CardTitle>User Sentiment</CardTitle>
        </CardHeader>
        <CardContent>
          <SentimentPieChart
            positive={data.sentiment.positive}
            neutral={data.sentiment.neutral}
            negative={data.sentiment.negative}
          />
        </CardContent>
      </Card>

      {/* Green IT */}
      <Card>
        <CardHeader>
          <CardTitle>Green IT</CardTitle>
        </CardHeader>
        <CardContent>
          <GreenITSummary
            carbonKg={data.green_it.total_carbon_kg}
            powerKwh={data.green_it.total_power_kwh}
          />
        </CardContent>
      </Card>
    </div>
  );
}
```

---

## API Endpoints

```python
# Provider Configuration
GET    /api/v1/dex/provider/                    # Get config
PUT    /api/v1/dex/provider/                    # Update config
POST   /api/v1/dex/provider/test/               # Test connection
POST   /api/v1/dex/provider/sync/               # Manual sync

# DEX Data
GET    /api/v1/dex/metrics/                     # Device metrics
GET    /api/v1/dex/metrics/{device_id}/         # Specific device
GET    /api/v1/dex/aggregates/                  # Aggregate metrics
GET    /api/v1/dex/dashboard/                   # Dashboard summary

# Green IT
GET    /api/v1/dex/green-it/summary/            # Green IT summary
GET    /api/v1/dex/green-it/trends/             # Carbon trends
```

---

## Checklist

### Setup

```
☐ 1E server URL configured
☐ Authentication method selected (NTLM/Basic)
☐ Credentials stored in vault
☐ Sync interval configured
☐ Mock mode tested for development
```

### Data Quality

```
☐ DEX scores syncing correctly
☐ Boot time metrics populated
☐ Sentiment data captured
☐ Green IT metrics available
☐ Aggregates computing properly
```

### Dashboard

```
☐ DEX score gauge working
☐ Boot time histogram rendering
☐ Sentiment breakdown showing
☐ Carbon footprint displayed
☐ Trend indicators accurate
```

---

## Anti-Patterns

| ❌ FORBIDDEN | ✅ CORRECT |
|--------------|------------|
| Hardcoded credentials | Use encrypted fields / vault |
| Syncing without pagination | Use paginated API calls |
| No mock provider | Always have mock for development |
| Full refresh every sync | Incremental where possible |
| Missing error handling | Handle API errors gracefully |
