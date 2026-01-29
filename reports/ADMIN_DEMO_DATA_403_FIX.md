# Admin Demo Data 403 Error Fix - COMPLETE

## Issue
User reported 403 Forbidden errors when accessing admin demo data endpoints (`/api/v1/admin/demo-mode` and `/api/v1/admin/demo-data-stats`) even when logged in as admin.

## Root Cause Analysis

1. **Backend Configuration**: The views use `AllowAny` permission in development mode (`DEBUG=True`), which should allow unauthenticated requests.

2. **CSRF Protection**: DRF's `SessionAuthentication` enforces CSRF protection for state-changing operations (POST/PUT/DELETE) even with `AllowAny` permission. This was blocking requests from the frontend when using mock authentication (no valid session cookie).

3. **Frontend Issue**: The frontend is using mock authentication (`VITE_USE_MOCK_AUTH === 'true'`), which means:
   - The frontend thinks the user is logged in
   - But there's no actual Django session cookie
   - API requests may not include proper CSRF tokens

## Changes Made

### Backend Changes

1. **Updated Views** (`backend/apps/core/views_demo.py`):
   - Added `@exempt_csrf` decorator for all demo data views in development mode
   - Added error handling to views to provide better error messages
   - Added CSRF token endpoint (`/api/v1/admin/csrf-token`) for frontend to fetch tokens
   - Confirmed `AllowAny` permission is used in development mode

2. **CSRF Exemption Logic**:
   ```python
   # In development, exempt CSRF for these API views to allow mock auth
   if settings.DEBUG:
       def exempt_csrf(view_func):
           return csrf_exempt(view_func)
   else:
       def exempt_csrf(view_func):
           return view_func  # No exemption in production
   ```

3. **New Endpoint**:
   - `GET /api/v1/admin/csrf-token` - Returns CSRF token for frontend use

### Frontend Changes

1. **Updated API Client** (`frontend/src/lib/api/client.ts`):
   - Made `getCsrfToken()` async to fetch CSRF token from API if not in cookies
   - Added caching for CSRF tokens
   - Updated `apiRequest()` to await CSRF token before making requests

2. **CSRF Token Fetching**:
   - First tries to get token from cookies (normal Django session flow)
   - Falls back to fetching from `/api/v1/admin/csrf-token` endpoint
   - Caches token to avoid repeated API calls

## Resolution

✅ **Fixed**: All endpoints now work correctly in development mode, even with mock authentication.

### Key Fixes:
1. **CSRF Exemption in Development**: Views are exempt from CSRF checks in development mode, allowing unauthenticated requests
2. **CSRF Token Endpoint**: Frontend can fetch CSRF tokens when needed
3. **Improved Error Handling**: Better error messages for debugging

### Security Note:
- CSRF exemption is **only active in development mode** (`DEBUG=True`)
- In production, CSRF protection is enforced and `IsAdminUser` permission is required
- This ensures security in production while allowing easy development with mock auth

## Testing

All endpoints tested and working:

```bash
# Test GET endpoints
curl http://localhost:8000/api/v1/admin/demo-mode
# Response: {"demo_mode_enabled":true}

curl http://localhost:8000/api/v1/admin/demo-data-stats
# Response: {"counts": {...}, "demo_mode_enabled":true}

# Test POST endpoint (no CSRF token needed in development)
curl -X POST http://localhost:8000/api/v1/admin/demo-mode \
  -H "Content-Type: application/json" \
  -d '{"enabled": true}'
# Response: {"demo_mode_enabled":true}

# Test CSRF token endpoint
curl http://localhost:8000/api/v1/admin/csrf-token
# Response: {"csrf_token":"..."}
```

## Status

✅ **COMPLETE** - All issues resolved

- ✅ Backend views updated with CSRF exemption in development
- ✅ Permission configuration verified (`AllowAny` in development, `IsAdminUser` in production)
- ✅ CORS configuration verified (`CORS_ALLOW_ALL_ORIGINS = True`)
- ✅ Frontend API client updated to handle CSRF tokens
- ✅ CSRF token endpoint added
- ✅ All endpoints tested and working
- ✅ Security maintained (CSRF exemption only in development)
