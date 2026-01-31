# E20: Planning Agent

**SPDX-License-Identifier: Apache-2.0**

**Priority**: P2-High
**Sprint**: 19-20 (Weeks 37-40)
**Dependencies**: E3 (RBAC), E7 (pgvector), E8 (AI Workflows), E14 (Discovery)
**ALM L2 Category**: Change Management

---

## Overview

The Planning Agent ingests semi-structured inputs for deployments. Leveraging device and user inventory along with reasoning LLMs and MCP tools, it formulates an optimal rollout strategy. This approach minimizes user disruption and reduces rollback risks.

### Key Benefits

- Reduces manual overhead in scheduling/planning post-change updates
- Optimal rollout strategy formulation
- Minimizes user disruption
- Reduces rollback risks
- AI-assisted ring population

### Data Sources

- Intune
- SCCM
- SharePoint
- MCP Servers
- Device inventory
- User profiles

---

## Requirements

### 1. Deployment Planning

**Inputs**:
- Application to deploy
- Target scope (all, department, region)
- Deployment window preferences
- Risk tolerance
- Dependencies

**Outputs**:
- Optimal ring assignment
- Deployment schedule
- Risk assessment
- Rollback plan

### 2. Ring Population Strategy

**Factors**:
- Device health scores
- User criticality (VIP, standard)
- Previous deployment success
- Hardware compatibility
- Network segment
- Time zone considerations

**Ring Types**:
- Ring 0: Lab/Automation
- Ring 1: IT Canary
- Ring 2: Early Adopters
- Ring 3: Department
- Ring 4: Global

### 3. Risk Minimization

**Analysis**:
- Blast radius calculation
- Dependency impact
- User productivity impact
- Rollback complexity
- Historical success rates

**Recommendations**:
- Optimal ring sizes
- Deployment timing
- Pause points
- Rollback triggers

### 4. Schedule Optimization

**Considerations**:
- Business hours vs off-hours
- Maintenance windows
- Holiday calendars
- Change freeze periods
- Resource availability

---

## Data Model

### Django Models

```python
# apps/planning_agent/models.py

class DeploymentPlan(TimeStampedModel, CorrelationIdModel):
    """AI-generated deployment plan."""
    name = models.CharField(max_length=255)
    application = models.ForeignKey('application_portfolio.Application', on_delete=models.CASCADE)
    version = models.CharField(max_length=100)
    target_scope = models.JSONField()  # departments, regions, groups
    status = models.CharField(max_length=20)  # draft, pending_approval, approved, executing, completed

    # AI Generation
    input_request = models.TextField()
    reasoning = models.TextField()

    # Risk Assessment
    overall_risk_score = models.FloatField()
    risk_factors = models.JSONField()

    # Approval
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='created_plans')
    approved_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='approved_plans')
    approved_at = models.DateTimeField(null=True)

class RingAssignment(TimeStampedModel):
    """Device assignment to deployment ring."""
    plan = models.ForeignKey(DeploymentPlan, on_delete=models.CASCADE)
    ring_number = models.IntegerField()
    ring_name = models.CharField(max_length=50)
    device_count = models.IntegerField()
    device_criteria = models.JSONField()  # how devices were selected
    scheduled_start = models.DateTimeField()
    scheduled_end = models.DateTimeField()
    success_threshold = models.FloatField()  # required % for promotion
    status = models.CharField(max_length=20)

class RingDevice(TimeStampedModel):
    """Device in a ring."""
    ring = models.ForeignKey(RingAssignment, on_delete=models.CASCADE)
    device_id = models.CharField(max_length=255)
    device_name = models.CharField(max_length=255)
    user_principal = models.CharField(max_length=255, null=True)
    selection_reason = models.CharField(max_length=255)
    health_score = models.FloatField(null=True)
    criticality = models.CharField(max_length=20)  # vip, standard, low

class DeploymentWindow(TimeStampedModel):
    """Allowed deployment windows."""
    name = models.CharField(max_length=255)
    description = models.TextField()
    day_of_week = models.JSONField()  # [0,1,2,3,4] for Mon-Fri
    start_time = models.TimeField()
    end_time = models.TimeField()
    timezone = models.CharField(max_length=50)
    is_active = models.BooleanField(default=True)

class ChangeFreezeperiod(TimeStampedModel):
    """Change freeze periods."""
    name = models.CharField(max_length=255)
    reason = models.TextField()
    start_date = models.DateField()
    end_date = models.DateField()
    scope = models.JSONField()  # affected departments, regions
    is_active = models.BooleanField(default=True)

class BlastRadiusAnalysis(TimeStampedModel, CorrelationIdModel):
    """Blast radius analysis for a deployment."""
    plan = models.ForeignKey(DeploymentPlan, on_delete=models.CASCADE)
    total_users_affected = models.IntegerField()
    vip_users_affected = models.IntegerField()
    departments_affected = models.JSONField()
    regions_affected = models.JSONField()
    critical_systems_affected = models.JSONField()
    productivity_impact_score = models.FloatField()
    recommendations = models.JSONField()

class RollbackPlan(TimeStampedModel):
    """Rollback plan for deployment."""
    deployment_plan = models.ForeignKey(DeploymentPlan, on_delete=models.CASCADE)
    trigger_conditions = models.JSONField()
    rollback_steps = models.JSONField()
    estimated_duration_minutes = models.IntegerField()
    requires_cab_approval = models.BooleanField()
    tested = models.BooleanField(default=False)
    tested_at = models.DateTimeField(null=True)
```

