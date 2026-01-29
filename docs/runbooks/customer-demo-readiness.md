# Customer Demo Readiness Guide

**SPDX-License-Identifier: Apache-2.0**
**Version**: 1.0.0
**Last Updated**: January 8, 2026

---

## 🎯 Overview

This guide ensures EUCORA is **bulletproof for customer demos**. The system is designed to:
- ✅ **Never fail completely** - Server starts even if seeding fails
- ✅ **Auto-recover** - Automatically seeds data if missing
- ✅ **Persist data** - Data survives container rebuilds
- ✅ **Health checks** - Verify readiness before demos

---

## 🚀 Pre-Demo Checklist

### 1. Verify System Health

```bash
# Check demo readiness
curl http://localhost:8000/health/demo-ready

# Expected response:
{
  "demo_mode_enabled": true,
  "demo_data_exists": true,
  "demo_data_counts": {
    "assets": 100,
    "applications": 10,
    "deployments": 20,
    ...
  },
  "status": "ready"
}
```

### 2. Check Container Status

```bash
# All containers should be running
docker-compose ps

# Check logs for errors
docker-compose logs eucora-api | tail -50
```

### 3. Verify Demo Data

```bash
# Quick check
./scripts/utilities/check-demo-data.sh

# Or via API
curl http://localhost:8000/api/v1/admin/demo-data-stats
```

---

## 🔧 System Resilience Features

### 1. Non-Blocking Entrypoint

The `entrypoint.sh` script:
- ✅ **Never exits** on seeding errors (only on critical DB failures)
- ✅ **Retries** critical operations (demo mode enable)
- ✅ **Logs warnings** but continues if seeding fails
- ✅ **Preserves existing data** on container restarts

### 2. Idempotent Seeding

All seeding operations are **idempotent**:
- ✅ Only creates missing records
- ✅ Safe to run multiple times
- ✅ Uses transactions for atomicity
- ✅ Handles race conditions

### 3. Automatic Recovery

On container start:
1. Checks if demo data exists
2. Seeds only if database is empty
3. Enables demo mode (with retries)
4. Starts server even if seeding fails

### 4. Health Check Endpoint

`/health/demo-ready` provides:
- Demo mode status
- Demo data counts
- Readiness status
- Actionable error messages

---

## 🆘 Emergency Recovery

### If Demo Breaks During Presentation

**Option 1: Emergency Recovery Script (Fastest)**

```bash
./scripts/utilities/emergency-demo-recovery.sh
```

This script:
- Checks current status
- Seeds minimum data if missing
- Enables demo mode
- Verifies recovery

**Option 2: Manual Recovery**

```bash
# Enable demo mode
docker-compose exec eucora-api python manage.py shell -c "
from apps.core.utils import set_demo_mode_enabled
set_demo_mode_enabled(True)
print('Demo mode enabled')
"

# Seed minimum data
docker-compose exec eucora-api python manage.py seed_demo_data \
  --assets 100 \
  --applications 10 \
  --deployments 20 \
  --users 5 \
  --events 100 \
  --batch-size 50
```

**Option 3: Via Admin UI**

1. Navigate to `http://localhost:5173/admin/demo-data`
2. Toggle "Demo Mode" to ON
3. Click "Seed Demo Data" with default values

---

## 🔄 Container Rebuild Safety

### Data Persistence

Demo data **persists across container rebuilds** because:

1. **Database Volume**: Data stored in Docker volume `postgres_data`
2. **Idempotent Seeding**: Only seeds if database is empty
3. **No Auto-Clear**: Entrypoint never uses `--clear-existing`

### Rebuild Process

```bash
# Rebuild containers (data persists)
docker-compose down
docker-compose build
docker-compose up -d

# Verify data still exists
curl http://localhost:8000/health/demo-ready
```

### Full Reset (Only if Needed)

```bash
# ⚠️ WARNING: This deletes all data
docker-compose down -v
docker-compose up -d
# System will auto-seed fresh data
```

---

## 📊 Monitoring During Demo

### Health Check Monitoring

```bash
# Watch health status
watch -n 5 'curl -s http://localhost:8000/health/demo-ready | jq'

# Or simple check
while true; do
  curl -s http://localhost:8000/health/demo-ready | jq '.status'
  sleep 5
done
```

