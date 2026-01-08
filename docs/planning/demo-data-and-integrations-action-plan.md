# Demo Data & External Integrations — Action Plan

**SPDX-License-Identifier: Apache-2.0**  
**Version**: 1.0  
**Status**: Planning  
**Author**: Platform Engineering  
**Date**: 2026-01-06

---

## Executive Summary

This document defines the implementation plan for:
1. **Demo Data Seeding**: Admin-controlled seeding of realistic enterprise scenarios for demonstrations and testing
2. **External System Integrations**: Real-time connectivity with ITSM, CMDB, Identity, and MDM systems for production use

**Architecture Principle**: The application operates in two modes:
- **Demo Mode**: Seeded data in local database for trials/demos/testing
- **Production Mode**: Live integration with enterprise systems for real operations

---

## 1. Required External Integrations

### 1.1 Identity & Directory Services

#### Microsoft Entra ID (Azure AD)
**Purpose**: Primary identity provider, user/device sync, conditional access  
**Integration Points**:
- OAuth2/OpenID Connect for SSO
- Microsoft Graph API for:
  - User directory sync (`/users`, `/groups`)
  - Device compliance state (`/deviceManagement/managedDevices`)
  - Conditional access policies
  - Group membership for RBAC

**Data Sync**:
- Users → `User` model (email, displayName, department, jobTitle)
- Groups → `EntraIDGroup` model for RBAC mapping
- Devices → `Asset` model enrichment (compliance, enrollment status)

**API Requirements**:
- `User.Read.All`, `Directory.Read.All`, `Device.Read.All`
- Certificate-based authentication for service principal
- Sync frequency: Every 1 hour (configurable)

#### Active Directory (On-Premises)
**Purpose**: Legacy directory for air-gapped/hybrid sites  
**Integration Points**:
- LDAP/LDAPS for user/group queries
- PowerShell/WinRM for computer object queries
- AD Connect for hybrid scenarios

**Data Sync**:
- Computer objects → `Asset` model (hostname, OU, lastLogon)
- User objects → `User` model (samAccountName, distinguishedName)
- Security groups → RBAC group mapping

**API Requirements**:
- Service account with constrained delegation
- LDAP read permissions
- Sync frequency: Every 4 hours (configurable)

---

### 1.2 CMDB (Configuration Management Database)

#### ServiceNow CMDB
**Purpose**: Authoritative source for asset inventory, relationships, config items  
**Integration Points**:
- Table API for CI queries (`/api/now/table/cmdb_ci_computer`)
- Import Sets API for bulk sync
- Relationship API for asset dependencies

**Data Sync**:
- CIs → `Asset` model (serial_number, asset_tag, location, owner)
- Relationships → Asset dependency graph
- Change requests → CAB workflow correlation

**API Requirements**:
- REST API with OAuth2 or Basic Auth
- Read access to `cmdb_ci_*` tables
- Sync frequency: Every 30 minutes (configurable)

#### Jira Assets (formerly Insight)
**Purpose**: Asset management for Jira-centric orgs  
**Integration Points**:
- Assets REST API v2 for object queries
- Object schema API for asset types
- Custom fields for metadata

**Data Sync**:
- Objects → `Asset` model
- Custom attributes → Asset custom fields
- Sync frequency: Every 1 hour

#### Freshservice CMDB
**Purpose**: Alternative CMDB for mid-market  
**Integration Points**:
- Assets API (`/api/v2/assets`)
- Asset types API
- Relationships API

---

### 1.3 ITSM (IT Service Management)

#### ServiceNow ITSM
**Purpose**: Change management, incident tracking, approval workflows  
**Integration Points**:
- Change Request API (`/api/now/table/change_request`)
- Incident API for impact tracking
- Approval API for CAB workflow integration

**Data Sync**:
- Change requests → CAB workflow (CRQ correlation)
- Incidents → Deployment failure tracking
- Approvals → CAB approval records

**API Requirements**:
- Create/update change requests
- Query approval status
- Webhook for approval notifications
- Sync frequency: Real-time (webhook) + polling every 5 minutes

#### Jira Service Management
**Purpose**: ITSM for Atlassian shops  
**Integration Points**:
- Issue API for change requests
- Approval API
- Webhooks for status updates

**Data Sync**:
- Jira issues (type=Change) → CAB workflow
- Approvals → CAB approval records
- Comments → Audit trail

#### Freshservice ITSM
**Purpose**: Lightweight ITSM  
**Integration Points**:
- Change API (`/api/v2/changes`)
- Approval API
- Webhooks

---

### 1.4 Mobile Device Management (MDM)

#### Apple Business Manager (ABM)
**Purpose**: Device enrollment, app distribution for Apple devices  
**Integration Points**:
- ABM API for device assignments
- VPP (Volume Purchase Program) API for app licensing
- Automated Device Enrollment (ADE) integration via Intune/Jamf

