# P4.3 Load Testing Plan

**SPDX-License-Identifier: Apache-2.0**  
**Status**: ✅ READY TO EXECUTE  
**Phase**: P4.3 Testing & Quality  
**Target Completion**: Jan 25-26, 2026

---

## Overview

Load testing validates system performance under sustained and burst loads using **Locust** - an open-source load testing framework.

**Key Metrics**:
- Target: **10,000 requests/sec** sustained
- Response time: **<500ms** at p50, **<1s** at p95
- Success rate: **≥99%** under load
- No timeouts or connection errors

---

## Test Scenarios

### Scenario 1: Concurrent Deployments

**Simulates**: Multiple teams deploying apps simultaneously  
**User Type**: `DeploymentUser`  
**Load Profile**:
- 100 concurrent users
- Create 3 deployments per user
- ~300 requests total
- Expected RPS: ~50-100 req/sec

**Tasks**:
```python
@task(3) create_deployment()     # 75% of traffic
@task(1) list_deployments()      # 17% of traffic  
@task(1) get_deployment_details()  # 8% of traffic
```

**Success Criteria**:
- ✅ 100% requests succeed
- ✅ Average response time <200ms
- ✅ p99 response time <500ms
- ✅ 0 timeouts or connection errors

**Command**:
```bash
locust -f tests/load_tests/locustfile.py \
  --headless \
  -u 100 \
  -r 10 \
  -t 5m \
  --host http://localhost:8000 \
  --csv results/scenario1_deployments
```

---

### Scenario 2: CAB Approval Backlog

**Simulates**: CAB reviewers approving/rejecting pending deployments  
**User Type**: `CABApprovalUser`  
**Load Profile**:
- 50 concurrent CAB reviewers
- Each approves ~5 deployments
- 100+ pending approvals queued
- Expected RPS: ~80-120 req/sec

**Tasks**:
```python
@task(4) list_pending_approvals()  # 57% of traffic (large list)
@task(3) approve_deployment()      # 43% of traffic
@task(1) reject_deployment()       # (included in 43%)
```

**Success Criteria**:
- ✅ List 100+ pending items in <1s
- ✅ Approve/reject in <200ms
- ✅ ≥99% approval success rate
- ✅ No data loss or approval duplicates

**Command**:
```bash
locust -f tests/load_tests/locustfile.py \
  --headless \
  -u 50 \
  -r 10 \
  -t 5m \
  --host http://localhost:8000 \
  --csv results/scenario2_cab_approvals
```

---

### Scenario 3: Connector Scaling

**Simulates**: Publishing to multiple execution planes in parallel  
**User Type**: `ConnectorPublishingUser`  
**Load Profile**:
- 200 concurrent publishers
- Publish to 5 execution planes (Intune, Jamf, SCCM, Landscape, Ansible)
- ~1000 publish operations total
- Expected RPS: ~150-200 req/sec

**Tasks**:
```python
@task(2) publish_to_intune()       # 28% of traffic
@task(2) publish_to_jamf()         # 28% of traffic
@task(2) publish_to_sccm()         # 28% of traffic
@task(1) query_connector_status()  # 14% of traffic
@task(1) remediate_deployment()    # (included in 14%)
```

**Success Criteria**:
- ✅ Publish to all 5 planes simultaneously
- ✅ <200ms response per publish operation
- ✅ p95 <500ms (accounting for backend processing)
- ✅ ≥99% success rate across all planes

**Command**:
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

### Scenario 4: Burst Load (Optional)

**Simulates**: Sudden spike in deployment traffic  
**User Type**: `HighLoadDeploymentUser`  
**Load Profile**:
- Ramp up to 1000 concurrent users over 1 minute
- Sustain for 2 minutes
- Ramp down over 1 minute
- Expected peak RPS: **10,000+ req/sec**

**Tasks**:
```python
@task create_deployment_burst()  # 100% of traffic
```

**Success Criteria**:
- ✅ Handle 10,000+ req/sec without dropping requests
- ✅ <1s response time at p99 even under peak load
- ✅ ≥98% success rate (acceptable for burst scenario)
- ✅ No cascading failures or system crashes

**Command** (interactive with Web UI):
```bash
locust -f tests/load_tests/locustfile.py \
  --host http://localhost:8000 \
  --web
# Then open http://localhost:8089 and ramp up to 1000 users
```

---

## Test Execution Plan

### Phase 1: Setup (30 minutes)
1. ✅ Create `tests/load_tests/locustfile.py` (4 User classes + event handlers)
2. ⏳ Install Locust: `pip install locust`
3. ⏳ Start backend: `docker-compose -f docker-compose.dev.yml up`
4. ⏳ Create test users in database (loadtest_user, cab_approver, publisher_user)

### Phase 2: Baseline (2.5 hours)
1. ⏳ Run Scenario 1 (Concurrent Deployments): 5 minutes
2. ⏳ Run Scenario 2 (CAB Approvals): 5 minutes
3. ⏳ Run Scenario 3 (Connector Scaling): 5 minutes
4. ⏳ Analyze results & identify bottlenecks

### Phase 3: Stress Testing (1 hour)
1. ⏳ Run Scenario 4 (Burst Load): 4 minutes peak
2. ⏳ Check for memory leaks: `docker stats eucora-api`
3. ⏳ Verify no connection pool exhaustion
4. ⏳ Verify database connection limits not exceeded

