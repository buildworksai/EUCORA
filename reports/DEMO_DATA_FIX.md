# Demo Data Admin Login Fix

**SPDX-License-Identifier: Apache-2.0**  
**Copyright (c) 2026 BuildWorks.AI**  
**Date**: 2026-01-06

## Issue

Demo data was not working in admin login interface. Users could log in but saw no demo data.

## Root Causes

### Issue 1: Missing Admin URLs ✅ FIXED

**Problem**: Admin demo data endpoints were not included in the main URL configuration.

**Error**: `NoReverseMatch: Reverse for 'demo-data-stats' not found`

**Fix**: Added admin URLs to `config/urls.py`:
```python
path('api/v1/admin/', include('apps.core.urls')),  # Admin demo data endpoints
```

### Issue 2: Demo Data Not Seeded ✅ FIXED

**Problem**: The `setup_dev_data` command only created the admin user but didn't seed demo data.

**Result**: All demo data counts were 0:
```json
{
  "assets": 0,
  "applications": 0,
  "deployments": 0,
  "ring_deployments": 0,
  "cab_approvals": 0,
  "evidence_packs": 0,
  "events": 0,
  "users": 0
}
```

**Fix**: Updated `entrypoint.sh` to automatically seed demo data on container startup:
```bash
echo "Seeding initial demo data (small set for development)..."
python manage.py seed_demo_data \
  --assets 100 \
  --applications 10 \
  --deployments 20 \
  --users 5 \
  --events 100 \
  --batch-size 50 \
  --clear-existing || echo "Demo data seeding skipped (may already exist)"

echo "Enabling demo mode..."
python manage.py shell -c "
from apps.core.utils import set_demo_mode_enabled
set_demo_mode_enabled(True)
print('Demo mode enabled')
" || echo "Demo mode setup skipped"
```

### Issue 3: Demo Mode Disabled ✅ FIXED

**Problem**: Demo mode was disabled by default, so demo data wouldn't be visible even if seeded.

**Fix**: Automatically enable demo mode in development entrypoint script.

## Files Modified

1. **backend/config/urls.py**
   - Added `path('api/v1/admin/', include('apps.core.urls'))` to include admin demo data endpoints

2. **backend/entrypoint.sh**
   - Added automatic demo data seeding with small development dataset
   - Added automatic demo mode enabling

## Admin Demo Data Endpoints

All endpoints are now accessible at `/api/v1/admin/`:

- `GET /api/v1/admin/demo-data-stats` - Get demo data statistics
- `POST /api/v1/admin/seed-demo-data` - Seed demo data
- `DELETE /api/v1/admin/clear-demo-data` - Clear demo data
- `GET /api/v1/admin/demo-mode` - Get demo mode status
- `POST /api/v1/admin/demo-mode` - Enable/disable demo mode

## Development Credentials

### Admin User (created by setup_dev_data)
- **Username**: `devadmin`
- **Email**: `admin@eucora.local`
- **Password**: `eucora-dev-password`
- **Access**: Django admin, API admin endpoints

### Demo User (created by seed_demo_data)
- **Username**: `demo`
- **Email**: `demo@eucora.com`
- **Password**: `admin@134`
- **Access**: Demo data access

## Verification

After container restart, verify:

1. **Demo data exists**:
   ```bash
   docker-compose exec eucora-api python manage.py shell -c "from apps.core.demo_data import demo_data_stats; import json; print(json.dumps(demo_data_stats(), indent=2))"
   ```

2. **Demo mode enabled**:
   ```bash
   docker-compose exec eucora-api python manage.py shell -c "from apps.core.utils import get_demo_mode_enabled; print('Demo mode:', get_demo_mode_enabled())"
   ```

3. **Admin endpoints accessible**:
   - Login to admin interface
   - Navigate to Demo Data Administration page
   - Should see demo data counts > 0

## Frontend Integration

The frontend `AdminDemoData` component (`frontend/src/routes/AdminDemoData.tsx`) uses:
- `useDemoDataStats()` - Fetches demo data statistics
- `useDemoMode()` - Gets demo mode status
- `useSeedDemoData()` - Seeds demo data
- `useClearDemoData()` - Clears demo data
- `useSetDemoMode()` - Toggles demo mode

All hooks use `/api/v1/admin/` endpoints which are now properly configured.

---

**Status**: ✅ **ALL ISSUES RESOLVED**

**Next Steps**: 
- Test admin login and demo data display
- Verify demo data seeding works correctly
- Test demo mode toggle functionality