**Data Sync**:
- Enrolled devices → `Asset` model (iOS/iPadOS/macOS)
- App assignments → Deployment intents
- License counts → Application inventory

**API Requirements**:
- ABM API credentials (server token)
- VPP organization ID
- Sync frequency: Every 6 hours

#### Android Enterprise / Zero-Touch
**Purpose**: Android device enrollment and management  
**Integration Points**:
- Google Play EMM API
- Zero-Touch API for device provisioning
- Managed Google Play for app distribution

**Data Sync**:
- Enrolled devices → `Asset` model (Android)
- App approvals → Application catalog
- Sync frequency: Every 6 hours

---

### 1.5 Endpoint Management Platforms (Execution Planes)

#### Microsoft Intune
**Purpose**: Primary execution plane for Windows/macOS/iOS/Android  
**Integration Points**:
- Microsoft Graph API (`/deviceManagement/*`)
- Device compliance queries
- App install status queries
- Group membership for targeting

**Data Sync**:
- Managed devices → `Asset` model (compliance, lastSync, os)
- App install status → Deployment telemetry
- Sync frequency: Every 15 minutes

#### Jamf Pro
**Purpose**: macOS-specific management  
**Integration Points**:
- Jamf Pro API (Classic + Universal)
- Computer inventory API
- Policy execution logs
- Smart group membership

**Data Sync**:
- Computers → `Asset` model (macOS)
- Policy results → Deployment telemetry
- Sync frequency: Every 15 minutes

#### SCCM (Microsoft Endpoint Configuration Manager)
**Purpose**: Legacy Windows management for air-gapped sites  
**Integration Points**:
- AdminService REST API
- WMI/PowerShell queries
- Collection membership
- Deployment status queries

**Data Sync**:
- Computer resources → `Asset` model
- Deployment status → Deployment telemetry
- Sync frequency: Every 30 minutes

#### Ubuntu Landscape
**Purpose**: Linux fleet management  
**Integration Points**:
- Landscape API for computer queries
- Package profile status
- Activity results

**Data Sync**:
- Computers → `Asset` model (Linux)
- Package status → Deployment telemetry
- Sync frequency: Every 1 hour

---

### 1.6 Monitoring & Observability

#### Datadog
**Purpose**: Application performance monitoring, metrics, logs  
**Integration Points**:
- Metrics API for custom metrics
- Events API for deployment events
- Logs API for centralized logging

**Data Sync**:
- Deployment metrics → Datadog dashboards
- Failure events → Datadog incidents
- Real-time (push)

#### Splunk
**Purpose**: SIEM, log aggregation, security analytics  
**Integration Points**:
- HTTP Event Collector (HEC) for logs
- REST API for search queries
- Alert webhooks

**Data Sync**:
- Audit events → Splunk index
- Security events → SIEM correlation
- Real-time (push)

#### Elastic (ELK Stack)
**Purpose**: Alternative log aggregation  
**Integration Points**:
- Elasticsearch API for log ingestion
- Kibana dashboards for visualization

---

### 1.7 Vulnerability & Security Scanning

#### Trivy / Grype / Snyk
**Purpose**: Container/package vulnerability scanning  
**Integration Points**:
- CLI integration in packaging pipelines
- API for scan result queries
- SBOM generation

**Data Sync**:
- Scan results → Evidence store
- CVE data → Risk scoring
- Per-build (synchronous)

#### Microsoft Defender for Endpoint
**Purpose**: Threat detection, vulnerability assessment  
**Integration Points**:
- Microsoft Graph Security API
- Threat Intelligence API
- Vulnerability data for assets

**Data Sync**:
- Device vulnerabilities → Asset risk scores
- Threat detections → Incident correlation
- Sync frequency: Every 1 hour

---

## 2. Demo Data Seeding Architecture

### 2.1 Design Principles

**Realism**: Demo data must reflect real enterprise scenarios:
- 50,000+ assets across multiple locations
- Mix of Windows 11/10, macOS, Ubuntu, iOS, Android
- Compliance scores (70-100)
- Deployment history with success/failure patterns
- Realistic user assignments and ownership

**Controllability**: Admin can:
- Seed full dataset or incremental batches
- Clear demo data without affecting real data
- Toggle demo mode on/off
- Customize scenario parameters (asset count, failure rate, etc.)

**Isolation**: Demo data uses same models but:
- Flagged with `is_demo=True` field
- Can be filtered/excluded from production queries
- Can be bulk-deleted via admin action

### 2.2 Demo Data Entities

#### Assets (50,000 records)
- **Types**: Laptop (60%), Desktop (20%), Virtual Machine (10%), Mobile (8%), Server (2%)
- **OS Distribution**:
  - Windows 11 (40%), Windows 10 (30%)
  - macOS Sonoma (12%), macOS Ventura (8%)
  - Ubuntu 22.04 (5%), iOS 17 (3%), Android 14 (2%)
