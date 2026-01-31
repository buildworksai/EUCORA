---
name: observability-stack
description: Observability patterns for EUCORA including Prometheus metrics, Grafana dashboards, alerting rules, and structured logging. Use when configuring monitoring, creating dashboards, or implementing metrics collection.
status: ✅ Working
last-validated: 2026-01-30
---

# Observability Stack

Prometheus, Grafana, and logging patterns for EUCORA platform monitoring.

---

## Quick Reference

| Component | Purpose |
|-----------|---------|
| Prometheus | Metrics collection and alerting |
| Grafana | Visualization and dashboards |
| Django Metrics | `/api/v1/metrics/` endpoint |
| Structured Logging | JSON logs with correlation IDs |
| SIEM | Azure Sentinel / Splunk for security events |

---

## Prometheus Configuration

### Scrape Configuration

```yaml
# backend/prometheus/prometheus.yml
global:
  scrape_interval: 15s
  evaluation_interval: 15s
  external_labels:
    environment: production
    cluster: eucora-prod

scrape_configs:
  # Control Plane API
  - job_name: 'control-plane'
    metrics_path: '/api/v1/metrics/'
    scheme: http
    static_configs:
      - targets: ['web:8000']
        labels:
          service: 'eucora-api'
    relabel_configs:
      - source_labels: [__address__]
        target_label: instance
        regex: '([^:]+):\d+'
        replacement: '${1}'

  # Celery Workers
  - job_name: 'celery'
    static_configs:
      - targets: ['celery-worker:9808']
        labels:
          service: 'celery-worker'

  # PostgreSQL (via postgres_exporter)
  - job_name: 'postgres'
    static_configs:
      - targets: ['postgres-exporter:9187']
        labels:
          service: 'postgres'

  # Redis (via redis_exporter)
  - job_name: 'redis'
    static_configs:
      - targets: ['redis-exporter:9121']
        labels:
          service: 'redis'
```

---

## Django Metrics Endpoint

### Metrics View

```python
# backend/apps/core/views_metrics.py
from django.http import HttpResponse
from prometheus_client import (
    Counter, Histogram, Gauge,
    generate_latest, CONTENT_TYPE_LATEST,
)

# Define metrics
REQUEST_COUNT = Counter(
    'eucora_http_requests_total',
    'Total HTTP requests',
    ['method', 'endpoint', 'status']
)

REQUEST_LATENCY = Histogram(
    'eucora_http_request_duration_seconds',
    'HTTP request latency',
    ['method', 'endpoint'],
    buckets=[0.01, 0.05, 0.1, 0.25, 0.5, 1.0, 2.5, 5.0, 10.0]
)

ACTIVE_DEPLOYMENTS = Gauge(
    'eucora_active_deployments',
    'Number of active deployments',
    ['status', 'ring']
)

CAB_APPROVALS = Counter(
    'eucora_cab_approvals_total',
    'CAB approval decisions',
    ['decision', 'risk_level']
)

CONNECTOR_OPERATIONS = Counter(
    'eucora_connector_operations_total',
    'Connector operation results',
    ['connector', 'operation', 'status']
)

def metrics_view(request):
    """Prometheus metrics endpoint."""
    # Update gauges with current values
    update_deployment_gauges()

    return HttpResponse(
        generate_latest(),
        content_type=CONTENT_TYPE_LATEST
    )

def update_deployment_gauges():
    """Update gauge metrics from database."""
    from apps.deployments.models import Deployment

    for status in ['pending', 'approved', 'in_progress', 'completed']:
        for ring in range(5):
            count = Deployment.objects.filter(
                status=status,
                target_ring=ring
            ).count()
            ACTIVE_DEPLOYMENTS.labels(status=status, ring=str(ring)).set(count)
```

### Middleware for Request Metrics

```python
# backend/apps/core/middleware.py
import time
from .views_metrics import REQUEST_COUNT, REQUEST_LATENCY

class PrometheusMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()

        response = self.get_response(request)

        # Record metrics
        duration = time.time() - start_time
        endpoint = self._get_endpoint(request)

        REQUEST_COUNT.labels(
            method=request.method,
            endpoint=endpoint,
            status=response.status_code
        ).inc()

        REQUEST_LATENCY.labels(
            method=request.method,
            endpoint=endpoint
        ).observe(duration)

        return response

    def _get_endpoint(self, request):
        # Normalize endpoint for cardinality control
        return request.resolver_match.url_name if request.resolver_match else 'unknown'
```

---

## Alert Rules

```yaml
# backend/prometheus/alert_rules.yml
groups:
  - name: eucora-alerts
    rules:
      # High error rate
      - alert: HighErrorRate
        expr: |
          sum(rate(eucora_http_requests_total{status=~"5.."}[5m]))
          / sum(rate(eucora_http_requests_total[5m])) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
          description: "Error rate is {{ $value | humanizePercentage }} over 5m"

      # Slow response times
      - alert: SlowResponseTime
        expr: |
          histogram_quantile(0.95, rate(eucora_http_request_duration_seconds_bucket[5m])) > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "Slow API response times"
          description: "P95 latency is {{ $value | humanizeDuration }}"

      # Pending deployments stuck
      - alert: StuckDeployments
        expr: |
          eucora_active_deployments{status="pending"} > 10
        for: 30m
        labels:
          severity: warning
        annotations:
          summary: "Many pending deployments"
          description: "{{ $value }} deployments pending for >30m"

      # Connector failures
      - alert: ConnectorFailures
        expr: |
          rate(eucora_connector_operations_total{status="failed"}[5m]) > 0.1
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: "Connector failures detected"
          description: "{{ $labels.connector }} failing at {{ $value }}/s"

      # Certificate expiry
      - alert: CertificateExpiringSoon
        expr: |
          eucora_certificate_expiry_days < 30
        for: 1h
        labels:
          severity: warning
        annotations:
          summary: "Certificate expiring soon"
          description: "{{ $labels.certificate }} expires in {{ $value }} days"
```

