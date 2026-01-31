# E8: AI Agent Workflows Deployment Guide

**SPDX-License-Identifier**: Apache-2.0
**Date**: January 31, 2026
**Status**: Ready for Deployment

---

## Prerequisites

- ✅ E1 (Document Management & RAG) - Complete
- ✅ E3 (RBAC) - Complete
- ✅ E7 (pgvector) - Complete
- ✅ PostgreSQL with pgvector extension
- ✅ Redis server running

---

## Step 1: Install Dependencies

### Backend Dependencies

Django Channels and channels-redis have been added to `pyproject.toml`. Install them:

```bash
cd backend
pip install channels channels-redis
# Or if using pip from pyproject.toml:
pip install -e .
```

**Dependencies Added:**
- `channels~=4.0.0` - Django Channels for WebSocket support
- `channels-redis~=4.2.0` - Redis backend for Channels

---

## Step 2: Database Migration

### Ensure pgvector Extension

The migration requires the pgvector extension (from E7). Verify it's installed:

```sql
-- Connect to PostgreSQL
psql -U eucora_user -d eucora

-- Check if extension exists
SELECT * FROM pg_extension WHERE extname = 'vector';

-- If not installed, create it:
CREATE EXTENSION IF NOT EXISTS vector;
```

### Run Migrations

```bash
cd backend
python manage.py migrate ai_agents
```

**Expected Output:**
```
Running migrations:
  Applying ai_agents.0006_workflow_models... OK
```

**Migration Creates:**
- `WorkflowDefinition` table
- `WorkflowExecution` table
- `WorkflowStep` table
- Indexes for performance
- Foreign key relationships

---

## Step 3: Seed Workflow Definitions

Seed the default workflow definitions for all agent types:

```bash
cd backend
python manage.py seed_workflows
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

**Workflows Created:**
1. **Packaging Assistant** (R2) - 5 steps
2. **CAB Evidence Generator** (R3) - 4 steps
3. **Risk Explainer** (R1) - 3 steps
4. **Deployment Advisor** (R3) - 5 steps
5. **Compliance Analyzer** (R2) - 3 steps
6. **Incident Responder** (R2) - 4 steps

---

## Step 4: Django Channels Configuration (Optional - WebSocket Support)

### Configuration Status

✅ **Already Configured:**
- `channels` added to `INSTALLED_APPS` in `backend/config/settings/base.py`
- `CHANNEL_LAYERS` configured with Redis backend
- `asgi.py` updated with ProtocolTypeRouter for WebSocket routing

### Verify Configuration

Check that Channels is properly configured:

```python
# In Django shell: python manage.py shell
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
print(channel_layer)  # Should show RedisChannelLayer instance
```

### WebSocket Endpoint

WebSocket connections are available at:
```
ws://localhost:8000/ws/ai/executions/{execution_id}/
```

**Frontend Integration:**
The `useWorkflowWebSocket` hook in `frontend/src/lib/api/hooks/useWorkflow.ts` is ready but requires a WebSocket client library. Example implementation:

```typescript
import { useEffect, useState } from 'react';

export function useWorkflowWebSocket(executionId: string) {
  const [connected, setConnected] = useState(false);
  const [lastUpdate, setLastUpdate] = useState<any>(null);

  useEffect(() => {
    const ws = new WebSocket(`ws://localhost:8000/ws/ai/executions/${executionId}/`);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => setConnected(false);
    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);
      setLastUpdate(data);
    };

    return () => ws.close();
  }, [executionId]);

  return { connected, lastUpdate };
}
```

---

## Step 5: Verify Installation

### Check API Endpoints

```bash
# List workflows
curl http://localhost:8000/api/v1/ai/workflows/

# Get workflow detail
curl http://localhost:8000/api/v1/ai/workflows/{workflow_id}/

# List executions (requires authentication)
curl -H "Authorization: Bearer {token}" http://localhost:8000/api/v1/ai/executions/
```

### Check Database

```sql
-- Verify tables created
SELECT table_name FROM information_schema.tables
WHERE table_schema = 'public'
AND table_name LIKE 'ai_agents_workflow%';

-- Should show:
-- ai_agents_workflowdefinition
-- ai_agents_workflowexecution
-- ai_agents_workflowstep

-- Verify workflows seeded
SELECT agent_type, name, risk_level FROM ai_agents_workflowdefinition;
-- Should show 6 workflows
```

---

## Step 6: Test Workflow Execution

### Via UI

1. Navigate to `/ai-agents` in the frontend
2. Click the **"Workflows"** tab
3. Select a workflow (e.g., "Risk Score Explanation")
4. Click **"Start Workflow"**
5. Navigate to the execution page
6. Verify step-by-step execution
7. For R2/R3 workflows, test approval gates

### Via API

```bash
# Start a workflow
curl -X POST http://localhost:8000/api/v1/ai/workflows/{workflow_id}/start/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "input_data": {
      "package_name": "test-package",
      "application_name": "Test App"
    }
  }'