- **Locations**: 20 global sites (HQ, Regional, Branch offices)
- **Compliance Scores**: Normal distribution (mean=90, std=10)
- **Status**: Active (95%), Inactive (3%), Maintenance (2%)
- **DEX Metrics**: bootTime, carbonFootprint, userSentiment

#### Applications (5,000 records)
- **Standard Apps**: Microsoft 365, Adobe Acrobat, Chrome, Slack, Zoom
- **Line-of-Business**: Custom internal tools
- **Versions**: Multiple versions per app (current + 2 prior)
- **Deployment Status**: Deployed (80%), Pending (15%), Failed (5%)
- **Ring Distribution**: Lab (50), Canary (500), Pilot (5000), Department (25000), Global (All)

#### Deployments (10,000 records)
- **Status Distribution**: Completed (70%), In Progress (20%), Failed (8%), Rolled Back (2%)
- **Risk Scores**: Distribution across 0-100 (weighted toward low-risk)
- **CAB Approvals**: High-risk deployments have approval records
- **Telemetry**: Success rates per ring, time-to-compliance

#### CAB Approvals (500 records)
- **Statuses**: Approved (80%), Pending (15%), Denied (5%)
- **Risk Scores**: >50 for all
- **Evidence Packs**: Complete evidence pack metadata
- **Approvers**: Rotated across demo CAB members

#### Audit Events (100,000 records)
- **Types**: Deployment, Approval, Policy Change, User Action
- **Correlation IDs**: Linked to deployment intents
- **Actors**: Demo users with realistic names
- **Time Distribution**: Last 90 days with realistic hourly patterns

#### Users (1,000 records)
- **Roles**: Admin (50), Operator (200), Viewer (500), Demo (250)
- **Departments**: IT Ops, Security, Development, HR, Finance
- **Permissions**: Mapped to roles
- **Activity**: Last login timestamps

### 2.3 Seeding Implementation

#### Backend: Django Management Command

**Location**: `backend/apps/core/management/commands/seed_demo_data.py`

**CLI Interface**:
```bash
python manage.py seed_demo_data \
  --assets 50000 \
  --apps 5000 \
  --deployments 10000 \
  --users 1000 \
  --clear-existing \
  --batch-size 1000
```

**Features**:
- Bulk creation with `bulk_create()` for performance
- Progress bar with `tqdm`
- Idempotent (can be re-run safely)
- Realistic faker data (names, emails, locations)
- Relationship integrity (FKs, M2M)

**Example Schema**:
```python
Asset.objects.bulk_create([
    Asset(
        name=fake.hostname(),
        asset_id=f"DEMO-{uuid4().hex[:8]}",
        type=random.choice(['Laptop', 'Desktop', 'Mobile']),
        os=random.choice(['Windows 11', 'macOS Sonoma', 'iOS 17']),
        location=fake.city(),
        status='Active',
        compliance_score=random.randint(70, 100),
        is_demo=True,  # Demo flag
        owner=fake.name(),
        serial_number=fake.ean13(),
        ip_address=fake.ipv4(),
        dex_score=random.uniform(7.0, 10.0),
        boot_time=random.randint(15, 60),
        carbon_footprint=random.uniform(50, 200),
    )
    for _ in range(batch_size)
], batch_size=1000)
```

#### Frontend: Admin Seeding Page

**Location**: New route `/admin/demo-data`

**UI Features**:
- Seed full dataset button
- Incremental seeding controls (add 1000 assets, etc.)
- Clear demo data button (with confirmation)
- Progress indicator during seeding
- Summary statistics (current demo record counts)
- Toggle demo mode (filters UI queries to show/hide demo data)

**API Endpoint**:
```
POST /api/v1/admin/seed-demo-data
  Body: { 
    "assets": 50000, 
    "apps": 5000, 
    "clear_existing": true 
  }
  Response: { 
    "status": "success", 
    "counts": { "assets": 50000, "apps": 5000 } 
  }
```

---

## 3. Settings Integration Pages Architecture

### 3.1 File Organization (500 Line Limit)

**Current Issue**: `Settings.tsx` is monolithic (~1000 lines)

**Refactored Structure**:
```
frontend/src/routes/settings/
├── index.tsx                      # Main Settings container (< 200 lines)
├── ProfileTab.tsx                 # Profile & notifications (< 300 lines)
├── AIProvidersTab.tsx             # AI provider configs (< 400 lines)
├── UsersTab.tsx                   # User management (< 400 lines)
├── IntegrationsTab.tsx            # Main integrations container (< 200 lines)
├── integrations/
│   ├── EntraIDIntegration.tsx     # Entra ID config (< 400 lines)
│   ├── ADIntegration.tsx          # Active Directory (< 400 lines)
│   ├── CMDBIntegration.tsx        # CMDB systems (< 450 lines)
│   ├── ITSMIntegration.tsx        # Ticketing systems (< 450 lines)
│   ├── MDMIntegration.tsx         # ABM, Android Enterprise (< 400 lines)
│   ├── MonitoringIntegration.tsx  # Datadog, Splunk, etc. (< 400 lines)
│   └── types.ts                   # Shared integration types
```

