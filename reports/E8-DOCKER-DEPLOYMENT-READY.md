# E8: AI Agent Workflows - Docker Deployment Ready

**SPDX-License-Identifier**: Apache-2.0
**Date**: January 31, 2026
**Status**: ✅ **READY FOR DOCKER DEPLOYMENT**

---

## Summary

E8 AI Agent Workflows is fully configured for Docker deployment. All Docker-specific settings have been updated, and the deployment process is automated via `entrypoint.sh`.

---

## What's Been Configured

### ✅ Docker-Specific Updates

1. **Entrypoint Script** (`backend/entrypoint.sh`)
   - Added automatic workflow seeding after migrations
   - Runs on every container start
   - Non-blocking (warnings only, won't stop container)

2. **Redis Configuration** (`backend/config/settings/base.py`)
   - `CHANNEL_LAYERS` automatically uses `REDIS_URL` environment variable
   - Works with Docker hostname `redis` (from docker-compose)
   - Parses Redis URL correctly for both Docker and localhost

3. **Dependencies** (`backend/pyproject.toml`)
   - `channels~=4.0.0` added
   - `channels-redis~=4.2.0` added
   - Will be installed on next container build

4. **ASGI Configuration** (`backend/config/asgi.py`)
   - WebSocket routing configured
   - Works with `runserver` (development)
   - Ready for `uvicorn` (production)

---

## Quick Deployment (Docker)

### Option 1: Automated Script

```bash
# Run deployment script
./scripts/docker-deploy-e8.sh
```

This script will:
1. Rebuild backend container
2. Restart API container
3. Verify workflows seeded
4. Test API endpoints

### Option 2: Manual Steps

```bash
# 1. Rebuild container (installs channels dependencies)
docker-compose -f docker-compose.dev.yml build eucora-api

# 2. Restart container (migrations and seeding run automatically)
docker-compose -f docker-compose.dev.yml restart eucora-api

# 3. Verify workflows seeded
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py shell -c "from apps.ai_agents.workflows.models import WorkflowDefinition; print(f'Workflows: {WorkflowDefinition.objects.count()}')"
```

---

## Verification Checklist

After deployment, verify:

- [ ] Container rebuilt successfully
- [ ] Migrations applied (check logs)
- [ ] 6 workflows seeded
- [ ] API endpoint `/api/v1/ai/workflows/` responds
- [ ] Frontend workflows tab visible
- [ ] Can start a workflow execution
- [ ] WebSocket connections work (optional)

### Quick Verification Commands

```bash
# Check container status
docker-compose -f docker-compose.dev.yml ps

# Check API logs
docker-compose -f docker-compose.dev.yml logs eucora-api | tail -50

# Test workflows API
curl http://localhost:8000/api/v1/ai/workflows/

# Check workflows in database
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py shell -c "from apps.ai_agents.workflows.models import WorkflowDefinition; [print(f'{w.agent_type}: {w.name}') for w in WorkflowDefinition.objects.all()]"
```

---

## Docker Environment Details

### Service Names (from docker-compose.dev.yml)

- **Backend API**: `eucora-api` (port 8000)
- **PostgreSQL**: `db` (port 5432)
- **Redis**: `redis` (port 6379)
- **Frontend**: `eucora-web` (port 5173)

### Redis Databases

- **Database 0**: Cache and sessions (`REDIS_URL`)
- **Database 1**: Celery broker and results
- **Database 2**: Channels WebSocket layer (auto-configured)

### Environment Variables

Already configured in `docker-compose.dev.yml`:
- ✅ `REDIS_URL=redis://redis:6379/0`
- ✅ `CELERY_BROKER_URL=redis://redis:6379/1`
- ✅ Channels uses same Redis host (`redis`) automatically

---

## Files Modified for Docker

- ✅ `backend/entrypoint.sh` - Added workflow seeding
- ✅ `backend/config/settings/base.py` - Docker-compatible Redis parsing
- ✅ `backend/pyproject.toml` - Channels dependencies
- ✅ `backend/config/asgi.py` - WebSocket routing
- ✅ `scripts/docker-deploy-e8.sh` - Deployment automation script

---

## Troubleshooting

### Container Won't Start

```bash
# Check logs
docker-compose -f docker-compose.dev.yml logs eucora-api

# Check if dependencies installed
docker-compose -f docker-compose.dev.yml exec eucora-api pip list | grep channels
```

### Workflows Not Seeding

```bash
# Manually seed
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py seed_workflows

# Check if workflows exist
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py shell -c "from apps.ai_agents.workflows.models import WorkflowDefinition; print(WorkflowDefinition.objects.count())"
```

### WebSocket Not Working

```bash
# Verify Redis connectivity
docker-compose -f docker-compose.dev.yml exec redis redis-cli ping

# Test Channels layer
docker-compose -f docker-compose.dev.yml exec eucora-api python manage.py shell -c "from channels.layers import get_channel_layer; print(get_channel_layer())"
```

---

## Next Steps

1. **Run Deployment:**
   ```bash
   ./scripts/docker-deploy-e8.sh
   ```

2. **Access Frontend:**
   - Open `http://localhost:5173`
   - Navigate to "AI Agent Hub"
   - Click "Workflows" tab

3. **Test Workflow:**
   - Start a workflow (e.g., "Risk Score Explanation")
   - Verify step-by-step execution
   - Test approval gates for R2/R3 workflows

---

**Docker Deployment Status**: ✅ **READY**

All Docker configurations are complete. Run the deployment script or follow manual steps above to deploy E8.