### Phase 4: Reporting (1 hour)
1. ⏳ Aggregate all Locust CSV results
2. ⏳ Create performance baseline report
3. ⏳ Identify optimization opportunities
4. ⏳ Document recommendations

**Total Estimated Time**: 5-6 hours

---

## Performance Baseline Targets

| Scenario | Users | RPS Target | p50 Response | p99 Response | Success Rate |
|----------|-------|-----------|--------------|--------------|--------------|
| **Concurrent Deployments** | 100 | 50-100 | <200ms | <500ms | ≥99% |
| **CAB Approvals** | 50 | 80-120 | <200ms | <500ms | ≥99% |
| **Connector Scaling** | 200 | 150-200 | <200ms | <500ms | ≥99% |
| **Burst Load** | 1000 | 10,000+ | <500ms | <1000ms | ≥98% |

---

## Infrastructure Requirements

### Backend Service
- CPU: 4 cores (recommend for Docker)
- Memory: 4GB
- Database: PostgreSQL with 100+ connections
- Celery workers: 4 (for async tasks)

### Locust Load Generator
- CPU: 2 cores (separate machine recommended)
- Memory: 2GB
- Network: Minimum 1Gbps to backend

### Monitoring During Tests
```bash
# Terminal 1: Locust load generator
locust -f tests/load_tests/locustfile.py --headless -u 100 -r 10 -t 5m

# Terminal 2: Monitor backend
docker stats eucora-api --no-stream

# Terminal 3: Monitor database
docker exec eucora-db psql -U postgres -c \
  "SELECT count(*) as connections FROM pg_stat_activity;"
```

---

## Expected Bottlenecks & Mitigations

### Bottleneck 1: Database Connection Pool Exhaustion
- **Symptom**: "QueuePool timeout" errors at 500+ concurrent users
- **Mitigation**: Increase `DATABASES['default']['CONN_MAX_AGE']` to 600s
- **Verify**: Monitor `SELECT count(*) FROM pg_stat_activity`

### Bottleneck 2: API Response Time Degradation
- **Symptom**: Response times grow from 200ms (100 users) to 5000ms (1000 users)
- **Mitigation**: Optimize querysets with `.select_related()` / `.prefetch_related()`
- **Verify**: Profile slow queries with `django.db.connection.queries`

### Bottleneck 3: Memory Leaks in Workers
- **Symptom**: `docker stats` shows memory growing unbounded
- **Mitigation**: Verify no circular references in signal handlers
- **Verify**: Monitor memory over 10+ minute test runs

### Bottleneck 4: Celery Task Queue Backlog
- **Symptom**: Deployment approval tasks queue up, not processing
- **Mitigation**: Increase number of Celery workers or optimize task time
- **Verify**: Monitor `docker logs eucora-celery-worker` for queue length

---

## Success Criteria for P4.3 Completion

✅ **All 3 baseline scenarios PASS**:
- Scenario 1: 100 users, <200ms p50, <500ms p99
- Scenario 2: 50 users, <1s for list_pending, <200ms for approve
- Scenario 3: 200 users, <200ms per publish, all 5 planes active

✅ **Burst load scenario SUSTAINS 10,000 req/sec** for ≥1 minute

✅ **No system crashes or cascading failures** observed

✅ **All 3 CSV result files generated**: `results/scenario{1,2,3}_{*}.csv`

✅ **Bottleneck analysis documented** with recommended optimizations

✅ **Report generated**: `/reports/P4-LOAD-TESTING-RESULTS.md`

---

## Next Steps

1. Execute Scenario 1 (Concurrent Deployments) as baseline
2. Analyze results against target thresholds
3. Execute Scenarios 2-4 in sequence
4. Aggregate results and identify top 3 optimization opportunities
5. Document in P4-LOAD-TESTING-RESULTS.md with recommendations
6. Proceed to P4.4 (TODO Resolution) once all scenarios complete

---

## Appendix: Locust Quick Reference

### Start Interactive Web UI
```bash
locust -f tests/load_tests/locustfile.py --host http://localhost:8000
# Open http://localhost:8089
```

### Run Headless with CSV Output
```bash
locust -f tests/load_tests/locustfile.py \
  --headless \
  -u 100 \
  -r 10 \
  -t 5m \
  --host http://localhost:8000 \
  --csv results/test_results
```

### Parameters
- `-u 100` : 100 concurrent users
- `-r 10` : Ramp up 10 users per second (total 10s to reach 100)
- `-t 5m` : Run for 5 minutes
- `--csv results/test` : Output CSV to `results/test_*.csv`
- `--headless` : No web UI, CLI only

### Result Files Generated
- `results/test_stats.csv` : Per-endpoint statistics (RPS, response time, failures)
- `results/test_stats_history.csv` : Time-series data (1-second granularity)
- `results/test_failures.csv` : All failures with error messages

### Parsing Results
```python
import pandas as pd
df = pd.read_csv('results/test_stats.csv')
print(df.groupby('Name')[['Request Count', 'Failure Count', 'Median Response Time']].sum())
```

---

**Status**: Ready to execute  
**Timeline**: Jan 25-26, 2026  
**Owner**: QA Engineer  
**Next Review**: After Scenario 1 baseline complete
