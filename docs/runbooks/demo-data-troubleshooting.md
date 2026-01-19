# Demo Data Troubleshooting Guide

**SPDX-License-Identifier: Apache-2.0**  
**Version**: 1.0.0  
**Last Updated**: January 8, 2026

---

## Common Issues

### Issue 1: Demos Not Loading / Zero Counts

**Symptoms:**
- Admin demo data page shows all zeros
- No demo data visible in dashboards
- API returns empty results

**Diagnosis:**
1. Check if demo data exists:
   ```bash
   ./scripts/utilities/check-demo-data.sh
   ```

2. Check demo mode status:
   ```bash
   # In Docker
   docker-compose exec eucora-api python manage.py shell -c "from apps.core.utils import get_demo_mode_enabled; print(get_demo_mode_enabled())"
   
   # Local
   python3 backend/manage.py shell -c "from apps.core.utils import get_demo_mode_enabled; print(get_demo_mode_enabled())"
   ```

**Solutions:**

1. **Seed Demo Data:**
   ```bash
   # Using script (recommended)
   ./scripts/utilities/seed-demo-data.sh
   
   # Using Docker
   docker-compose exec eucora-api python manage.py seed_demo_data \
     --assets 100 \
     --applications 10 \
     --deployments 20 \
     --users 5 \
     --events 100 \
     --batch-size 50 \
     --clear-existing
   
   # Using management command directly
   python3 backend/manage.py seed_demo_data \
     --assets 100 \
     --applications 10 \
     --deployments 20 \
     --users 5 \
     --events 100 \
     --batch-size 50 \
     --clear-existing
   ```

2. **Enable Demo Mode:**
   ```bash
   # In Docker
   docker-compose exec eucora-api python manage.py shell -c "from apps.core.utils import set_demo_mode_enabled; set_demo_mode_enabled(True)"
   
   # Local
   python3 backend/manage.py shell -c "from apps.core.utils import set_demo_mode_enabled; set_demo_mode_enabled(True)"
   ```

3. **Via Admin UI:**
   - Navigate to `/admin/demo-data`
   - Toggle "Demo Mode" switch to ON
   - Click "Seed Demo Data" button

### Issue 2: API Endpoints Not Responding

**Symptoms:**
- 404 errors on `/api/v1/admin/demo-data-stats`
- Network errors in browser console
- Frontend shows loading state indefinitely

**Diagnosis:**
1. Check if URLs are configured:
   ```bash
   grep -r "api/v1/admin" backend/config/urls.py
   ```

2. Check if backend is running:
   ```bash
   curl http://localhost:8000/api/v1/admin/demo-data-stats
   ```

**Solutions:**

1. **Verify URL Configuration:**
   Ensure `backend/config/urls.py` includes:
   ```python
   path('api/v1/admin/', include('apps.core.urls')),
   ```

2. **Check Backend Logs:**
   ```bash
   # Docker
   docker-compose logs eucora-api | tail -50
   
   # Local
   # Check Django server output
   ```

3. **Restart Backend:**
   ```bash
   docker-compose restart eucora-api
   ```

### Issue 3: Demo Mode Disabled

**Symptoms:**
- Demo data exists but not visible
- API returns empty results even with demo data
- `demo_mode_enabled` is `false`

**Solutions:**

1. **Enable via Management Command:**
   ```bash
   python3 backend/manage.py shell -c "from apps.core.utils import set_demo_mode_enabled; set_demo_mode_enabled(True); print('Demo mode enabled')"
   ```

2. **Enable via Admin UI:**
   - Navigate to `/admin/demo-data`
   - Toggle "Demo Mode" switch to ON

3. **Check Database:**
   ```bash
   python3 backend/manage.py shell -c "from apps.core.models import DemoModeConfig; config = DemoModeConfig.objects.first(); print(f'Demo mode: {config.is_enabled if config else \"Not configured\"}')"
   ```

### Issue 4: Frontend Not Showing Data

**Symptoms:**
- Backend has demo data
- Demo mode is enabled
- Frontend still shows zeros

**Diagnosis:**
1. Check browser console for errors
2. Check network tab for API responses
3. Verify API response structure matches frontend expectations

**Solutions:**

1. **Clear Browser Cache:**
   - Hard refresh: `Ctrl+Shift+R` (Windows/Linux) or `Cmd+Shift+R` (Mac)
   - Clear cache and reload

2. **Check API Response:**
   ```bash
   curl http://localhost:8000/api/v1/admin/demo-data-stats
   ```
   
   Should return:
   ```json
   {
     "counts": {
       "assets": 100,
       "applications": 10,
       ...
     },
     "demo_mode_enabled": true
   }
   ```

3. **Verify Frontend API Client:**
   - Check `frontend/src/lib/api/client.ts` configuration
   - Verify `VITE_API_URL` environment variable
   - Check CORS settings if accessing from different origin

---

## Quick Fix Commands

### Full Reset and Seed
```bash
# Clear existing demo data and seed fresh
./scripts/utilities/seed-demo-data.sh

# Or with Docker
docker-compose exec eucora-api python manage.py seed_demo_data \
  --assets 100 \
  --applications 10 \
  --deployments 20 \
  --users 5 \
  --events 100 \
  --batch-size 50 \
  --clear-existing

# Enable demo mode
docker-compose exec eucora-api python manage.py shell -c "from apps.core.utils import set_demo_mode_enabled; set_demo_mode_enabled(True)"
```

### Check Status
```bash
./scripts/utilities/check-demo-data.sh
```

### Enable Demo Mode Only
```bash
# Docker
docker-compose exec eucora-api python manage.py shell -c "from apps.core.utils import set_demo_mode_enabled; set_demo_mode_enabled(True)"

# Local
python3 backend/manage.py shell -c "from apps.core.utils import set_demo_mode_enabled; set_demo_mode_enabled(True)"
```

---

## Verification Steps

After fixing issues, verify:

1. **Backend Status:**
   ```bash
   curl http://localhost:8000/api/v1/admin/demo-data-stats
   ```

2. **Frontend Access:**
   - Navigate to `http://localhost:5173/admin/demo-data`
   - Verify counts are non-zero
   - Verify "Demo Mode" toggle is ON

3. **Dashboard Visibility:**
   - Check `/dashboard` for demo data
   - Check `/assets` for demo assets
   - Check `/cab` for demo CAB approvals

---

## Environment Variables

Ensure these are set correctly:

**Backend:**
- `DEBUG=True` (for development)
- `POSTGRES_DB=eucora`
- `POSTGRES_USER=eucora_user`
- `POSTGRES_PASSWORD=eucora_dev_password`

**Frontend:**
- `VITE_API_URL=http://localhost:8000/api/v1`
- `VITE_USE_MOCK_AUTH=true` (for development)

---

## Additional Resources

- [Demo Data Seeding Runbook](./demo-data-seeding.md)
- [Development Setup](../DEVELOPMENT_SETUP.md)
- [Admin Demo Data API Documentation](../../backend/apps/core/views_demo.py)