### 3.2 Integration Page Design Pattern

Each integration page follows consistent structure:

```tsx
// Example: CMDBIntegration.tsx
export default function CMDBIntegration() {
  const [config, setConfig] = useState<CMDBConfig>(defaultConfig);
  const [testStatus, setTestStatus] = useState<TestResult | null>(null);

  const handleTestConnection = async () => {
    // Test API connectivity
    const result = await api.post('/integrations/cmdb/test', config);
    setTestStatus(result);
  };

  const handleSave = async () => {
    // Save configuration
    await api.post('/integrations/cmdb/save', config);
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>CMDB Integration</CardTitle>
        <CardDescription>
          Sync asset inventory from your CMDB system
        </CardDescription>
      </CardHeader>
      
      <CardContent>
        {/* System Type Selector */}
        <SystemTypeSelector 
          value={config.type}
          onChange={(type) => setConfig({ ...config, type })}
          options={['servicenow', 'jira', 'freshservice', 'custom']}
        />

        {/* Dynamic Form Based on Type */}
        {config.type === 'servicenow' && <ServiceNowForm config={config} onChange={setConfig} />}
        {config.type === 'jira' && <JiraForm config={config} onChange={setConfig} />}
        
        {/* Sync Settings */}
        <SyncSettingsForm config={config} onChange={setConfig} />
        
        {/* Test Connection */}
        <TestConnectionButton onClick={handleTestConnection} status={testStatus} />
      </CardContent>

      <CardFooter>
        <Button onClick={handleSave}>
          <Save className="mr-2 h-4 w-4" />
          Save Configuration
        </Button>
      </CardFooter>
    </Card>
  );
}
```

### 3.3 Backend Integration Models

**Location**: `backend/apps/integrations/`

**Models**:
```python
# backend/apps/integrations/models.py
class ExternalSystem(TimeStampedModel):
    """Base model for external system integrations."""
    
    class SystemType(models.TextChoices):
        ENTRA_ID = 'entra_id', 'Microsoft Entra ID'
        ACTIVE_DIRECTORY = 'active_directory', 'Active Directory'
        SERVICENOW = 'servicenow', 'ServiceNow'
        JIRA = 'jira', 'Jira'
        FRESHSERVICE = 'freshservice', 'Freshservice'
        INTUNE = 'intune', 'Microsoft Intune'
        JAMF = 'jamf', 'Jamf Pro'
        ABM = 'abm', 'Apple Business Manager'
        ANDROID_ENTERPRISE = 'android_enterprise', 'Android Enterprise'
        DATADOG = 'datadog', 'Datadog'
        SPLUNK = 'splunk', 'Splunk'
    
    name = models.CharField(max_length=255)
    type = models.CharField(max_length=50, choices=SystemType.choices)
    is_enabled = models.BooleanField(default=False)
    api_url = models.URLField()
    auth_type = models.CharField(max_length=50)  # oauth2, basic, cert, token
    credentials = models.JSONField(default=dict)  # Encrypted vault reference
    sync_interval_minutes = models.IntegerField(default=60)
    last_sync_at = models.DateTimeField(null=True, blank=True)
    last_sync_status = models.CharField(max_length=50, null=True, blank=True)
    metadata = models.JSONField(default=dict)  # System-specific config

class IntegrationSyncLog(TimeStampedModel):
    """Audit log for integration sync operations."""
    
    system = models.ForeignKey(ExternalSystem, on_delete=models.CASCADE)
    sync_started_at = models.DateTimeField()
    sync_completed_at = models.DateTimeField(null=True, blank=True)
    status = models.CharField(max_length=50)  # success, failed, partial
    records_fetched = models.IntegerField(default=0)
    records_created = models.IntegerField(default=0)
    records_updated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    correlation_id = models.UUIDField(default=uuid4)
```

**API Endpoints**:
```python
# backend/apps/integrations/views.py
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_integrations(request):
    """List all configured integrations."""
    systems = ExternalSystem.objects.all()
    return Response(ExternalSystemSerializer(systems, many=True).data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_integration(request):
    """Save or update integration configuration."""
    # Validate, encrypt credentials, store in vault
    pass

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_integration(request, system_id):
    """Test connectivity to external system."""
    # Attempt API call with provided credentials
    pass

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def trigger_sync(request, system_id):
    """Manually trigger sync for an integration."""
    # Enqueue Celery task for sync
    pass

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def sync_logs(request, system_id):
    """Retrieve sync history for an integration."""
    logs = IntegrationSyncLog.objects.filter(system_id=system_id).order_by('-created_at')
    return Response(IntegrationSyncLogSerializer(logs, many=True).data)
```

