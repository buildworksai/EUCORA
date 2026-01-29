# Docker Rebuild Instructions — Quick Reference

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

---

## 🚀 Quick Start (Automated Script)

```bash
cd /Users/raghunathchava/code/EUCORA
./scripts/rebuild-docker.sh
```

**Timeline:** ~5-10 minutes (includes verification)

---

## 📋 Manual Steps (If Script Fails)

### Step 1: Stop Containers
```bash
cd /Users/raghunathchava/code/EUCORA
docker compose down
```

### Step 2: Rebuild (No Cache)
```bash
docker compose build web --no-cache
docker compose build celery-worker --no-cache
docker compose build celery-beat --no-cache
```

### Step 3: Start Containers
```bash
docker compose up -d
```

### Step 4: Verify Running
```bash
docker compose ps
```

**Expected:** All containers show "Up" (not "Exited" or "Restarting")

---

## ✅ Verification Checklist

### 1. Check Django Version
```bash
docker compose exec web python -c "import django; print(django.VERSION)"
```
**Expected:** `(5, 1, 15, 'final', 0)`

### 2. Check django-celery-beat Version
```bash
docker compose exec web python -c "import django_celery_beat; print(django_celery_beat.__version__)"
```
**Expected:** `2.8.1`

### 3. Check requests Version
```bash
docker compose exec web python -c "import requests; print(requests.__version__)"
```
**Expected:** `2.32.5`

### 4. Verify Migrations Applied
```bash
docker compose exec web python manage.py showmigrations | grep -E "(evidence_store|packaging_factory|cab_workflow)"
```

**Expected Output:**
```
evidence_store
  [X] 0001_initial
  [X] 0002_add_is_demo
  [X] 0003_add_p5_models
  [X] 0004_seed_risk_factors_v1
  [X] 0005_p5_5_defense_in_depth
  [X] 0006_seed_p5_5_data
  [X] 0007_rename_evidence_st_inciden_idx_...    ← NEW ✅

packaging_factory
  [X] 0001_initial
  [X] 0002_rename_packaging_p_package_idx_...    ← NEW ✅

cab_workflow
  [X] 0001_initial
  [X] 0002_add_is_demo
  [X] 0003_add_external_change_request_id
  [X] 0005_p5_cab_workflow                       ← NEW ✅
  [X] 0006_rename_cab_workflow_cab_req_idx_...   ← NEW ✅
```

### 5. Run Django System Check
```bash
docker compose exec web python manage.py check --deploy
```
**Expected:** `System check identified no issues (0 silenced).` (warnings OK)

### 6. Test Health Endpoint
```bash
curl http://localhost:8000/api/v1/health/liveness/
```
**Expected:** HTTP 200 OK with `{"status":"healthy",...}`

### 7. Check Logs for Errors
```bash
docker compose logs web | tail -50
docker compose logs celery-worker | tail -20
docker compose logs celery-beat | tail -20
```
**Expected:** No error messages, no crash loops

---

## 🐛 Troubleshooting

### Problem: Containers Crash on Startup

**Diagnosis:**
```bash
docker compose logs web | grep -i "error\|traceback"
```

**Common Issues:**

#### Issue 1: Migration Errors
```bash
# Check migration status
docker compose exec web python manage.py showmigrations

# Manually apply if needed
docker compose exec web python manage.py migrate evidence_store
docker compose exec web python manage.py migrate packaging_factory
docker compose exec web python manage.py migrate cab_workflow
```

#### Issue 2: Django Version Wrong
```bash
# Verify Django version in container
docker compose exec web pip show django

# If wrong, rebuild with no cache
docker compose down
docker compose build web --no-cache --pull
docker compose up -d
```

#### Issue 3: Database Connection Issues
```bash
# Restart database
docker compose restart db

# Wait 10 seconds
sleep 10

# Restart web
docker compose restart web
```

---

### Problem: Migrations Show Unapplied `[ ]`

**Solution:**
```bash
# Force apply migrations
docker compose exec web python manage.py migrate --fake-initial
```

---

### Problem: Health Check Returns 500

**Diagnosis:**
```bash
docker compose exec web python manage.py check
docker compose logs web | tail -30
```

**Solution:** Check logs for specific error, likely migration or database issue

---

## 🎯 Success Criteria

✅ All containers "Up" status
✅ Django 5.1.15 installed
✅ django-celery-beat 2.8.1 installed
✅ requests 2.32.5 installed
✅ All 4 new migrations applied ([X])
✅ System check: 0 errors
✅ Health check: 200 OK
✅ No crash loops in logs

---

## 📊 After Successful Rebuild

### Run Backend Tests
```bash
docker compose exec web pytest backend/apps/cab_workflow/tests/test_p5_3_api.py -v
```
**Expected:** 32/32 tests passing

### Run Full Test Suite (Optional)
```bash
docker compose exec web pytest -v
```
**Expected:** High pass rate (22/24 or better)

---

## 📝 Report Success

When rebuild is successful, notify with:

**"Docker rebuild complete - all containers verified"**

Include output of:
```bash
docker compose ps
docker compose exec web python manage.py showmigrations | grep -E "(0007|0002|0005|0006)"
curl http://localhost:8000/api/v1/health/liveness/
```

---

## 📚 Documentation

- **Full Details:** [backend/reports/COMMIT-SUMMARY-2026-01-25.md](backend/reports/COMMIT-SUMMARY-2026-01-25.md)
- **Troubleshooting:** [backend/reports/docker-crash-fix-2026-01-24.md](backend/reports/docker-crash-fix-2026-01-24.md)
- **Migration Details:** [backend/reports/django-51-migration-fix-2026-01-24.md](backend/reports/django-51-migration-fix-2026-01-24.md)

---

## ⏭️ Next Steps After Rebuild

1. ✅ Verify all tests pass
2. ✅ Monitor containers for 24 hours
3. 🚀 Proceed to **Phase P6: Connector Integration MVP**

**Kickoff Command:** Say **"proceed to P6"** when ready

---

**Generated:** 2026-01-25
**Status:** Ready for Docker rebuild
**Timeline:** 5-10 minutes
