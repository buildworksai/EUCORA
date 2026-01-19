# Demo Data Persistence Guide

**SPDX-License-Identifier: Apache-2.0**  
**Version**: 1.0.0  
**Last Updated**: January 8, 2026

---

## Overview

Demo data in EUCORA is designed to **persist across container restarts**. The seeding system is **idempotent** - it only creates new records if the target count hasn't been reached, preserving your existing data.

---

## How It Works

### Idempotent Seeding

The `seed_demo_data()` function is now **idempotent**:

1. **Checks existing counts** before seeding
2. **Only creates missing records** up to the target count
3. **Preserves existing data** unless `--clear-existing` is explicitly used

### Entrypoint Behavior

The `entrypoint.sh` script:

1. **Checks if demo data exists** on container startup
2. **Only seeds if database is empty** (no demo data found)
3. **Preserves existing data** on subsequent restarts
4. **Never uses `--clear-existing`** automatically

---

## Seeding Behavior

### First Time (Empty Database)

```bash
# Container starts → No demo data found → Seeds default amounts:
# - 100 assets
# - 10 applications  
# - 20 deployments
# - 5 users
# - 100 events
```

### After Manual Seeding

```bash
# You seed large dataset:
python manage.py seed_demo_data --assets 50000 --applications 5000 ...

# Container restarts → Existing data detected → Skips seeding
# Your 50,000 assets and 5,000 applications are preserved!
```

### Incremental Seeding

```bash
# If you have 100 assets and want 50,000:
python manage.py seed_demo_data --assets 50000

# Result: Only creates 49,900 new assets (100 + 49,900 = 50,000)
# Existing 100 assets are preserved
```

---

## Preserving Your Data

### ✅ Safe Operations (Data Preserved)

1. **Container restart** - Data persists
2. **Running seed without `--clear-existing`** - Only adds missing records
3. **Database volume persists** - Data stored in Docker volume

### ⚠️ Destructive Operations (Data Lost)

1. **Using `--clear-existing` flag** - Clears all demo data first
2. **Removing database volume** - `docker-compose down -v`
3. **Running `clear_demo_data()`** - Explicitly clears all demo data

---

## Best Practices

### 1. Initial Seeding

For first-time setup, use the entrypoint (automatic) or seed manually:

```bash
# Automatic (on first container start)
docker-compose up -d

# Manual (for larger datasets)
docker-compose exec eucora-api python manage.py seed_demo_data \
  --assets 50000 \
  --applications 5000 \
  --deployments 10000 \
  --users 1000 \
  --events 100000 \
  --batch-size 1000
```

### 2. Adding More Data

To increase counts without clearing existing data:

```bash
# This will only add missing records up to the target
python manage.py seed_demo_data --assets 100000  # Adds 50,000 more if you have 50,000
```

### 3. Resetting Data

Only if you need to start fresh:

```bash
# Via management command
python manage.py seed_demo_data --clear-existing --assets 100 ...

# Via API
curl -X POST http://localhost:8000/api/v1/admin/seed-demo-data \
  -H "Content-Type: application/json" \
  -d '{"clear_existing": true, "assets": 100, ...}'

# Via admin UI
# Navigate to /admin/demo-data → Click "Clear Demo Data" → Then "Seed Demo Data"
```

---

## Database Volume Persistence

### Docker Compose

The database volume persists data:

```yaml
volumes:
  postgres_data:  # This volume persists across restarts
```

### Checking Volume

```bash
# List volumes
docker volume ls | grep eucora

# Inspect volume
docker volume inspect eucora_postgres_data
```

### Removing Data (Full Reset)

```bash
# Stop containers and remove volumes
docker-compose down -v

# Restart (will seed fresh data)
docker-compose up -d
```

---

## Troubleshooting

### Issue: Data Still Disappears After Restart

**Possible Causes:**

1. **Database volume not persisting**
   ```bash
   # Check if volume exists
   docker volume ls | grep postgres
   
   # If missing, recreate
   docker-compose down
   docker-compose up -d
   ```

2. **Using `--clear-existing` in custom scripts**
   - Check any custom seeding scripts
   - Remove `--clear-existing` unless explicitly needed

3. **Database container being recreated**
   ```bash
   # Check container status
   docker-compose ps
   
   # Ensure db container is running
   docker-compose up -d db
   ```

### Issue: Seeding Creates Duplicates

**Solution:** The seeding functions use `bulk_create(ignore_conflicts=True)`, which prevents duplicates. If you see duplicates, check for:
- Unique constraints on models
- Database-level constraints
- Race conditions (unlikely with single-threaded seeding)

---

## Verification

### Check Data Persistence

```bash
# Before restart
docker-compose exec eucora-api python manage.py shell -c "
from apps.core.demo_data import demo_data_stats
stats = demo_data_stats()
print(f'Assets: {stats[\"assets\"]:,}')
print(f'Applications: {stats[\"applications\"]:,}')
"

# Restart container
docker-compose restart eucora-api

# After restart (should show same counts)
docker-compose exec eucora-api python manage.py shell -c "
from apps.core.demo_data import demo_data_stats
stats = demo_data_stats()
print(f'Assets: {stats[\"assets\"]:,}')
print(f'Applications: {stats[\"applications\"]:,}')
"
```

---

## Summary

✅ **Demo data now persists across container restarts**  
✅ **Seeding is idempotent - only adds missing records**  
✅ **Entrypoint script preserves existing data**  
✅ **Database volume ensures persistence**  
⚠️ **Only use `--clear-existing` when you want to reset**

---

**Related Documentation:**
- [Demo Data Seeding Runbook](./demo-data-seeding.md)
- [Demo Data Troubleshooting](./demo-data-troubleshooting.md)