---

## Grafana Dashboard

### Dashboard JSON (Key Panels)

```json
{
  "title": "EUCORA Control Plane",
  "panels": [
    {
      "title": "Request Rate",
      "type": "timeseries",
      "targets": [{
        "expr": "sum(rate(eucora_http_requests_total[5m])) by (status)",
        "legendFormat": "{{status}}"
      }]
    },
    {
      "title": "P95 Latency",
      "type": "gauge",
      "targets": [{
        "expr": "histogram_quantile(0.95, rate(eucora_http_request_duration_seconds_bucket[5m]))"
      }]
    },
    {
      "title": "Active Deployments by Status",
      "type": "piechart",
      "targets": [{
        "expr": "sum(eucora_active_deployments) by (status)",
        "legendFormat": "{{status}}"
      }]
    },
    {
      "title": "CAB Decisions",
      "type": "timeseries",
      "targets": [{
        "expr": "sum(rate(eucora_cab_approvals_total[1h])) by (decision)",
        "legendFormat": "{{decision}}"
      }]
    },
    {
      "title": "Connector Health",
      "type": "stat",
      "targets": [{
        "expr": "sum(rate(eucora_connector_operations_total{status=\"success\"}[5m])) / sum(rate(eucora_connector_operations_total[5m]))",
        "legendFormat": "Success Rate"
      }]
    }
  ]
}
```

### Grafana Provisioning

```yaml
# backend/grafana/provisioning/datasources/prometheus.yml
apiVersion: 1
datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: false
```

---

## Structured Logging

### Python Logging Configuration

```python
# backend/config/settings/logging.py
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'json': {
            '()': 'pythonjsonlogger.jsonlogger.JsonFormatter',
            'format': '%(asctime)s %(levelname)s %(name)s %(message)s',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'json',
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'INFO',
    },
    'loggers': {
        'apps': {
            'level': 'INFO',
            'handlers': ['console'],
            'propagate': False,
        },
        'django.request': {
            'level': 'WARNING',
            'handlers': ['console'],
            'propagate': False,
        },
    },
}
```

### Correlation ID in Logs

```python
import logging
import json

class CorrelationIdFilter(logging.Filter):
    """Add correlation_id to all log records."""

    def filter(self, record):
        from apps.core.context import get_correlation_id
        record.correlation_id = get_correlation_id() or '-'
        return True

# Usage in code
logger = logging.getLogger('apps.deployments')
logger.info(
    "Deployment approved",
    extra={
        'deployment_id': str(deployment.id),
        'risk_score': deployment.risk_score,
        'approved_by': request.user.email,
    }
)

# Output:
# {"timestamp": "2026-01-30T10:30:00Z", "level": "INFO", "correlation_id": "abc-123",
#  "message": "Deployment approved", "deployment_id": "xyz-456", "risk_score": 45.5}
```

---

## SIEM Integration

### Azure Sentinel

```python
# backend/apps/core/siem.py
import requests
import hashlib
import hmac
import base64
from datetime import datetime

class AzureSentinelClient:
    """Send security events to Azure Sentinel."""

    def __init__(self, workspace_id: str, shared_key: str):
        self.workspace_id = workspace_id
        self.shared_key = shared_key
        self.log_type = "EUCORA_SecurityEvents"

    def send_event(self, event: dict):
        """Send security event to Sentinel."""
        body = json.dumps([event])
        date = datetime.utcnow().strftime('%a, %d %b %Y %H:%M:%S GMT')

        signature = self._build_signature(date, len(body))

        uri = f"https://{self.workspace_id}.ods.opinsights.azure.com/api/logs?api-version=2016-04-01"

        headers = {
            'Content-Type': 'application/json',
            'Authorization': signature,
            'Log-Type': self.log_type,
            'x-ms-date': date,
        }

        response = requests.post(uri, data=body, headers=headers)
        response.raise_for_status()

# Usage
sentinel = AzureSentinelClient(workspace_id, shared_key)
sentinel.send_event({
    'EventType': 'CAB_APPROVAL',
    'CorrelationId': correlation_id,
    'DeploymentId': str(deployment.id),
    'Decision': 'APPROVED',
    'ApprovedBy': approver.email,
    'RiskScore': deployment.risk_score,
    'Timestamp': datetime.utcnow().isoformat(),
})
```

---

## Key Metrics to Monitor

| Metric | Alert Threshold | Severity |
|--------|-----------------|----------|
| Error rate (5xx) | > 5% | Critical |
| P95 latency | > 2s | Warning |
| Pending deployments | > 10 for 30m | Warning |
| Connector failures | > 10% | Critical |
| Certificate expiry | < 30 days | Warning |
| CAB queue depth | > 20 | Warning |
| Database connections | > 80% pool | Warning |
| Redis memory | > 80% | Warning |

---

## Checklist

```
☐ Prometheus scraping /api/v1/metrics/
☐ All custom metrics defined and exported
☐ Alert rules configured for critical paths
☐ Grafana dashboards provisioned
☐ Structured JSON logging enabled
☐ Correlation IDs in all log entries
☐ SIEM integration for security events
☐ On-call alerting configured (PagerDuty/Opsgenie)
```