### Log Monitoring

```bash
# Watch logs in real-time
docker-compose logs -f eucora-api

# Filter for errors
docker-compose logs eucora-api | grep -i error
```

---

## 🎯 Demo Scenarios

### Scenario 1: Fresh Start

```bash
# Start fresh system
docker-compose up -d

# Wait for startup (30-60 seconds)
sleep 60

# Verify readiness
curl http://localhost:8000/health/demo-ready
```

### Scenario 2: After Container Restart

```bash
# Restart containers
docker-compose restart

# Data persists automatically
# Verify after 30 seconds
sleep 30
curl http://localhost:8000/health/demo-ready
```

### Scenario 3: After Rebuild

```bash
# Rebuild (data persists)
docker-compose down
docker-compose build
docker-compose up -d

# Verify after startup
sleep 60
curl http://localhost:8000/health/demo-ready
```

### Scenario 4: Recovery from Failure

```bash
# Run emergency recovery
./scripts/utilities/emergency-demo-recovery.sh

# Verify recovery
curl http://localhost:8000/health/demo-ready
```

---

## 🛡️ Failure Modes & Recovery

### Failure: Seeding Errors

**Symptoms:**
- Health check shows `demo_data_exists: false`
- Logs show seeding errors

**Recovery:**
```bash
# Run emergency recovery
./scripts/utilities/emergency-demo-recovery.sh

# Or seed manually
docker-compose exec eucora-api python manage.py seed_demo_data \
  --assets 100 --applications 10 --deployments 20
```

### Failure: Demo Mode Disabled

**Symptoms:**
- Health check shows `demo_mode_enabled: false`
- No demo data visible in UI

**Recovery:**
```bash
# Enable demo mode
docker-compose exec eucora-api python manage.py shell -c "
from apps.core.utils import set_demo_mode_enabled
set_demo_mode_enabled(True)
"
```

### Failure: Database Connection

**Symptoms:**
- Health check returns 503
- Container logs show connection errors

**Recovery:**
```bash
# Check database container
docker-compose ps db

# Restart database
docker-compose restart db

# Wait for health
sleep 10
curl http://localhost:8000/health/ready
```

---

## ✅ Pre-Demo Verification Script

```bash
#!/bin/bash
# Quick pre-demo verification

echo "🔍 Pre-Demo Verification"
echo "======================"

# Check containers
echo -n "Containers: "
if docker-compose ps | grep -q "Up"; then
  echo "✅ Running"
else
  echo "❌ Not running"
  exit 1
fi

# Check demo readiness
echo -n "Demo Readiness: "
STATUS=$(curl -s http://localhost:8000/health/demo-ready | jq -r '.status')
if [ "$STATUS" = "ready" ]; then
  echo "✅ Ready"
else
  echo "❌ Not ready (status: $STATUS)"
  echo "Run: ./scripts/utilities/emergency-demo-recovery.sh"
  exit 1
fi

# Check demo mode
echo -n "Demo Mode: "
MODE=$(curl -s http://localhost:8000/health/demo-ready | jq -r '.demo_mode_enabled')
if [ "$MODE" = "true" ]; then
  echo "✅ Enabled"
else
  echo "❌ Disabled"
  exit 1
fi

# Check data
echo -n "Demo Data: "
DATA=$(curl -s http://localhost:8000/health/demo-ready | jq -r '.demo_data_exists')
if [ "$DATA" = "true" ]; then
  echo "✅ Exists"
else
  echo "❌ Missing"
  exit 1
fi

echo ""
echo "✅ System ready for demo!"
```

---

## 📝 Best Practices

1. **Always verify before demo**: Run health check
2. **Keep recovery script handy**: `emergency-demo-recovery.sh`
3. **Monitor logs**: Watch for errors during demo
4. **Don't panic**: System is designed to recover automatically
5. **Use health endpoint**: `/health/demo-ready` is your friend

---

## 🔗 Related Documentation

- [Demo Data Persistence](./demo-data-persistence.md)
- [Demo Data Troubleshooting](./demo-data-troubleshooting.md)
- [Emergency Recovery Script](../../scripts/utilities/emergency-demo-recovery.sh)

---

**Remember**: The system is designed to **never fail completely**. Even if seeding fails, the server starts and you can recover via the admin UI or recovery script.
