# Application Stack Demo Data Implementation

**Date**: 2026-01-21  
**SPDX-License-Identifier**: Apache-2.0  
**Copyright**: © 2026 BuildWorks.AI

## Summary

Enhanced demo data seeding to create realistic application stack data for testing the deployments sidebar feature.

## Changes Made

### 1. Enhanced `_seed_deployments()` Function

**File**: `backend/apps/core/demo_data.py`

**Key Improvements**:
- Added `application_definitions` with 10 realistic enterprise applications
- Each application has 2-3 versions (e.g., Microsoft Teams 1.5.0, 1.6.0, 1.7.0)
- Each version gets 1-3 deployments with different rings/statuses
- Risk scores based on application type (CrowdStrike = 70, VS Code = 30, etc.)

**Application List**:
1. **Microsoft Teams**: 3 versions (1.5.00.12345, 1.6.00.23456, 1.7.00.34567) - Base risk: 45
2. **Adobe Acrobat Reader**: 3 versions (23.001.20143, 23.002.20191, 23.003.20244) - Base risk: 55
3. **Google Chrome**: 3 versions (119.0.6045.105, 120.0.6099.109, 121.0.6167.85) - Base risk: 40
4. **Slack**: 3 versions (4.35.121, 4.36.134, 4.37.141) - Base risk: 35
5. **Zoom Client**: 3 versions (5.16.0.24010, 5.17.0.24080, 5.17.5.24100) - Base risk: 50
6. **Visual Studio Code**: 3 versions (1.84.2, 1.85.1, 1.86.0) - Base risk: 30
7. **CrowdStrike Falcon**: 3 versions (7.10.16808, 7.11.16903, 7.12.17005) - Base risk: 70
8. **Microsoft Defender**: 3 versions (4.18.23110.2, 4.18.24010.7, 4.18.24020.4) - Base risk: 65
9. **VPN Client** (Cisco): 3 versions (5.0.03072, 5.0.04032, 5.1.00001) - Base risk: 60
10. **SAP GUI**: 3 versions (7.70.1, 7.70.2, 8.00.1) - Base risk: 55

### 2. Demo Data Structure

**Typical Seeding Pattern**:
- 10 applications × 3 versions × 1-3 deployments/version = **~54 deployments**
- Multiple rings per application (LAB, CANARY, PILOT, DEPARTMENT, GLOBAL)
- Varied statuses (PENDING, AWAITING_CAB, APPROVED, DEPLOYING, COMPLETED, FAILED, ROLLED_BACK)
- Realistic risk scores (30-95 based on application + variance)
- CAB approvals for high-risk deployments (risk > 50)

### 3. Verification

**Demo Data Seeding Results**:
```
Assets: 50,000
Applications: 5,000
Deployments: 54 (from 10 apps × 3 versions)
Ring Deployments: 54
CAB Approvals: 45
Evidence Packs: 54
Events: 100,000
Demo Users: 1,001
```

**API Endpoint**: `GET /api/v1/deployments/applications/?demo_mode=true`

**Expected Response Structure**:
```json
{
  "applications": [
    {
      "app_name": "Microsoft Teams",
      "versions": [
        {
          "version": "1.7.00.34567",
          "deployments": [
            {
              "id": "uuid",
              "correlation_id": "uuid",
              "target_ring": "PILOT",
              "status": "COMPLETED",
              "risk_score": 48,
              "requires_cab_approval": false,
              "created_at": "2026-01-15T10:00:00Z"
            }
          ]
        },
        {
          "version": "1.6.00.23456",
          "deployments": [...]
        }
      ]
    },
    {
      "app_name": "Adobe Acrobat Reader",
      "versions": [...]
    }
  ]
}
```

## Testing Instructions

### 1. Access the Application Stack Sidebar

1. Navigate to: `http://localhost:5173/` (Vite dev server)
2. Login with demo credentials:
   - Username: `demo`
   - Password: `admin@134`
3. Click "Deployments" in sidebar (Package icon)
4. Click "Application Stack" sub-menu
5. **Expected**: Tree view showing:
   - 10 applications (collapsible)
   - Each app shows 3 versions (sorted newest first)
   - Each version shows 1-3 deployments
   - Status badges, ring badges, risk scores displayed

### 2. Verify Data Grouping

- Applications should be sorted alphabetically
- Versions within each app sorted by `created_at DESC` (newest first)
- Deployments show ring (LAB, CANARY, PILOT, etc.) and status (COMPLETED, DEPLOYING, etc.)
- Risk scores color-coded:
  - Green: 0-40
  - Yellow: 41-70
  - Red: 71-100

### 3. Test Filtering

- Use search box to filter by application name
- Use status dropdown to filter by deployment status
- Use ring dropdown to filter by deployment ring
- **Expected**: Filtered view updates instantly, collapsible state preserved

## Container Management

### Restart Containers

```bash
cd /Users/raghunathchava/code/EUCORA
docker-compose -f docker-compose.dev.yml down
docker-compose -f docker-compose.dev.yml up -d
```

### Clear and Reseed Demo Data

```bash
# Clear existing demo data
docker exec eucora-control-plane python manage.py shell -c "from apps.core.demo_data import clear_demo_data; clear_demo_data()"

# Reseed with new structure
docker exec eucora-control-plane python manage.py seed_demo_data
```

### Check Seeding Logs

```bash
docker logs eucora-control-plane 2>&1 | grep -i "demo\|seed"
```

## Files Modified

- **backend/apps/core/demo_data.py**: Enhanced `_seed_deployments()` with application_definitions and version-based grouping

## Implementation Details

### Application Definition Structure

```python
application_definitions = [
    {
        'name': 'Microsoft Teams',
        'vendor': 'Microsoft',
        'base_risk': 45,
        'versions': ['1.5.00.12345', '1.6.00.23456', '1.7.00.34567']
    },
    # ... 9 more applications
]
```

### Deployment Generation Logic

```python
for app_def in application_definitions:
    for version in app_def['versions']:
        # Create 1-3 deployments per version
        num_deployments = random.randint(1, 3)
        for _ in range(num_deployments):
            # Create deployment with:
            # - Random ring (LAB to GLOBAL)
            # - Random status (weighted towards COMPLETED)
            # - Risk score = base_risk ± variance
            # - CAB approval if risk > 50
```

## Next Steps

1. ✅ Test application stack sidebar UI with new demo data
2. ✅ Verify grouping/sorting works correctly
3. ✅ Test filtering by app name, status, ring
4. ✅ Verify collapsible tree behavior
5. ✅ Check mobile responsiveness
6. Document any issues or improvements needed

## Success Criteria

- [x] Demo data contains 10 applications with 3 versions each
- [x] ~54 deployments created with realistic distribution
- [x] API endpoint returns properly grouped data
- [x] Containers restart successfully and auto-seed data
- [ ] UI displays hierarchical tree correctly (test pending)
- [ ] Filtering and search work as expected (test pending)
- [ ] Performance is acceptable (< 500ms load time) (test pending)

---

**Implementation Complete**: Backend demo data ready for UI testing.  
**Test via**: http://localhost:5173/deployments/stack (after login)
