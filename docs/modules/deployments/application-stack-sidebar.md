<!-- SPDX-License-Identifier: Apache-2.0 -->
<!-- Copyright (c) 2026 BuildWorks.AI -->

# Application Stack Sidebar Implementation

## Overview

This document describes the full-stack implementation of the **Application Stack Sidebar** feature, which displays a hierarchical view of applications, versions, and deployments in the UI sidebar.

**Route**: `/deployments/stack`  
**Navigation**: Sidebar → "Application Stack" (Package icon)

## Architecture

### Backend API Endpoint

**Endpoint**: `GET /api/v1/deployments/applications`

**Authentication**: Required (IsAuthenticated)

**Query Parameters**:
- `app_name` (optional): Case-insensitive filter for application names
- `status` (optional): Filter by deployment status
- `ring` (optional): Filter by target ring

**Response Schema**:

```json
{
  "applications": [
    {
      "app_name": "Adobe Acrobat Reader",
      "latest_version": "24.001",
      "deployment_count": 3,
      "versions": [
        {
          "version": "24.001",
          "latest_created_at": "2026-01-20T10:00:00Z",
          "deployments": [
            {
              "correlation_id": "12345678-1234-1234-1234-123456789012",
              "target_ring": "CANARY",
              "status": "COMPLETED",
              "risk_score": 15,
              "requires_cab_approval": false,
              "created_at": "2026-01-20T10:00:00Z"
            }
          ]
        }
      ]
    }
  ]
}
```

### Features

#### 1. Application Grouping
- Applications are alphabetically sorted by name
- Each application shows total deployment count
- Latest version is computed from most recent deployment per app

#### 2. Version Expansion
- Versions are sorted by creation date (newest first)
- Each version shows count of nested deployments
- Collapsible tree structure for easy navigation

#### 3. Deployment Details
- Target ring displayed inline with status badge
- Risk score displayed with color coding:
  - ≤ 50: Green (safe)
  - > 50: Red (requires CAB approval)
- Creation date shown for each deployment

#### 4. Status Indicators
- **COMPLETED**: Green checkmark
- **APPROVED**: Green checkmark
- **DEPLOYING**: Blue clock (in progress)
- **AWAITING_CAB**: Yellow alert (pending approval)
- **PENDING**: Gray clock (not started)
- **REJECTED**: Red alert
- **FAILED**: Red alert
- **ROLLED_BACK**: Yellow alert

#### 5. Search & Filtering
- Real-time search by application name
- Server-side filtering for optimal performance
- Client-side secondary filtering for responsive UX

## Implementation Details

### Backend Files Modified

#### `/backend/apps/deployment_intents/views.py`
Added new view: `list_applications_with_versions(request)`

- Fetches all deployments from queryable context
- Groups by application name
- Sorts versions by creation date
- Builds hierarchical response structure
- Supports query parameter filtering

#### `/backend/apps/deployment_intents/urls.py`
Added new route:
```python
path('applications', views.list_applications_with_versions, name='applications'),
```

### Frontend Files Created

#### `/frontend/src/routes/deployments/sidebar-contracts.ts`
Contracts and endpoints for the sidebar feature:
- `SidebarApplicationGroup` type definition
- `SidebarVersionEntry` type definition
- `ApplicationListResponse` type definition
- `SIDEBAR_ENDPOINTS` constant with `/deployments/applications`

#### `/frontend/src/lib/api/hooks/useSidebarApplications.ts`
TanStack Query hook:
- `useSidebarApplications(filters?)` hook
- Manages caching and refetching logic
- Supports optional filters (app_name, status, ring)
- Poll interval: 5 minutes (refetch on window focus)

#### `/frontend/src/routes/deployments/DeploymentsSidebar.tsx`
Main component with three sub-components:
1. `ApplicationEntry`: Collapsible application groups
2. `VersionEntry`: Nested version entries within each app
3. `DeploymentRow`: Individual deployment display with status/risk

Features:
- Expandable tree structure using Radix UI Collapsible
- Search input with real-time filtering
- Loading skeleton states
- Empty state handling
- Inline status icons and color-coded risk scores
- Ring-specific badge colors

