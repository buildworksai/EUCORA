# EUCORA Quick Reference

**SPDX-License-Identifier: Apache-2.0**
**Last Updated**: January 31, 2026

---

## Development Environment

### Start Services
```bash
cd /Users/raghunathchava/code/EUCORA
docker-compose -f docker-compose.dev.yml up -d
```

### Stop Services
```bash
docker-compose -f docker-compose.dev.yml down
```

### View Logs
```bash
# All services
docker-compose -f docker-compose.dev.yml logs -f

# Specific service
docker-compose -f docker-compose.dev.yml logs -f eucora-api
docker-compose -f docker-compose.dev.yml logs -f eucora-web
```

### Restart Services
```bash
docker-compose -f docker-compose.dev.yml restart eucora-api eucora-web
```

---

## Access Points

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:5173 | admin@eucora.com / admin@134 |
| Backend API | http://localhost:8000 | - |
| API Docs | http://localhost:8000/api/docs/ | - |
| Grafana | http://localhost:3000 | admin / admin |
| Prometheus | http://localhost:9090 | - |
| MinIO Console | http://localhost:9001 | minioadmin / minioadmin |
| pgAdmin | http://localhost:5050 | admin@eucora.com / admin |

---

## Common Commands

### Database
```bash
# Run migrations
docker exec eucora-control-plane python manage.py migrate

# Create migrations
docker exec eucora-control-plane python manage.py makemigrations

# Seed demo data
docker exec eucora-control-plane python manage.py seed_demo_data

# Django shell
docker exec -it eucora-control-plane python manage.py shell
```

### Testing
```bash
# Run all tests
docker exec eucora-control-plane pytest --cov

# Run specific app tests
docker exec eucora-control-plane pytest apps/storage/tests/ -v

# Run with coverage report
docker exec eucora-control-plane pytest --cov --cov-report=html
```

### Frontend
```bash
# TypeScript check
cd frontend && npx tsc --noEmit

# Lint check
cd frontend && npm run lint

# Build
cd frontend && npm run build
```

### Pre-commit
```bash
# Install hooks
pip install pre-commit && pre-commit install

# Run all checks
pre-commit run --all-files
```

---

## API Endpoints

### Core Endpoints
| Resource | Endpoint | Methods |
|----------|----------|---------|
| Assets | `/api/v1/assets/` | GET, POST, PUT, DELETE |
| Applications | `/api/v1/applications/` | GET, POST, PUT, DELETE |
| Deployments | `/api/v1/deployments/` | GET, POST, PUT, DELETE |
| CAB Requests | `/api/v1/cab/requests/` | GET, POST, PUT, DELETE |
| Storage | `/api/v1/storage/providers/` | GET, POST, PUT, DELETE |
| AI Agents | `/api/v1/ai-agents/workflows/` | GET, POST |

### Example Requests
```bash
# List deployments
curl http://localhost:8000/api/v1/deployments/

# Get storage health
curl http://localhost:8000/api/v1/storage/health/

# Test storage provider
curl -X POST http://localhost:8000/api/v1/storage/providers/{id}/test/

# Get metrics
curl http://localhost:8000/api/v1/metrics/
```

---

## Monitoring

### Check Container Status
```bash
docker-compose -f docker-compose.dev.yml ps
```

### Health Checks
```bash
# API health
curl http://localhost:8000/health/live

# Storage health
curl http://localhost:8000/api/v1/storage/health/

# Prometheus health
curl http://localhost:9090/-/healthy
```

### View Metrics
```bash
curl http://localhost:8000/api/v1/metrics/ | grep deployment
```

---

## Grafana Dashboard

### Key Metrics
| Metric | Description |
|--------|-------------|
| `deployment_total` | Total deployments by status/ring |
| `deployment_duration_seconds` | Deployment duration histogram |
| `ring_promotion_total` | Ring promotions |
| `connector_health` | Connector status |
| `circuit_breaker_state` | Circuit breaker health |

### Prometheus Queries
```promql
# Deployment rate
rate(deployment_total[1m])

# Success rate
sum(rate(deployment_total{status="COMPLETED"}[5m])) / sum(rate(deployment_total[5m]))

# Avg deployment duration
histogram_quantile(0.95, rate(deployment_duration_seconds_bucket[5m]))
```

---

## MinIO Storage

### Create Bucket
```bash
docker exec eucora-minio mc alias set local http://localhost:9000 minioadmin minioadmin
docker exec eucora-minio mc mb local/eucora-storage --ignore-existing
```

### List Buckets
```bash
docker exec eucora-minio mc ls local/
```

### Upload File
```bash
docker exec eucora-minio mc cp /path/to/file local/eucora-storage/
```

---

## Troubleshooting

### API Not Responding
```bash
# Check container
docker ps | grep eucora-control-plane

# Check logs
docker-compose -f docker-compose.dev.yml logs --tail=50 eucora-api

# Restart
docker-compose -f docker-compose.dev.yml restart eucora-api
```

### Database Connection Issues
```bash
# Check PostgreSQL
docker ps | grep postgres

# Connect to database
docker exec -it eucora-db psql -U eucora -d eucora_db
```

### Frontend Not Loading
```bash
# Check container
docker ps | grep eucora-web

# Check logs
docker-compose -f docker-compose.dev.yml logs --tail=50 eucora-web

# Restart
docker-compose -f docker-compose.dev.yml restart eucora-web
```

### Storage Provider Issues
```bash
# Check MinIO
docker ps | grep minio

# Test MinIO connection
docker exec eucora-minio mc admin info local

# Verify bucket exists
docker exec eucora-minio mc ls local/eucora-storage
```

---

## Git Workflow

### Commit with Pre-commit
```bash
git add -A
git commit -m "feat: description"
```

### Bypass Pre-commit (emergency only)
```bash
git commit --no-verify -m "fix: description"
```

### Push to Main
```bash
git push origin main
```

---

## File Locations

| Component | Path |
|-----------|------|
| Backend Apps | `backend/apps/` |
| Frontend Routes | `frontend/src/routes/` |
| Docker Compose | `docker-compose.dev.yml` |
| K8s Manifests | `k8s/` |
| Scripts | `scripts/` |
| Documentation | `docs/` |
| Reports | `reports/` |

---

*For detailed implementation history, see IMPLEMENTATION_HISTORY.md*
