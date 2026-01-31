# E8: AI Agent Workflows - Docker Deployment Guide

**SPDX-License-Identifier**: Apache-2.0
**Date**: January 31, 2026
**Status**: Ready for Docker Deployment

---

## Overview

This guide covers deploying E8 AI Agent Workflows in the Docker environment. The application runs in Docker Compose with PostgreSQL, Redis, and other services.

---

## Prerequisites

- ✅ Docker and Docker Compose installed
- ✅ E1, E3, E7 dependencies already deployed
- ✅ Docker containers running (`docker-compose -f docker-compose.dev.yml up`)

---

## Step 1: Rebuild Backend Container (After Code Changes)

After adding E8 code, rebuild the backend container to install new dependencies:

```bash
# Rebuild backend container with new dependencies (channels, channels-redis)
docker-compose -f docker-compose.dev.yml build eucora-api

# Or rebuild all services
docker-compose -f docker-compose.dev.yml build
```

**What This Does:**
- Installs `channels` and `channels-redis` from `pyproject.toml`
- Updates Python dependencies
- Prepares container for WebSocket support

---

## Step 2: Run Migrations

Migrations run automatically via `entrypoint.sh`, but you can run manually:

```bash
# Run migrations in the API container
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py migrate ai_agents

# Or restart container to trigger automatic migrations
docker-compose -f docker-compose.dev.yml restart eucora-api
```

**Expected Output:**
```
Running migrations:
  Applying ai_agents.0006_workflow_models... OK
```

---

## Step 3: Seed Workflow Definitions

Workflows are seeded automatically via `entrypoint.sh` on container start. To seed manually:

```bash
# Seed workflows in the API container
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py seed_workflows
```

**Expected Output:**
```
======================================================================
EUCORA Workflow Definitions Seeder
======================================================================
  ✓ Created: Package Analysis and Evidence Generation (packaging)
  ✓ Created: CAB Evidence Generation (cab_evidence)
  ✓ Created: Risk Score Explanation (risk_explainer)
  ✓ Created: Deployment Planning and Execution (deployment)
  ✓ Created: Compliance Analysis (compliance)
  ✓ Created: Incident Response (incident)

======================================================================
Summary:
  Created: 6
  Updated: 0
  Total workflows: 6
======================================================================
```

---

## Step 4: Verify Configuration

### Check Redis Connectivity (for Channels)

```bash
# Test Redis connection from API container
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py shell
```

In Django shell:
```python
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
print(channel_layer)  # Should show RedisChannelLayer
```

### Check Workflow API Endpoints

```bash
# List workflows (from host machine)
curl http://localhost:8000/api/v1/ai/workflows/

# Should return JSON with workflow definitions
```

### Check Database

```bash
# Connect to PostgreSQL
docker-compose -f docker-compose.dev.yml exec db psql -U eucora_user -d eucora

# Verify tables
\dt ai_agents_workflow*

# Verify workflows seeded
SELECT agent_type, name, risk_level FROM ai_agents_workflowdefinition;
```

---

## Step 5: Test Workflow Execution

### Via Frontend UI

1. **Access Frontend**: `http://localhost:5173`
2. **Navigate to AI Agents**: Click "AI Agent Hub" in sidebar
3. **Open Workflows Tab**: Click "Workflows" tab
4. **Start Workflow**: Click "Start Workflow" on any workflow
5. **View Execution**: Navigate to execution page
6. **Test Approval Gates**: For R2/R3 workflows, test approve/reject

### Via API (from host)

```bash
# Get auth token first (if using token auth)
TOKEN=$(curl -X POST http://localhost:8000/api/v1/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin@134"}' | jq -r '.token')

# List workflows
curl http://localhost:8000/api/v1/ai/workflows/ \
  -H "Authorization: Bearer $TOKEN"

# Start workflow execution
curl -X POST http://localhost:8000/api/v1/ai/workflows/{workflow_id}/start/ \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "package_name": "test-package"
    }
  }'
```

---

## Docker Configuration Details

### Environment Variables

The `docker-compose.dev.yml` already includes:
- ✅ `REDIS_URL=redis://redis:6379/0` - Redis for cache
- ✅ `CELERY_BROKER_URL=redis://redis:6379/1` - Redis for Celery
- ✅ Channels uses same Redis host (`redis`) but different database

### ASGI vs WSGI

**Development (`docker-compose.dev.yml`):**
- Uses `python manage.py runserver` which supports ASGI
- WebSocket connections work automatically
- No additional configuration needed