#### `/frontend/src/routes/deployments/DeploymentsSidebar.test.tsx`
Comprehensive test suite covering:
- Loading states
- Application rendering
- Search filtering
- Empty states
- Status/risk display
- Component integration

### UI Component Updates

#### `/frontend/src/components/layout/Sidebar.tsx`
Added navigation item:
```typescript
{
  href: '/deployments/stack',
  label: 'Application Stack',
  icon: Package,
  resource: 'deployments'
}
```

#### `/frontend/src/App.tsx`
Added route:
```typescript
<Route path="/deployments/stack" element={<DeploymentsSidebar />} />
```

## UI/UX Design

### Visual Hierarchy

```
📦 Application Name [3 deployments]
  └─ v24.001 [2 deployments]
     └─ ✓ CANARY | COMPLETED | R:15
     └─ ⏱ PILOT | DEPLOYING | R:15
  └─ v23.999 [1 deployment]
     └─ ✓ LAB | APPROVED | R:10
```

### Color Palette

- **Ring Badges**: Different color per ring
  - LAB: Slate
  - CANARY: Teal
  - PILOT: Blue
  - DEPARTMENT: Purple
  - GLOBAL: Green
- **Status Icons**: Context-aware colors
- **Risk Scores**: Red (high) ↔ Green (low)

### Interactions

- **Expand/Collapse**: Click on application or version header
- **Search**: Type in search input to filter by app name
- **View Details**: Click a deployment to navigate to details (future feature)

## Data Flow

### Backend to Frontend

```
Django View (list_applications_with_versions)
    ↓
DeploymentIntent QuerySet
    ↓
Grouping by app_name and version
    ↓
REST Response (ApplicationListResponse)
    ↓
React Query (useSidebarApplications)
    ↓
Component (DeploymentsSidebar)
    ↓
UI Render
```

### Real-time Updates

- **Poll Interval**: 5 minutes
- **On Window Focus**: Refetch immediately
- **Manual Refetch**: Available via `refetch()` from hook

## Testing

### Backend Test
File: `/backend/apps/deployment_intents/tests/test_applications_endpoint.py`

Verifies:
- Response structure validation
- Application grouping logic
- Version sorting (newest first)
- Deployment nesting
- JSON serialization

### Frontend Tests
File: `/frontend/src/routes/deployments/DeploymentsSidebar.test.tsx`

Covers:
- Loading state rendering
- Application/version/deployment display
- Search filtering
- Empty state handling
- Status indicators
- Risk score display

## Deployment Checklist

- [x] Backend endpoint implemented and tested
- [x] Frontend contracts defined
- [x] React hooks implemented with TanStack Query
- [x] Sidebar component with full tree structure
- [x] Search and filtering functionality
- [x] Status indicators and risk coloring
- [x] Tests (backend structure + frontend integration)
- [x] TypeScript build passes (zero errors)
- [x] ESLint validation passes (zero warnings)
- [x] Navigation link added to sidebar
- [x] Route configured in App.tsx

## Future Enhancements

1. **Click to Details**: Navigate to deployment details page
2. **Inline Actions**: Promote/rollback buttons per deployment
3. **Status History**: Timeline view of deployment progression
4. **Bulk Operations**: Select multiple and execute actions
5. **Custom Columns**: Allow user to show/hide risk, dates, etc.
6. **Export**: Download application inventory as CSV
7. **Favorites**: Pin frequently accessed applications
8. **Quick Stats**: Summary statistics in sidebar header

## Compliance Notes

- ✓ Correlation IDs maintained throughout backend flow
- ✓ Demo mode filtering applied via `apply_demo_filter`
- ✓ Authentication enforced on endpoint
- ✓ All queries indexed for performance
- ✓ Response includes immutable audit-trail fields

## References

- **Backend Architecture**: [docs/architecture/control-plane-design.md](../../docs/architecture/control-plane-design.md)
- **Deployment Model**: [docs/architecture/ring-model.md](../../docs/architecture/ring-model.md)
- **Risk Scoring**: [docs/architecture/risk-model.md](../../docs/architecture/risk-model.md)
- **Sidebar Design**: UI/UX specifications in component