### 3.4 Celery Tasks for Background Sync

**Location**: `backend/apps/integrations/tasks.py`

**Tasks**:
```python
from celery import shared_task
from .services import get_integration_service

@shared_task(bind=True, max_retries=3)
def sync_external_system(self, system_id):
    """Background task to sync data from external system."""
    system = ExternalSystem.objects.get(id=system_id)
    service = get_integration_service(system.type)
    
    log = IntegrationSyncLog.objects.create(
        system=system,
        sync_started_at=timezone.now(),
        status='running'
    )
    
    try:
        result = service.sync(system)
        log.sync_completed_at = timezone.now()
        log.status = 'success'
        log.records_fetched = result['fetched']
        log.records_created = result['created']
        log.records_updated = result['updated']
        log.save()
        
        system.last_sync_at = timezone.now()
        system.last_sync_status = 'success'
        system.save()
    except Exception as e:
        log.status = 'failed'
        log.error_message = str(e)
        log.save()
        
        system.last_sync_status = 'failed'
        system.save()
        
        self.retry(exc=e, countdown=60 * (2 ** self.request.retries))
```

**Periodic Scheduling** (Celery Beat):
```python
# backend/config/celery.py
from celery.schedules import crontab

app.conf.beat_schedule = {
    'sync-all-integrations': {
        'task': 'apps.integrations.tasks.sync_all_integrations',
        'schedule': crontab(minute='*/15'),  # Every 15 minutes
    },
}
```

---

## 4. Integration Service Layer

### 4.1 Service Interface Pattern

**Location**: `backend/apps/integrations/services/`

**Base Interface**:
```python
# backend/apps/integrations/services/base.py
from abc import ABC, abstractmethod

class IntegrationService(ABC):
    """Base class for all external system integrations."""
    
    @abstractmethod
    def test_connection(self, config: dict) -> dict:
        """Test API connectivity and credentials."""
        pass
    
    @abstractmethod
    def sync(self, system: ExternalSystem) -> dict:
        """Perform full sync from external system."""
        pass
    
    @abstractmethod
    def fetch_assets(self, system: ExternalSystem) -> list:
        """Fetch asset inventory."""
        pass
    
    def _authenticate(self, system: ExternalSystem):
        """Handle authentication (OAuth2, Basic, Cert)."""
        pass
    
    def _handle_rate_limit(self, response):
        """Handle rate limiting with exponential backoff."""
        pass
```

**Example Implementation**:
```python
# backend/apps/integrations/services/servicenow.py
class ServiceNowService(IntegrationService):
    """ServiceNow CMDB integration."""
    
    def test_connection(self, config: dict) -> dict:
        """Test ServiceNow API connectivity."""
        url = f"{config['api_url']}/api/now/table/cmdb_ci_computer"
        headers = self._get_auth_headers(config)
        
        try:
            response = requests.get(url, headers=headers, params={'sysparm_limit': 1})
            response.raise_for_status()
            return {'status': 'success', 'message': 'Connection successful'}
        except requests.exceptions.RequestException as e:
            return {'status': 'failed', 'message': str(e)}
    
    def sync(self, system: ExternalSystem) -> dict:
        """Sync assets from ServiceNow CMDB."""
        assets = self.fetch_assets(system)
        created, updated = 0, 0
        
        for asset_data in assets:
            asset, created_flag = Asset.objects.update_or_create(
                asset_id=asset_data['sys_id'],
                defaults={
                    'name': asset_data['name'],
                    'serial_number': asset_data['serial_number'],
                    'location': asset_data['location'],
                    'owner': asset_data['assigned_to'],
                    'status': self._map_status(asset_data['install_status']),
                    'type': self._map_type(asset_data['category']),
                    'os': asset_data['os'],
                    'is_demo': False,
                }
            )
            if created_flag:
                created += 1
            else:
                updated += 1
        
        return {
            'fetched': len(assets),
            'created': created,
            'updated': updated
        }
    
    def fetch_assets(self, system: ExternalSystem) -> list:
        """Fetch computer CIs from ServiceNow."""
        url = f"{system.api_url}/api/now/table/cmdb_ci_computer"
        headers = self._get_auth_headers(system)
        params = {
            'sysparm_query': 'install_status=1',  # Active
            'sysparm_limit': 10000,
            'sysparm_offset': 0
        }
        
        assets = []
        while True:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            data = response.json()
            assets.extend(data['result'])
            
            if len(data['result']) < params['sysparm_limit']:
                break
            
            params['sysparm_offset'] += params['sysparm_limit']
        
        return assets
    
    def _get_auth_headers(self, system):
        """Generate auth headers (Basic Auth or OAuth2)."""
        # Retrieve credentials from vault
        credentials = vault.get_secret(system.credentials['vault_path'])
        return {
            'Authorization': f"Basic {credentials['basic_auth_token']}",
            'Content-Type': 'application/json'
        }
    
    def _map_status(self, install_status):
        """Map ServiceNow install status to Asset status."""
        mapping = {
            '1': 'Active',
            '2': 'Inactive',
            '3': 'Retired',
            '6': 'Maintenance'
        }
        return mapping.get(str(install_status), 'Active')
    
    def _map_type(self, category):
        """Map ServiceNow category to Asset type."""
        # Implementation specific to ServiceNow categories
        pass
```

