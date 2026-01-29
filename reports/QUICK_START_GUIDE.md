# Grafana Metrics Integration - Quick Start Guide

**Last Updated:** January 24, 2026
**Status:** ✅ Production Ready

---

## Access Points

### Grafana Dashboard
- **URL:** http://localhost:3000
- **Credentials:** admin/admin (first login only)
- **Dashboard:** EUCORA Control Plane - Operations Dashboard

### Prometheus
- **URL:** http://localhost:9090
- **Query Examples:**
  - All deployment metrics: `deployment_total`
  - Deployment rate: `rate(deployment_total[1m])`
  - Success rate: `sum(rate(deployment_total{status="COMPLETED"}[5m])) / sum(rate(deployment_total[5m]))`

### API Metrics Endpoint
- **URL:** http://localhost:8000/api/v1/metrics/
- **Format:** Prometheus text format
- **Authentication:** None (internal endpoint)

---

## Common Queries

### All Deployment Metrics
```bash
curl http://localhost:8000/api/v1/metrics/ | grep deployment
```

### Query Prometheus from CLI
```bash
# All deployment metrics
curl 'http://localhost:9090/api/v1/query?query=deployment_total' | jq

# Deployment rate
curl 'http://localhost:9090/api/v1/query?query=rate(deployment_total[1m])' | jq

# Success rate
curl 'http://localhost:9090/api/v1/query?query=rate(deployment_total{status="COMPLETED"}[5m])' | jq
```

---

## Container Management

### Check Status
```bash
docker-compose -f docker-compose.dev.yml ps
```

### View Logs
```bash
# API logs
docker-compose -f docker-compose.dev.yml logs eucora-api

# Prometheus logs
docker-compose -f docker-compose.dev.yml logs eucora-prometheus

# Grafana logs
docker-compose -f docker-compose.dev.yml logs eucora-grafana
```

### Restart Services
```bash
# Restart metrics stack
docker-compose -f docker-compose.dev.yml restart eucora-api eucora-prometheus eucora-grafana

# Full restart
docker-compose -f docker-compose.dev.yml down && docker-compose -f docker-compose.dev.yml up -d
```

---

## Testing Metrics

### Create Test Deployment
```bash
docker exec eucora-control-plane python /app/test_metrics_recording.py
```

### Verify Metrics Flowing
```bash
# 1. Check metrics endpoint
curl http://localhost:8000/api/v1/metrics/ | grep deployment_total

# 2. Wait 30 seconds for Prometheus scrape
sleep 30

# 3. Query Prometheus
curl 'http://localhost:9090/api/v1/query?query=deployment_total' | python3 -m json.tool
```

---

## Available Metrics

| Metric | Type | Labels | Purpose |
|--------|------|--------|---------|
| `deployment_total` | Counter | app_name, ring, status, requires_cab | Total deployments |
| `deployment_duration_seconds` | Histogram | app_name, ring, status | Deployment duration |
| `deployment_duration_seconds_sum` | Sum | app_name, ring, status | Total duration |
| `deployment_duration_seconds_count` | Count | app_name, ring, status | Number of deployments |
| `ring_promotion_total` | Counter | from_ring, to_ring, status | Ring promotions |
| `promotion_gate_success_rate` | Gauge | ring | Success rate per ring |
| `circuit_breaker_state` | Gauge | service, connector_type | Circuit breaker health |
| `connector_health` | Gauge | connector_type | Connector status |
| `db_connection_pool_size` | Gauge | - | DB pool status |

---

## Grafana Dashboard Panels

### Current Panels
1. **Deployment Rate** — Deployments per minute
2. **Success Rates by Ring** — Success rate per ring
3. **Connector Health Status** — Health of each connector
4. **Circuit Breaker State** — Circuit breaker states
5. **Deployment Duration** — Duration distribution

### How to Add New Panel
1. Navigate to http://localhost:3000
2. Login as admin
3. Open dashboard: EUCORA Control Plane - Operations Dashboard
4. Click "Add Panel"
5. Choose visualization type
6. Enter Prometheus query (e.g., `deployment_total`)
7. Click "Save"

---

## Troubleshooting

### Metrics Not Appearing
**Problem:** Dashboard shows no data
**Solution:**
```bash
# 1. Verify API is running
curl http://localhost:8000/api/v1/metrics/

# 2. Check Prometheus targets
curl http://localhost:9090/api/v1/targets | grep eucora-api

# 3. Wait 30 seconds for scrape
sleep 30

# 4. Query Prometheus directly
curl 'http://localhost:9090/api/v1/query?query=deployment_total'
```

