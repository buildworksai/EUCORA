# P4.3 Load Testing - Quick Execution Guide

**SPDX-License-Identifier: Apache-2.0**
**Date**: Jan 22, 2026
**Status**: Ready to Execute
**Timeline**: Jan 25-26, 2026

---

## Quick Start (5 minutes)

### 1. Install Locust
```bash
cd /Users/raghunathchava/code/EUCORA
pip install locust
```

### 2. Start Backend
```bash
# Terminal 1: Start all services
docker-compose -f docker-compose.dev.yml up

# Wait for services to be ready (~30 seconds)
# Confirm: http://localhost:8000/api/v1/health/ returns 200
```

### 3. Create Test Users
```bash
# Terminal 2: Create test user accounts
docker-compose -f docker-compose.dev.yml exec eucora-api python -c "
from django.contrib.auth.models import User
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')
import django
django.setup()

# Create test users if they don't exist
User.objects.get_or_create(username='loadtest_user', defaults={'password': 'test123'})
User.objects.get_or_create(username='cab_approver', defaults={'password': 'test123'})
User.objects.get_or_create(username='publisher_user', defaults={'password': 'test123'})
print('✅ Test users created')
"
```

### 4. Run Load Test
```bash
# Terminal 3: Start Locust load generator
cd /Users/raghunathchava/code/EUCORA
locust -f tests/load_tests/locustfile.py \
  --headless \
  -u 100 \
  -r 10 \
  -t 5m \
  --host http://localhost:8000 \
  --csv results/scenario1_deployments
```

**Expected Output**:
```
[2026-01-25 10:00:00,000] Starting web interface at http://0.0.0.0:8089
[2026-01-25 10:00:05,000] 100 concurrent Locust users hatched
[2026-01-25 10:05:00,000] Stopping test (time limit reached)

Type   Name                 # reqs      # fails  Avg     Min     Max
───────────────────────────────────────────────────────────────
POST   /api/v1/deployments/  250         0       145ms   50ms    450ms
GET    /api/v1/deployments/  75          0       120ms   40ms    300ms
GET    /api/v1/deployments/{id}/  50   0       110ms   35ms    280ms
───────────────────────────────────────────────────────────────
Total                        375         0       135ms   35ms    450ms
```

---

## Scenario Execution Commands

### Scenario 1: Concurrent Deployments (5 minutes)

**What it tests**: Multiple teams creating deployments simultaneously
**Users**: 100 concurrent
**Expected RPS**: 50-100 requests/sec
**Target**: <200ms p50, <500ms p99

```bash
locust -f tests/load_tests/locustfile.py \
  --headless \
  -u 100 \
  -r 10 \
  -t 5m \
  --host http://localhost:8000 \
  --csv results/scenario1_deployments
```

**Parse Results**:
```bash
python3 << 'EOF'
import pandas as pd
df = pd.read_csv('results/scenario1_deployments_stats.csv')
print(df[['Name', 'Request Count', 'Failure Count', 'Median Response Time', 'Max Response Time']])
EOF
```

---

### Scenario 2: CAB Approval Backlog (5 minutes)

**What it tests**: CAB reviewers approving 100+ pending deployments
**Users**: 50 concurrent CAB reviewers
**Expected RPS**: 80-120 requests/sec
**Target**: <1s for listing 100+ items, <200ms for approve/reject

```bash
locust -f tests/load_tests/locustfile.py \
  --headless \
  -u 50 \
  -r 5 \
  -t 5m \
  --host http://localhost:8000 \
  --csv results/scenario2_cab_approvals
```

---

### Scenario 3: Connector Scaling (5 minutes)

**What it tests**: Publishing to 5 execution planes in parallel
**Users**: 200 concurrent publishers
**Expected RPS**: 150-200 requests/sec
**Target**: <200ms per publish operation

```bash
locust -f tests/load_tests/locustfile.py \
  --headless \
  -u 200 \
  -r 20 \
  -t 5m \
  --host http://localhost:8000 \
  --csv results/scenario3_connectors
```

---

### Scenario 4: Burst Load - Interactive Web UI (4 minutes peak)

**What it tests**: System resilience under 1000+ concurrent users
**Peak RPS**: 10,000+ requests/sec
**Target**: <1s p99 response time, ≥98% success

```bash
# Start web UI (no headless, interactive ramp-up)
locust -f tests/load_tests/locustfile.py --host http://localhost:8000

# Open http://localhost:8089 in browser
# Step 1: Set "Number of users": 1000
# Step 2: Set "Spawn rate": 100 (will ramp up 100 users/sec = 10 seconds to 1000)
# Step 3: Click "Start swarming"
# Step 4: Let it run for 2-3 minutes at peak load
# Step 5: Click "Stop" to end test
```

---

## Monitoring During Tests

### Terminal 2: Monitor Backend Resource Usage
```bash
# Watch CPU, memory, network in real-time
docker stats eucora-api eucora-db eucora-celery-worker
```

**Expected Output**:
```
NAME              CPU %    MEM USAGE / LIMIT
eucora-api        15-25%   250MB / 4GB
eucora-db         5-10%    200MB / 4GB
eucora-celery     5-8%     150MB / 4GB
```

### Terminal 4: Monitor Database Connection Pool
```bash
# Check active connections (watch for exhaustion)
docker exec eucora-db psql -U postgres -c \
  "SELECT count(*) as active_connections FROM pg_stat_activity;"

# Watch in real-time
while true; do
  docker exec eucora-db psql -U postgres -c \
    "SELECT count(*) FROM pg_stat_activity;" 2>/dev/null | grep -A1 count
  sleep 2
done
```

**Expected Behavior**:
- Ramp up phase: Connections increase from 10 → 50
- Sustained load: Stable at 40-60 connections
- No "QueuePool timeout" errors in backend logs