### 4.2 Service Factory

```python
# backend/apps/integrations/services/__init__.py
from .servicenow import ServiceNowService
from .jira import JiraService
from .entra_id import EntraIDService
from .abm import AppleBusinessManagerService
# ... other services

SERVICE_REGISTRY = {
    'servicenow': ServiceNowService,
    'jira': JiraService,
    'entra_id': EntraIDService,
    'abm': AppleBusinessManagerService,
    # ... other mappings
}

def get_integration_service(system_type: str) -> IntegrationService:
    """Factory method to get integration service by type."""
    service_class = SERVICE_REGISTRY.get(system_type)
    if not service_class:
        raise ValueError(f"No service registered for system type: {system_type}")
    return service_class()
```

---

## 5. Implementation Phases

### Phase 1: Demo Data Foundation (Week 1)
**Goal**: Enable demo data seeding without external integrations

**Tasks**:
1. Create `seed_demo_data.py` management command
   - Asset generation (50K)
   - Application generation (5K)
   - Deployment generation (10K)
   - User generation (1K)
   - CAB approval generation (500)
   - Audit event generation (100K)
2. Add `is_demo` field to all relevant models (migration)
3. Update model managers/querysets to filter demo data
4. Create admin UI page `/admin/demo-data`
   - Seed controls
   - Clear demo data
   - Statistics display
5. Create API endpoints:
   - `POST /api/v1/admin/seed-demo-data`
   - `DELETE /api/v1/admin/clear-demo-data`
   - `GET /api/v1/admin/demo-data-stats`

**Deliverables**:
- Working demo data seeding
- Admin can toggle demo mode
- UI displays realistic enterprise data

---

### Phase 2: Settings Refactoring (Week 2)
**Goal**: Modularize Settings into sub-500-line files

**Tasks**:
1. Create `frontend/src/routes/settings/` directory structure
2. Extract ProfileTab component
3. Extract AIProvidersTab component
4. Extract UsersTab component
5. Create IntegrationsTab container
6. Extract integration sub-components:
   - EntraIDIntegration
   - CMDBIntegration
   - ITSMIntegration
   - MDMIntegration
   - MonitoringIntegration
7. Update routing and navigation
8. Ensure each file < 500 lines

**Deliverables**:
- Refactored Settings page
- All files under 500 lines
- No functionality regression

---

### Phase 3: Integration Backend Infrastructure (Week 3)
**Goal**: Build integration framework and models

**Tasks**:
1. Create `backend/apps/integrations/` Django app
2. Create models:
   - `ExternalSystem`
   - `IntegrationSyncLog`
3. Create base `IntegrationService` interface
4. Implement service factory pattern
5. Create Celery tasks for background sync
6. Configure Celery Beat for periodic sync
7. Create API endpoints:
   - `GET /api/v1/integrations/`
   - `POST /api/v1/integrations/`
   - `PUT /api/v1/integrations/<id>/`
   - `DELETE /api/v1/integrations/<id>/`
   - `POST /api/v1/integrations/<id>/test`
   - `POST /api/v1/integrations/<id>/sync`
   - `GET /api/v1/integrations/<id>/logs`
8. Add vault integration for credential storage

**Deliverables**:
- Integration framework ready
- Background sync tasks operational
- API endpoints functional

---

### Phase 4: CMDB Integrations (Week 4)
**Goal**: Implement ServiceNow, Jira Assets, Freshservice CMDB sync

**Tasks**:
1. Implement `ServiceNowService`
   - Test connection
   - Fetch assets (cmdb_ci_computer table)
   - Map fields to Asset model
   - Handle pagination
2. Implement `JiraService` (Jira Assets)
   - Assets API v2 integration
   - Object schema mapping
   - Custom field handling
3. Implement `FreshserviceService`
   - Assets API integration
   - Asset type mapping
4. Create frontend integration forms
5. Add field mapping configuration UI
6. Test end-to-end sync

**Deliverables**:
- 3 CMDB integrations functional
- Asset sync working
- UI configuration complete

---

### Phase 5: ITSM Integrations (Week 5)
**Goal**: Implement ServiceNow, Jira, Freshservice ITSM for CAB workflow

