# P7 Agent Management - Docker Testing Guide

**SPDX-License-Identifier: Apache-2.0**

---

## Quick Start (30 Minutes)

### Step 1: Start Docker Environment (5 min)

```bash
cd /Users/raghunathchava/code/EUCORA

# Start all services
docker compose -f docker-compose.dev.yml up -d

# Wait for services to be healthy
docker compose -f docker-compose.dev.yml ps
```

**Expected Services**:
- eucora-db (PostgreSQL)
- eucora-redis (Redis)
- eucora-minio (MinIO)
- eucora-control-plane (Django API)
- eucora-celery-worker (Celery worker)
- eucora-celery-beat (Celery Beat scheduler)
- eucora-prometheus (Prometheus)
- eucora-grafana (Grafana)
- eucora-web (React frontend)

### Step 2: Run Migrations (5 min)

```bash
# Create migrations for agent_management
docker compose -f docker-compose.dev.yml exec eucora-api python manage.py makemigrations agent_management

# Apply migrations
docker compose -f docker-compose.dev.yml exec eucora-api python manage.py migrate

# Verify migrations applied
docker compose -f docker-compose.dev.yml exec eucora-api python manage.py showmigrations agent_management
```

**Expected Output**:
```
agent_management
 [X] 0001_initial
```

### Step 3: Run Comprehensive Tests (15 min)

```bash
# Run all agent_management tests
docker compose -f docker-compose.dev.yml exec eucora-api pytest apps/agent_management/tests/ -v

# Run specific test modules
docker compose -f docker-compose.dev.yml exec eucora-api pytest apps/agent_management/tests/test_models.py -v
docker compose -f docker-compose.dev.yml exec eucora-api pytest apps/agent_management/tests/test_services.py -v
docker compose -f docker-compose.dev.yml exec eucora-api pytest apps/agent_management/tests/test_api.py -v
docker compose -f docker-compose.dev.yml exec eucora-api pytest apps/agent_management/tests/test_tasks.py -v

# Run with coverage report
docker compose -f docker-compose.dev.yml exec eucora-api pytest apps/agent_management/tests/ --cov=apps.agent_management --cov-report=term-missing
```

**Expected Results**:
- **80 tests total**
- **All tests passing**
- **Coverage ≥ 90%**

### Step 4: Manual API Testing (5 min)

#### Register an Agent

```bash
curl -X POST http://localhost:8000/api/v1/agent-management/agents/register/ \
  -H "Content-Type: application/json" \
  -H "X-Correlation-ID: test-001" \
  -u admin:admin@134 \
  -d '{
    "hostname": "test-win-001",
    "platform": "windows",
    "platform_version": "11 22H2",
    "agent_version": "1.0.0",
    "registration_key": "test-reg-001",
    "cpu_cores": 8,
    "memory_mb": 16384,
    "disk_gb": 512,
    "ip_address": "10.0.1.100",
    "mac_address": "00:15:5D:00:00:01"
  }'
```

**Expected Response** (201 Created):
```json
{
  "id": "uuid-here",
  "hostname": "test-win-001",
  "platform": "windows",
  "status": "ONLINE",
  ...
}
```

#### Send Heartbeat

```bash
# Get agent ID from registration response
AGENT_ID="<uuid-from-above>"

curl -X POST http://localhost:8000/api/v1/agent-management/agents/$AGENT_ID/heartbeat/ \
  -H "X-Correlation-ID: test-002" \
  -u admin:admin@134
```

**Expected Response** (200 OK):
```json
{
  "status": "ok",
  "pending_tasks": 0,
  "tasks": []
}
```

#### List All Agents

```bash
curl -X GET http://localhost:8000/api/v1/agent-management/agents/ \
  -u admin:admin@134
```

---

## Verification Checklist

### Database
- [ ] Migrations applied successfully
- [ ] All 5 tables created (Agent, AgentTask, AgentOfflineQueue, AgentTelemetry, AgentDeploymentStatus)
- [ ] Indexes created correctly