---

## Agent Workflow Definition

```json
{
  "name": "deployment_planning_workflow",
  "agent_type": "planning",
  "risk_level": "R2",
  "steps": [
    {
      "name": "parse_request",
      "description": "Parse deployment request and requirements",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "gather_inventory",
      "description": "Gather device and user inventory from sources",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "analyze_compatibility",
      "description": "Analyze hardware/software compatibility",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "calculate_blast_radius",
      "description": "Calculate blast radius and impact",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "generate_ring_strategy",
      "description": "Generate optimal ring assignment strategy",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "optimize_schedule",
      "description": "Optimize deployment schedule",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "generate_rollback_plan",
      "description": "Generate rollback plan",
      "risk_level": "R1",
      "requires_approval": false
    },
    {
      "name": "present_plan",
      "description": "Present deployment plan for review",
      "risk_level": "R2",
      "requires_approval": true,
      "approval_context": "Review and approve deployment plan"
    },
    {
      "name": "create_deployment",
      "description": "Create deployment intent from approved plan",
      "risk_level": "R2",
      "requires_approval": true
    }
  ],
  "policy_requirements": [
    "deployment_policy",
    "change_management_policy",
    "risk_policy"
  ]
}
```

---

## Ring Strategy Algorithm

```python
class RingStrategyGenerator:
    """Generates optimal ring assignment strategy."""

    def generate_strategy(
        self,
        application: Application,
        target_scope: dict,
        risk_tolerance: str
    ) -> DeploymentPlan:
        """Generate deployment strategy."""

        # 1. Gather all devices in scope
        devices = self.gather_devices(target_scope)

        # 2. Score each device
        scored_devices = []
        for device in devices:
            score = self.calculate_device_score(device)
            scored_devices.append((device, score))

        # 3. Sort by suitability for early rings
        scored_devices.sort(key=lambda x: x[1], reverse=True)

        # 4. Assign to rings based on risk tolerance
        ring_sizes = self.calculate_ring_sizes(
            total_devices=len(devices),
            risk_tolerance=risk_tolerance
        )

        rings = []
        idx = 0
        for ring_num, (ring_name, size_pct) in enumerate(ring_sizes.items()):
            ring_size = int(len(devices) * size_pct / 100)
            ring_devices = scored_devices[idx:idx + ring_size]
            idx += ring_size

            rings.append(RingAssignment(
                ring_number=ring_num,
                ring_name=ring_name,
                devices=ring_devices
            ))

        return rings

    def calculate_device_score(self, device: dict) -> float:
        """Score device suitability for early ring."""
        score = 0.0

        # Health score (higher = better for early ring)
        score += device.get('health_score', 0.5) * 30

        # IT staff device bonus
        if device.get('is_it_staff'):
            score += 20

        # Non-VIP bonus (safer for early rings)
        if device.get('criticality') != 'vip':
            score += 15

        # Previous success history
        score += device.get('deployment_success_rate', 0.8) * 20

        # Compatible hardware
        if device.get('meets_requirements'):
            score += 15

        return score

    def calculate_ring_sizes(
        self,
        total_devices: int,
        risk_tolerance: str
    ) -> dict:
        """Calculate ring sizes based on risk tolerance."""

        if risk_tolerance == 'conservative':
            return {
                'Ring 0 - Lab': 1,
                'Ring 1 - IT Canary': 2,
                'Ring 2 - Early Adopters': 5,
                'Ring 3 - Department': 20,
                'Ring 4 - Global': 72
            }
        elif risk_tolerance == 'moderate':
            return {
                'Ring 0 - Lab': 1,
                'Ring 1 - IT Canary': 5,
                'Ring 2 - Early Adopters': 10,
                'Ring 3 - Department': 30,
                'Ring 4 - Global': 54
            }
        else:  # aggressive
            return {
                'Ring 0 - Lab': 1,
                'Ring 1 - IT Canary': 10,
                'Ring 2 - Early Adopters': 20,
                'Ring 3 - Global': 69
            }
```