**Tasks**:
1. Implement ServiceNow Change Request integration
   - Create CR from deployment intent
   - Query approval status
   - Webhook for status updates
2. Implement Jira Service Management
   - Create Jira issue (type=Change)
   - Approval API integration
   - Webhook handling
3. Implement Freshservice Changes
   - Change API integration
   - Approval workflow
4. Link CAB workflow to external CRs
   - Store external CR ID in CAB approval model
   - Bi-directional status sync
5. Create UI for ITSM configuration

**Deliverables**:
- CAB workflow integrated with ITSM
- Change requests auto-created
- Approval status synced

---

### Phase 6: Identity Integrations (Week 6)
**Goal**: Implement Entra ID and AD sync for users/groups/devices

**Tasks**:
1. Implement `EntraIDService`
   - Microsoft Graph API OAuth2 flow
   - User directory sync (`/users`)
   - Group sync for RBAC (`/groups`)
   - Device sync (`/deviceManagement/managedDevices`)
   - Conditional access policy queries
2. Implement `ActiveDirectoryService`
   - LDAP/LDAPS integration
   - User/group queries
   - Computer object sync
3. Map Entra ID groups to RBAC roles
4. Sync device compliance state to Asset model
5. Create UI for identity provider configuration
6. Handle SSO integration (OAuth2/OIDC)

**Deliverables**:
- User/group sync from Entra ID
- AD sync for hybrid environments
- Device compliance enrichment

---

### Phase 7: MDM Integrations (Week 7)
**Goal**: Implement Apple Business Manager and Android Enterprise

**Tasks**:
1. Implement `AppleBusinessManagerService`
   - ABM API integration (server token auth)
   - Device assignment queries
   - VPP app licensing sync
   - ADE enrollment status
2. Implement `AndroidEnterpriseService`
   - Google Play EMM API
   - Zero-Touch enrollment
   - Managed Google Play app sync
3. Sync enrolled devices to Asset model
4. Link app distribution to deployment intents
5. Create UI for MDM configuration

**Deliverables**:
- Mobile device sync from ABM/Android Enterprise
- App licensing visibility
- Enrollment automation

---

### Phase 8: Monitoring Integrations (Week 8)
**Goal**: Implement Datadog, Splunk, Elastic for telemetry

**Tasks**:
1. Implement `DatadogService`
   - Metrics API for custom metrics
   - Events API for deployment events
   - Dashboard creation
2. Implement `SplunkService`
   - HTTP Event Collector for logs
   - Alert webhook handling
3. Implement `ElasticService`
   - Elasticsearch API for log ingestion
   - Index management
4. Push deployment metrics to monitoring systems
5. Create UI for monitoring configuration
6. Add monitoring dashboards links to UI

**Deliverables**:
- Deployment telemetry in Datadog/Splunk
- Centralized logging
- Real-time alerting

---

### Phase 9: Security & Vulnerability Integrations (Week 9)
**Goal**: Integrate vulnerability scanners and Defender for Endpoint

**Tasks**:
1. Implement Trivy/Grype/Snyk in packaging pipelines
   - CLI integration for SBOM generation
   - Scan result parsing
   - Policy enforcement (block Critical/High)
2. Implement `DefenderForEndpointService`
   - Microsoft Graph Security API
   - Device vulnerability queries
   - Threat intelligence
3. Enrich Asset risk scores with vulnerability data
4. Create UI for scanner configuration
5. Display vulnerability reports in evidence packs

**Deliverables**:
- Automated vulnerability scanning
- Risk scores enriched with CVE data
- Defender integration for threat visibility

---

### Phase 10: Testing & Documentation (Week 10)
**Goal**: Comprehensive testing and documentation

**Tasks**:
1. Write integration tests for all services
2. Load testing for sync performance
3. Security review of credential handling
4. Create integration runbooks:
   - ServiceNow setup guide
   - Jira setup guide
   - Entra ID app registration guide
   - ABM configuration guide
5. Update API documentation (OpenAPI)
6. Create video tutorials for integration setup
7. User acceptance testing with demo data

**Deliverables**:
- Test coverage ≥ 90%
- Integration documentation complete
- UAT passed

---

## 6. Security & Compliance Considerations

### 6.1 Credential Management

**Vault Integration**:
- All API keys, tokens, certificates stored in HashiCorp Vault or Azure Key Vault
- Credentials never stored in database directly
- Database stores vault path reference only
- Automatic credential rotation where supported

**Encryption**:
- Transit encryption for all API calls (TLS 1.2+)
- At-rest encryption for configuration data
- Certificate-based auth preferred over secrets

### 6.2 Access Control

**Service Principals**:
- Dedicated service principal per integration
- Scoped permissions (least privilege)
- No shared credentials across integrations

**RBAC**:
- Admin role required for integration configuration
- Viewer role can see integration status
- Operator role can trigger manual sync
- Audit all integration configuration changes