### Prometheus Not Scraping
**Problem:** Prometheus targets show DOWN
**Solution:**
```bash
# 1. Verify API container is healthy
docker ps | grep eucora-control-plane

# 2. Test metrics endpoint
curl http://localhost:8000/api/v1/metrics/

# 3. Check network
docker network ls
docker network inspect eucora_default

# 4. Restart Prometheus
docker-compose -f docker-compose.dev.yml restart eucora-prometheus
```

### Grafana Not Connecting to Prometheus
**Problem:** Datasource shows FAILED
**Solution:**
```bash
# 1. Verify Prometheus is running
docker ps | grep prometheus

# 2. Test Prometheus API
curl http://localhost:9090/api/v1/query?query=up

# 3. In Grafana, go to Configuration → Data Sources
# 4. Edit Prometheus datasource
# 5. Update URL if needed: http://prometheus:9090
# 6. Click "Save & Test"
```

---

## Performance Tips

### Optimize Prometheus Retention
If disk space is a concern, edit `backend/prometheus/prometheus.yml`:
```yaml
global:
  retention: 7d  # Keep 7 days instead of 15
```

### Optimize Scrape Interval
If you need more recent data, reduce scrape interval in `prometheus.yml`:
```yaml
global:
  scrape_interval: 10s  # Instead of 15s
```

### Optimize Grafana Refresh
In dashboard panel settings, set refresh rate:
- Fast updates: `5s`
- Standard: `30s`
- Low priority: `1m`

---

## Backup & Restore

### Backup Prometheus Data
```bash
# Create backup of Prometheus data directory
docker-compose -f docker-compose.dev.yml exec eucora-prometheus tar czf /tmp/prometheus-backup.tar.gz /prometheus

# Copy to host
docker cp eucora-prometheus:/tmp/prometheus-backup.tar.gz ./prometheus-backup.tar.gz
```

### Backup Grafana Dashboards
```bash
# Export dashboard as JSON
curl -H "Authorization: Bearer <api-key>" \
  http://localhost:3000/api/dashboards/db/eucora-ops-dashboard \
  > dashboard-backup.json
```

---

## Monitoring the Metrics System Itself

### Check Prometheus Health
```bash
curl http://localhost:9090/-/healthy
```

### Check Prometheus Readiness
```bash
curl http://localhost:9090/-/ready
```

### View Prometheus Targets
```bash
curl http://localhost:9090/api/v1/targets | python3 -m json.tool
```

### View Prometheus Rules
```bash
curl http://localhost:9090/api/v1/rules | python3 -m json.tool
```

---

## Next Steps

### Week 1
- [ ] Monitor dashboards daily
- [ ] Verify metrics continue flowing
- [ ] Check Prometheus disk usage

### Week 2
- [ ] Configure Prometheus alert rules
- [ ] Set up email/Slack notifications
- [ ] Create SLO dashboards

### Month 1
- [ ] Analyze metrics for optimization
- [ ] Implement additional connector metrics
- [ ] Set up metrics export to external monitoring

---

## Support & Documentation

- **Architecture:** See `docs/architecture/`
- **Implementation Details:** See `reports/`
- **Code:** See `backend/apps/deployment_intents/`
- **Metrics Definition:** See `backend/apps/core/metrics.py`

---

## Emergency Procedures

### Reset Prometheus Data
```bash
# Stop Prometheus
docker-compose -f docker-compose.dev.yml stop eucora-prometheus

# Remove data volume
docker volume rm eucora_prometheus_data

# Restart
docker-compose -f docker-compose.dev.yml up -d eucora-prometheus
```

### Reset Grafana
```bash
# Stop Grafana
docker-compose -f docker-compose.dev.yml stop eucora-grafana

# Remove data volume
docker volume rm eucora_grafana_data

# Restart (dashboards will be re-provisioned)
docker-compose -f docker-compose.dev.yml up -d eucora-grafana
```

### Full System Reset
```bash
cd /Users/raghunathchava/code/EUCORA

# Stop everything
docker-compose -f docker-compose.dev.yml down

# Remove all data
docker volume prune -f

# Restart fresh
docker-compose -f docker-compose.dev.yml up -d
```

---

## Quick Reference

| Action | Command |
|--------|---------|
| View metrics | `curl http://localhost:8000/api/v1/metrics/` |
| Open Grafana | http://localhost:3000 |
| Open Prometheus | http://localhost:9090 |
| Check containers | `docker-compose ps` |
| View logs | `docker-compose logs -f eucora-api` |
| Test metrics | `docker exec eucora-control-plane python /app/test_metrics_recording.py` |
| Query deployment_total | `curl 'http://localhost:9090/api/v1/query?query=deployment_total'` |

---

**Status:** ✅ System Operational
**Last Checked:** January 24, 2026

*For detailed documentation, see IMPLEMENTATION_COMPLETE_SUMMARY.md*
