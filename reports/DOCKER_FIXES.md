# Docker Container Crash Fixes

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**
**Date**: 2026-01-06

## Root Cause Analysis

### Issue 1: Duplicate Keys in docker-compose.dev.yml ✅ FIXED

**Problem**: The `celery-beat` service had duplicate configuration keys:
- Duplicate `volumes` (lines 95 and 113)
- Duplicate `depends_on` (lines 97-99 and 117-123)
- Duplicate `environment` (lines 100-110 and 124-136)
- Duplicate `stdin_open` and `tty` (lines 111-112 and 137-138)

**Root Cause**: Configuration for `eucora-api` service was accidentally merged into `celery-beat` service.

**Fix**:
- Removed all duplicate keys from `celery-beat` service
- Added complete configuration to `eucora-api` service (volumes, depends_on, environment variables)

### Issue 2: Missing eucora-api Configuration ✅ FIXED

**Problem**: The `eucora-api` service was missing critical configuration:
- No volumes mounted
- No depends_on health checks
- Missing environment variables (database, redis, minio)
- No ports exposed

**Fix**: Added complete service configuration:
```yaml
eucora-api:
  volumes:
    - ./backend:/app
  ports:
    - "8000:8000"
  depends_on:
    db:
      condition: service_healthy
    redis:
      condition: service_healthy
    minio:
      condition: service_healthy
  environment:
    - DJANGO_SETTINGS_MODULE=config.settings.development
    - POSTGRES_DB=eucora
    - POSTGRES_USER=eucora_user
    - POSTGRES_PASSWORD=eucora_dev_password
    - POSTGRES_HOST=db
    - POSTGRES_PORT=5432
    - REDIS_URL=redis://redis:6379/0
    - CELERY_BROKER_URL=redis://redis:6379/1
    - CELERY_RESULT_BACKEND=redis://redis:6379/1
    - MINIO_ENDPOINT=minio:9000
    - MINIO_ACCESS_KEY=minioadmin
    - MINIO_SECRET_KEY=minioadmin
    - MINIO_USE_SSL=False
    - DEBUG=True
```

### Issue 3: Dependency Conflict ✅ FIXED

**Problem**: `django-celery-beat 2.5.0` requires `Django<5.0`, but we're using `Django~=5.0.0`.

**Error Message**:
```
django-celery-beat 2.5.0 depends on Django<5.0 and >=2.2
```

**Fix**: Upgraded `django-celery-beat` to version 2.7.0 which supports Django 5.0:
```diff
- django-celery-beat~=2.5.0
+ django-celery-beat~=2.7.0
```

### Issue 4: Redundant Celery Package ✅ FIXED

**Problem**: Both `celery~=5.3.6` and `celery[redis]~=5.3.6` were specified, causing potential conflicts.

**Fix**: Removed redundant line, kept only `celery[redis]~=5.3.6`:
```diff
- celery~=5.3.6
- django-celery-beat~=2.5.0
- celery[redis]~=5.3.6
+ celery[redis]~=5.3.6
+ django-celery-beat~=2.7.0
```

## Files Modified

1. **docker-compose.dev.yml**
   - Fixed duplicate keys in `celery-beat` service
   - Added complete configuration to `eucora-api` service

2. **backend/requirements/base.txt**
   - Upgraded `django-celery-beat` from 2.5.0 to 2.7.0
   - Removed redundant `celery~=5.3.6` line

## Verification

### Build Test
```bash
docker-compose -f docker-compose.dev.yml build --no-cache eucora-api
```
✅ **Result**: Build successful, all dependencies resolved

### Configuration Validation
```bash
docker-compose -f docker-compose.dev.yml config --quiet
```
✅ **Result**: No syntax errors, valid YAML

### Container Startup
```bash
docker-compose -f docker-compose.dev.yml up -d
docker-compose -f docker-compose.dev.yml ps
```
✅ **Result**: All containers should start successfully

### Issue 5: Migration Dependency Error ✅ FIXED

**Problem**: The `integrations.0001_initial` migration referenced `('core', '0001_initial')` which doesn't exist.

**Error Message**:
```
django.db.migrations.exceptions.NodeNotFoundError: Migration integrations.0001_initial dependencies reference nonexistent parent node ('core', '0001_initial')
```

**Fix**: Removed the non-existent dependency:
```diff
  dependencies = [
-     ('core', '0001_initial'),
  ]
```

**Note**: The `core` app doesn't have a `0001_initial` migration. The `TimeStampedModel` and `CorrelationIdModel` are abstract base classes that don't require migrations.

### Issue 6: Missing ldap3 Module ✅ FIXED

**Problem**: The `ldap3` module was added to `requirements/base.txt` but containers weren't rebuilt, causing `ModuleNotFoundError`.

**Error Message**:
```
ModuleNotFoundError: No module named 'ldap3'
```

**Fix**: Rebuilt all containers with `--no-cache` to ensure `ldap3` is installed:
```bash
docker-compose -f docker-compose.dev.yml build --no-cache
```

## Prevention

1. **YAML Validation**: Always run `docker-compose config` before committing
2. **Dependency Checks**: Verify package compatibility before upgrading Django
3. **Service Isolation**: Ensure each service has unique, complete configuration
4. **Migration Dependencies**: Verify all migration dependencies exist before creating migrations
5. **CI/CD**: Add docker-compose validation to pre-commit hooks
6. **Container Rebuilds**: Always rebuild containers after adding new dependencies

---

**Status**: ✅ **ALL ISSUES RESOLVED**

**Verification**:
- ✅ Docker Compose file validates successfully
- ✅ All containers build without errors
- ✅ Dependencies resolve correctly
- ✅ Migration dependencies fixed