### 6.3 Rate Limiting & Throttling

**API Quotas**:
- Respect vendor API rate limits
- Implement exponential backoff
- Cache frequently accessed data
- Batch API calls where possible

**Sync Throttling**:
- Configurable sync intervals per integration
- Avoid sync storms (stagger sync schedules)
- Circuit breaker for repeated failures

### 6.4 Data Privacy

**PII Handling**:
- Minimal PII stored (only what's necessary)
- GDPR/CCPA compliance for user data
- Data retention policies (30/90/365 days)
- Right to deletion support

**Audit Trail**:
- All sync operations logged
- Correlation IDs for troubleshooting
- SIEM integration for security events
- Immutable audit logs

---

## 7. Monitoring & Observability

### 7.1 Integration Health Metrics

**Metrics to Track**:
- Sync success/failure rate
- Sync duration (p50, p95, p99)
- Records fetched/created/updated per sync
- API error rates by integration
- Credential expiry dates
- Last successful sync timestamp

**Dashboards**:
- Integration health overview
- Per-integration detail view
- Sync history timeline
- Error rate trends

### 7.2 Alerting

**Alert Conditions**:
- Sync failure (3 consecutive failures)
- API rate limit exceeded
- Credential expiry (7 days warning)
- Data sync lag > 2x expected interval
- Authentication failures

**Alert Channels**:
- Email to admin team
- Slack/Teams webhook
- PagerDuty for critical failures
- In-app notification banner

---

## 8. Performance Optimization

### 8.1 Sync Performance

**Strategies**:
- Incremental sync (delta queries where supported)
- Parallel processing for independent integrations
- Batch database operations (`bulk_create`, `bulk_update`)
- Connection pooling for API clients
- Caching for rarely-changed data (asset types, locations)

**Expected Performance**:
- 50K asset sync: < 10 minutes
- 5K app sync: < 5 minutes
- User sync: < 2 minutes
- Real-time webhook processing: < 1 second

### 8.2 Database Optimization

**Indexes**:
- `asset_id` (unique index)
- `serial_number` (index for lookups)
- `is_demo` (filtered index for production queries)
- `external_system_id` (foreign key index)
- `last_sync_at` (index for sorting)

**Query Optimization**:
- Use `select_related` for foreign keys
- Use `prefetch_related` for M2M
- Paginate large result sets
- Database query monitoring (Django Debug Toolbar)

---

## 9. Migration Strategy for Existing Customers

### 9.1 Migration Phases

**Phase 1: Parallel Run**
- Run both demo mode and production integrations
- Validate data consistency
- Monitor sync performance

**Phase 2: Cutover**
- Disable demo mode
- Enable production integrations
- Clear demo data
- Validate full sync

**Phase 3: Optimization**
- Tune sync intervals
- Adjust rate limits
- Optimize queries based on load

### 9.2 Rollback Plan

**Rollback Triggers**:
- Data corruption detected
- Sync performance unacceptable
- Integration stability issues

**Rollback Procedure**:
1. Disable production integrations
2. Re-enable demo mode
3. Restore demo data from backup
4. Investigate and fix root cause
5. Re-attempt migration

---

## 10. Success Metrics

### 10.1 Demo Data Metrics

- **Seeding Performance**: 50K assets in < 5 minutes
- **Data Realism**: User acceptance score > 8/10
- **UI Responsiveness**: Dashboard load < 2 seconds with demo data

### 10.2 Integration Metrics

- **Integration Coverage**: 100% of planned systems
- **Sync Reliability**: > 99% success rate
- **Sync Performance**: Within expected SLAs
- **Credential Security**: Zero credential exposures
- **User Adoption**: > 80% of customers configure at least 2 integrations

---

## 11. Risk Assessment

| Risk | Impact | Likelihood | Mitigation |
|---|---|---|---|
| API rate limit exceeded | High | Medium | Implement exponential backoff, caching |
| Credential compromise | Critical | Low | Vault storage, rotation, audit logging |
| Data sync corruption | High | Low | Validation, rollback, incremental sync |
| Vendor API changes | Medium | Medium | Versioned API clients, integration tests |
| Performance degradation | Medium | Medium | Load testing, query optimization, caching |
| PII compliance violation | Critical | Low | Minimal PII storage, GDPR compliance review |

---

## 12. Next Steps

1. **Review and Approval**: CAB review of this action plan
2. **Team Allocation**: Assign engineers to phases
3. **Sprint Planning**: Break phases into 2-week sprints
4. **Kickoff**: Begin Phase 1 (Demo Data Foundation)
5. **Weekly Sync**: Review progress, adjust timeline
6. **Quarterly Review**: Assess integration adoption, optimize

---

**Document Version**: 1.0  
**Last Updated**: 2026-01-06  
**Next Review**: 2026-02-06  
**Owner**: Platform Engineering Team