### API Endpoints
- [ ] Agent registration works (POST /agents/register/)
- [ ] Agent heartbeat works (POST /agents/{id}/heartbeat/)
- [ ] List agents works (GET /agents/)
- [ ] Create task works (POST /tasks/)
- [ ] Submit telemetry works (POST /telemetry/)

### Celery Tasks
- [ ] Celery Beat scheduler running
- [ ] check_agent_health task scheduled (every 5 min)
- [ ] timeout_stale_tasks task scheduled (every 10 min)

```bash
# Check Celery Beat schedule
docker compose -f docker-compose.dev.yml logs eucora-celery-beat | grep "check-agent-health"
docker compose -f docker-compose.dev.yml logs eucora-celery-beat | grep "timeout-stale-tasks"
```

### Tests
- [ ] All 80 tests passing
- [ ] Model tests: 20/20 passing
- [ ] Service tests: 30/30 passing
- [ ] API tests: 25/25 passing
- [ ] Task tests: 5/5 passing
- [ ] Coverage ≥ 90%

---

## Troubleshooting

### Database Connection Issues

```bash
# Check PostgreSQL logs
docker compose -f docker-compose.dev.yml logs eucora-db

# Verify database is healthy
docker compose -f docker-compose.dev.yml exec eucora-db pg_isready -U eucora_user -d eucora
```

### Redis Connection Issues

```bash
# Check Redis logs
docker compose -f docker-compose.dev.yml logs eucora-redis

# Test Redis connection
docker compose -f docker-compose.dev.yml exec eucora-redis redis-cli ping
```

### Django Application Issues

```bash
# Check Django logs
docker compose -f docker-compose.dev.yml logs eucora-api

# Shell into container
docker compose -f docker-compose.dev.yml exec eucora-api bash

# Check Django settings
docker compose -f docker-compose.dev.yml exec eucora-api python manage.py check
```

### Test Failures

```bash
# Run tests with verbose output
docker compose -f docker-compose.dev.yml exec eucora-api pytest apps/agent_management/tests/ -vv

# Run specific failing test
docker compose -f docker-compose.dev.yml exec eucora-api pytest apps/agent_management/tests/test_models.py::AgentModelTests::test_agent_creation -vv

# Run with pdb debugger
docker compose -f docker-compose.dev.yml exec eucora-api pytest apps/agent_management/tests/ --pdb
```

---

## Performance Testing

### Database Query Performance

```bash
# Enable Django query logging
docker compose -f docker-compose.dev.yml exec eucora-api python manage.py shell

# In Django shell:
from django.db import connection
from django.test.utils import override_settings

with override_settings(DEBUG=True):
    from apps.agent_management.models import Agent
    agents = list(Agent.objects.all())
    print(len(connection.queries))  # Should be 1 query (no N+1)
```

### API Response Time

```bash
# Benchmark agent registration
ab -n 100 -c 10 -T application/json -u admin:admin@134 \
  -p /tmp/agent_payload.json \
  http://localhost:8000/api/v1/agent-management/agents/register/

# Expected: < 100ms per request
```

---

## Next Steps After Verification

1. **Document Agent Specification** (4 hours)
   - Create `docs/agent/AGENT_SPECIFICATION.md`
   - Define Go-based agent requirements
   - Document communication protocol

2. **Start P8 Implementation** (Days 2-3)
   - Create `apps/packaging_factory`
   - Implement models and services
   - Write comprehensive tests

---

## Reference

- **API Documentation**: http://localhost:8000/api/docs/
- **Django Admin**: http://localhost:8000/admin/ (admin / admin@134)
- **Prometheus**: http://localhost:9090/
- **Grafana**: http://localhost:3000/ (admin / admin)

---

**ESTIMATED TIME**: 30 minutes
**STATUS**: Ready for execution