**Production (if using `Dockerfile`):**
- Uses `gunicorn` with WSGI (doesn't support WebSockets)
- For WebSocket support, switch to `uvicorn`:
  ```dockerfile
  CMD ["uvicorn", "config.asgi:application", "--host", "0.0.0.0", "--port", "8000"]
  ```

### Redis Hostname

In Docker, Redis hostname is `redis` (service name), not `localhost`. The `CHANNEL_LAYERS` configuration automatically uses the `REDIS_URL` environment variable, which is set to `redis://redis:6379/0` in docker-compose.

---

## WebSocket Testing in Docker

### Test WebSocket Connection

From host machine, use a WebSocket client:

```javascript
// In browser console or WebSocket client
const ws = new WebSocket('ws://localhost:8000/ws/ai/executions/{execution_id}/');

ws.onopen = () => console.log('Connected');
ws.onmessage = (event) => console.log('Message:', JSON.parse(event.data));
ws.onerror = (error) => console.error('Error:', error);
```

**Note**: WebSocket connections work through Docker port mapping (`8000:8000`).

---

## Troubleshooting

### Migration Fails: pgvector Not Found

**Error:**
```
ModuleNotFoundError: No module named 'pgvector'
```

**Solution:**
```bash
# Rebuild container to install dependencies
docker-compose -f docker-compose.dev.yml build eucora-api
docker-compose -f docker-compose.dev.yml up -d eucora-api
```

### Migration Fails: Extension Not Installed

**Error:**
```
ERROR: extension "vector" does not exist
```

**Solution:**
```bash
# Connect to PostgreSQL container
docker-compose -f docker-compose.dev.yml exec db psql -U eucora_user -d eucora

# Create extension
CREATE EXTENSION IF NOT EXISTS vector;
```

### Channels Import Error

**Error:**
```
ImportError: cannot import name 'ProtocolTypeRouter'
```

**Solution:**
```bash
# Rebuild container
docker-compose -f docker-compose.dev.yml build eucora-api
docker-compose -f docker-compose.dev.yml restart eucora-api
```

### WebSocket Connection Refused

**Check:**
1. Container is running: `docker-compose -f docker-compose.dev.yml ps`
2. Port 8000 is mapped: Check `docker-compose.dev.yml` ports section
3. Redis is healthy: `docker-compose -f docker-compose.dev.yml exec redis redis-cli ping`
4. ASGI is being used: Check container logs for ASGI startup

**View Logs:**
```bash
docker-compose -f docker-compose.dev.yml logs eucora-api | tail -50
```

### Workflows Not Seeding

**Check Entrypoint:**
```bash
# View entrypoint logs
docker-compose -f docker-compose.dev.yml logs eucora-api | grep -i workflow

# Manually seed if needed
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py seed_workflows
```

---

## Quick Start Commands

### Full Deployment (First Time)

```bash
# 1. Rebuild containers with new dependencies
docker-compose -f docker-compose.dev.yml build

# 2. Start all services
docker-compose -f docker-compose.dev.yml up -d

# 3. Check logs for migration and seeding
docker-compose -f docker-compose.dev.yml logs eucora-api | tail -100

# 4. Verify workflows seeded
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py shell -c "from apps.ai_agents.workflows.models import WorkflowDefinition; print(f'Workflows: {WorkflowDefinition.objects.count()}')"
```

### After Code Updates

```bash
# Restart API container (migrations and seeding run automatically)
docker-compose -f docker-compose.dev.yml restart eucora-api

# Or rebuild if dependencies changed
docker-compose -f docker-compose.dev.yml build eucora-api
docker-compose -f docker-compose.dev.yml up -d eucora-api
```

### Verify Everything Works

```bash
# Check API health
curl http://localhost:8000/health/live

# Check workflows endpoint
curl http://localhost:8000/api/v1/ai/workflows/

# Check container status
docker-compose -f docker-compose.dev.yml ps
```

---

## Docker-Specific Notes

### Volume Mounts

The `docker-compose.dev.yml` mounts the backend directory:
```yaml
volumes:
  - ./backend:/app
```

This means:
- ✅ Code changes are reflected immediately (no rebuild needed)
- ✅ But Python dependencies still need container restart after `pyproject.toml` changes

### Database Persistence

PostgreSQL data persists in Docker volume `postgres_data`. Migrations are applied automatically on container start via `entrypoint.sh`.

### Redis Persistence

Redis data persists in Docker volume `redis_data`. Channels uses Redis database 2 (separate from cache db 0 and Celery db 1).

---

## Production Considerations

For production deployment:

1. **Use ASGI Server**: Switch from `gunicorn` (WSGI) to `uvicorn` (ASGI) in `Dockerfile`
2. **WebSocket Load Balancing**: Use sticky sessions if load balancing
3. **Redis HA**: Configure Redis Sentinel or Cluster for high availability
4. **Monitoring**: Monitor WebSocket connection counts and Redis memory usage

---

## Files Modified for Docker

- ✅ `backend/entrypoint.sh` - Added workflow seeding step
- ✅ `backend/config/settings/base.py` - CHANNEL_LAYERS uses REDIS_URL (works with Docker hostname)
- ✅ `docker-compose.dev.yml` - Already configured correctly (no changes needed)

---

**Docker Deployment Status**: ✅ **READY**

All Docker-specific configurations are complete. Follow the steps above to deploy E8 in your Docker environment.