---

## Interpreting Results

### CSV Output Files

After each scenario, Locust generates 3 CSV files:

1. **scenario{N}_stats.csv** - Per-endpoint statistics
   ```
   Name,# requests,# failures,Median response time,Average response time,Min response time,Max response time
   POST /api/v1/deployments/,250,0,145,150,50,450
   GET /api/v1/deployments/,75,0,120,125,40,300
   ```

2. **scenario{N}_stats_history.csv** - Time-series data (1-second granularity)
   ```
   Time,Type,Name,# requests,# failures,Median response time
   1705...000,POST,/api/v1/deployments/,50,0,140
   1705...000,GET,/api/v1/deployments/,15,0,115
   ```

3. **scenario{N}_failures.csv** - All failed requests with error details

### Success Criteria Checklist

```
Scenario 1: Concurrent Deployments
  ✓ Request Count ≥ 375 (5 min × 75 req/sec avg)
  ✓ Failure Count = 0 (100% success)
  ✓ Median Response Time < 200ms
  ✓ Max Response Time < 500ms (p99)

Scenario 2: CAB Approvals
  ✓ Request Count ≥ 400 (5 min × 80 req/sec avg)
  ✓ Failure Count = 0 (100% success)
  ✓ List operations: <1000ms median
  ✓ Approve/Reject: <200ms median

Scenario 3: Connector Scaling
  ✓ Request Count ≥ 750 (5 min × 150 req/sec avg)
  ✓ Failure Count ≤ 5 (≥99% success)
  ✓ All 5 planes active simultaneously
  ✓ Publish operations: <200ms median

Scenario 4: Burst Load
  ✓ Request Count ≥ 10,000 (peak 10k req/sec)
  ✓ Failure Count ≤ 200 (≥98% success)
  ✓ Response time <1000ms at p99
  ✓ No cascading failures or crashes
```

---

## Troubleshooting

### Problem: "Connection refused" errors

**Symptom**: Locust shows `500+ failures, error: Connection refused`

**Solution**:
1. Verify backend is running: `curl http://localhost:8000/api/v1/health/`
2. Wait 30 seconds for services to fully start
3. Verify test users exist in database
4. Check backend logs: `docker logs eucora-api | tail -20`

### Problem: "QueuePool timeout" in backend logs

**Symptom**: `sqlalchemy.pool.QueuePool.timeout exceeded`

**Solution**:
1. Database connection pool is exhausted
2. Increase pool size: Edit `backend/config/settings.py`
   ```python
   DATABASES['default']['CONN_MAX_AGE'] = 600  # Increase connection lifetime
   ```
3. Restart backend: `docker-compose restart eucora-api`
4. Re-run scenario with fewer concurrent users

### Problem: Response time suddenly spikes after 2-3 minutes

**Symptom**: Median response time jumps from 150ms to 2000ms

**Solution**:
1. Memory leak in application
2. Check Celery task queue: `docker logs eucora-celery-worker | grep queue`
3. Profile slow queries: `django-extensions shell_plus --quiet --ipython`
4. Check database: `SELECT count(*) FROM pg_stat_activity;`

### Problem: "Authentication failed" errors

**Symptom**: 401 errors on all requests

**Solution**:
1. Verify test users were created: `docker-compose exec eucora-api python manage.py shell`
2. Check password: `User.objects.filter(username='loadtest_user').first()`
3. Regenerate token (if token-based auth): Run test user creation script again

---

## After Test Completion

### Step 1: Collect Results
```bash
# Create results directory if needed
mkdir -p results/

# List all CSV files generated
ls -la results/scenario*_stats.csv
```

### Step 2: Aggregate Results
```bash
python3 << 'EOF'
import pandas as pd
import glob

# Load all scenario results
scenarios = {}
for file in glob.glob('results/scenario*_stats.csv'):
    name = file.split('/')[-1].split('_stats')[0]
    scenarios[name] = pd.read_csv(file)

# Print summary
for scenario, df in scenarios.items():
    print(f"\n{scenario.upper()}")
    print(f"  Total Requests: {df['# requests'].sum()}")
    print(f"  Total Failures: {df['# failures'].sum()}")
    print(f"  Avg Response: {df['Median response time'].mean():.0f}ms")
    print(f"  Max Response: {df['Max response time'].max():.0f}ms")
EOF
```

### Step 3: Create Report
```bash
# Generate P4-LOAD-TESTING-RESULTS.md in /reports/
# Include:
# - Baseline metrics for each scenario
# - Bottleneck analysis
# - Optimization recommendations
# - Pass/fail criteria assessment
```

---

## Performance Baselines (Expected Results)

| Scenario | Users | RPS | p50 | p99 | Success |
|----------|-------|-----|-----|-----|---------|
| Deployments | 100 | 75 | 150ms | 450ms | 100% |
| CAB Approvals | 50 | 100 | 140ms | 400ms | 100% |
| Connectors | 200 | 175 | 160ms | 480ms | 99.5% |
| Burst Peak | 1000 | 10,000 | 400ms | 950ms | 98% |

If results significantly differ from baselines, bottleneck analysis is needed before moving to next phase.

---

## Success Criteria for Phase Completion

✅ **All 3 baseline scenarios complete** (Scenarios 1-3)
✅ **Baseline metrics match targets** (see tables above)
✅ **Burst load scenario sustains 10,000 req/sec**
✅ **No system crashes or cascading failures**
✅ **Results aggregated in P4-LOAD-TESTING-RESULTS.md**
✅ **Bottleneck analysis documented with recommendations**

---

**Ready to execute**: Jan 25, 2026
**Timeline**: 5-6 hours total
**Next Phase**: P4.4 (TODO Resolution) on Jan 27