---

## API Endpoints

```
# Deployment Plans
GET/POST /api/planning/plans/
GET /api/planning/plans/{id}/
POST /api/planning/plans/{id}/approve/
POST /api/planning/plans/{id}/execute/

# Natural Language
POST /api/planning/generate/

# Ring Assignments
GET /api/planning/plans/{id}/rings/
GET /api/planning/plans/{id}/rings/{ring_id}/devices/

# Blast Radius
GET /api/planning/plans/{id}/blast-radius/

# Rollback Plans
GET /api/planning/plans/{id}/rollback/

# Windows and Freezes
GET/POST /api/planning/deployment-windows/
GET/POST /api/planning/change-freezes/

# Optimization
POST /api/planning/optimize-schedule/
```

---

## Frontend Components

### 1. Planning Dashboard

```
AI Agents > Planning
├── Create Plan
│   ├── Natural language input
│   ├── Application selector
│   ├── Scope configuration
│   └── Risk tolerance
├── Active Plans
│   ├── Plan cards with status
│   ├── Ring progress
│   └── Quick actions
├── Schedule Calendar
│   ├── Deployment windows
│   ├── Change freezes
│   └── Upcoming deployments
└── Analytics
    ├── Success rates by ring
    ├── Risk distribution
    └── Historical performance
```

### 2. Plan Detail View

```
Deployment Plan: Office 365 Update
├── Summary
│   ├── Application: Office 365
│   ├── Version: 16.0.14326
│   ├── Total devices: 10,000
│   └── Risk score: 42/100
├── Ring Strategy
│   ├── Ring 0: 100 devices (Lab)
│   ├── Ring 1: 200 devices (IT)
│   ├── Ring 2: 500 devices (Early Adopters)
│   ├── Ring 3: 2,000 devices (Department)
│   └── Ring 4: 7,200 devices (Global)
├── Schedule
│   ├── Ring timeline (Gantt)
│   ├── Deployment windows
│   └── Pause points
├── Blast Radius
│   ├── Users affected: 8,500
│   ├── VIP users: 150
│   ├── Departments: 12
│   └── Impact visualization
├── Rollback Plan
│   ├── Trigger conditions
│   ├── Steps
│   └── Test status
└── Actions
    ├── Approve plan
    ├── Modify rings
    ├── Execute
    └── Export
```

---

## Acceptance Criteria

- [ ] Natural language plan generation
- [ ] Device/user inventory integration
- [ ] Ring strategy algorithm
- [ ] Blast radius calculation
- [ ] Schedule optimization
- [ ] Change freeze awareness
- [ ] Rollback plan generation
- [ ] Approval workflow
- [ ] Deployment intent creation
- [ ] ≥90% test coverage