# Approve a step (if workflow is awaiting approval)
curl -X POST http://localhost:8000/api/v1/ai/executions/{execution_id}/approve/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "notes": "Approved after review"
  }'
```

---

## Troubleshooting

### Migration Fails: pgvector Not Found

**Error:**
```
ModuleNotFoundError: No module named 'pgvector'
```

**Solution:**
```bash
pip install pgvector
# Or ensure E7 dependencies are installed
pip install -e .[dev]
```

### Migration Fails: Extension Not Installed

**Error:**
```
ERROR: extension "vector" does not exist
```

**Solution:**
```sql
-- Connect to PostgreSQL as superuser
CREATE EXTENSION IF NOT EXISTS vector;
```

### Channels Import Error

**Error:**
```
ImportError: cannot import name 'ProtocolTypeRouter' from 'channels.routing'
```

**Solution:**
```bash
pip install --upgrade channels
```

### WebSocket Connection Fails

**Check:**
1. Redis is running: `redis-cli ping` (should return `PONG`)
2. CHANNEL_LAYERS configuration is correct
3. ASGI application is being used (not WSGI)
4. Allowed hosts includes WebSocket origin

**For Development:**
```python
# In settings/development.py
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '*']  # For dev only
```

---

## Configuration Files Modified

### Backend

1. **`backend/pyproject.toml`**
   - Added `channels~=4.0.0`
   - Added `channels-redis~=4.2.0`

2. **`backend/config/settings/base.py`**
   - Added `"channels"` to `INSTALLED_APPS`
   - Added `CHANNEL_LAYERS` configuration

3. **`backend/config/asgi.py`**
   - Updated to use `ProtocolTypeRouter`
   - Added WebSocket routing

4. **`backend/apps/ai_agents/urls.py`**
   - Added workflow router URLs

### Frontend

1. **`frontend/src/routes/ai/contracts.ts`**
   - Extended with workflow types

2. **`frontend/src/lib/api/hooks/useWorkflow.ts`**
   - Added workflow API hooks

3. **`frontend/src/components/ai/`**
   - Added workflow visualization components

4. **`frontend/src/routes/AIAgentHub.tsx`**
   - Added workflows and executions tabs

5. **`frontend/src/App.tsx`**
   - Added workflow page route

---

## Post-Deployment Verification

### Checklist

- [ ] Migrations applied successfully
- [ ] 6 workflow definitions seeded
- [ ] API endpoints responding
- [ ] Frontend workflows tab visible
- [ ] Can start a workflow
- [ ] Step-by-step execution visible
- [ ] Approval gates work for R2/R3
- [ ] Policy context displays correctly
- [ ] WebSocket connections work (if Channels configured)

### Performance Checks

```bash
# Check database indexes
python manage.py dbshell
\d ai_agents_workflowexecution
# Should show indexes on status, initiated_by, correlation_id, etc.

# Check Redis connectivity (for Channels)
python manage.py shell
from channels.layers import get_channel_layer
channel_layer = get_channel_layer()
channel_layer.send('test-channel', {'type': 'test.message', 'text': 'hello'})
# Should not raise errors
```

---

## Rollback Procedure

If issues occur, rollback steps:

```bash
# 1. Rollback migration
python manage.py migrate ai_agents 0005

# 2. Remove workflow definitions
python manage.py shell
from apps.ai_agents.workflows.models import WorkflowDefinition
WorkflowDefinition.objects.all().delete()

# 3. Remove Channels (if needed)
# Comment out 'channels' in INSTALLED_APPS
# Revert asgi.py to simple get_asgi_application()
```

---

## Next Steps

After successful deployment:

1. **Monitor Workflow Executions**
   - Check execution success rates
   - Monitor approval gate usage
   - Track policy context retrieval performance

2. **Configure Workflow Definitions**
   - Customize workflows for your organization
   - Add organization-specific steps
   - Adjust risk levels as needed

3. **Integrate with ALM Agents (E10-E21)**
   - E8 provides the foundation for all ALM agents
   - Each agent (CMDB, Change Communications, etc.) will use workflow engine

4. **WebSocket Optimization** (if using Channels)
   - Monitor WebSocket connection counts
   - Tune CHANNEL_LAYERS capacity and expiry
   - Consider connection pooling for high traffic

---

**Deployment Status**: ✅ Ready

All components are implemented and configured. Follow the steps above to deploy E8 AI Agent Workflows.
