# E5: Application Policy UI — Deployment Policy Configuration

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Version**: 1.0
**Date**: 2026-01-30
**Status**: Draft for Implementation
**Priority**: P1-Critical
**Dependencies**: E3 (Comprehensive RBAC)

---

## Overview

Provide a comprehensive UI for packagers and application managers to configure deployment policies such as:
- Disable uninstall
- Enforce configuration
- Block manual installation
- Require restart
- Platform-specific policies

These policies map to execution plane configurations (Intune, Jamf, SCCM) and are enforced during deployment.

---

## Policy Categories

### 1. Installation Policies

| Policy | Description | Intune Mapping | Jamf Mapping | SCCM Mapping |
|--------|-------------|----------------|--------------|--------------|
| **Require Admin Install** | Force admin context installation | `installAsManaged: true` | Self Service disabled | Deploy with Admin rights |
| **Allow User Install** | Allow per-user installation | `installAsManaged: false` | Self Service enabled | Deploy with User rights |
| **Block Manual Install** | Prevent users from installing directly | Device-based + compliance | Restrict to MDM only | Disable user-initiated |
| **Silent Install Required** | Must install without user interaction | `installExperience: silent` | Install silently | `/qn` flag |

### 2. Uninstall Policies

| Policy | Description | Intune Mapping | Jamf Mapping | SCCM Mapping |
|--------|-------------|----------------|--------------|--------------|
| **Disable Uninstall** | Users cannot uninstall | Remove from Apps & Features | Uninstall policy: None | Hide in Add/Remove |
| **Admin Uninstall Only** | Only admins can uninstall | Require admin for removal | Restrict to Self Service | Advertise as mandatory |
| **Allow User Uninstall** | Users can uninstall freely | Standard behavior | Self Service uninstall | User uninstall allowed |

### 3. Update Policies

| Policy | Description | Intune Mapping | Jamf Mapping | SCCM Mapping |
|--------|-------------|----------------|--------------|--------------|
| **Auto Update** | Update automatically when available | Supersedence auto | Patch Management auto | Auto deployment |
| **Notify Before Update** | Notify user before update | Toast notification | Self Service + notify | User notification |
| **Admin Update Only** | Only admin can trigger updates | Compliance required | Admin-initiated only | IT-controlled |
| **Block Updates** | Prevent any updates | Version pinning | Version lock | Deployment locked |

### 4. Configuration Enforcement

| Policy | Description | Intune Mapping | Jamf Mapping | SCCM Mapping |
|--------|-------------|----------------|--------------|--------------|
| **Enforce Configuration** | Apply and maintain config | Config profile + remediation | Configuration profile | Baseline enforcement |
| **Detect Configuration Drift** | Report but don't remediate | Detection script | Extension attributes | DCM detection |
| **Allow User Configuration** | Users can modify settings | No restrictions | User-configurable | Default behavior |

### 5. Device Restart Policies

| Policy | Description | Intune Mapping | Jamf Mapping | SCCM Mapping |
|--------|-------------|----------------|--------------|--------------|
| **Force Restart** | Restart immediately after install | `deviceRestartBehavior: force` | Reboot payload | Force reboot |
| **Prompt Restart** | Prompt user to restart | `deviceRestartBehavior: prompt` | Defer reboot | User prompt |
| **Defer Restart** | Allow user to defer restart | `deviceRestartBehavior: defer` | Deferral options | Maintenance window |
| **No Restart Required** | App doesn't require restart | `deviceRestartBehavior: none` | No reboot | No reboot |

### 6. Dependency Policies

| Policy | Description | Mapping |
|--------|-------------|---------|
| **Enforce Dependencies** | Install dependencies first | Dependency chain in all platforms |
| **Block if Dependencies Missing** | Fail if deps not present | Pre-install check |
| **Install Dependencies Silently** | Auto-install deps | Chained deployment |

### 7. Compliance Policies

| Policy | Description | Mapping |
|--------|-------------|---------|
| **Required for Compliance** | Device non-compliant without app | Compliance policy integration |
| **Optional Installation** | App not required for compliance | Standard deployment |
| **Conditional Access Block** | Block resources if not installed | CA policy integration |

---

## Data Model

### Backend Models

```python
# backend/apps/policy_engine/models.py (extend existing)

class ApplicationPolicy(TimeStampedModel, CorrelationIdModel):
    """Deployment policies for applications."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=128)
    description = models.TextField(blank=True)

    # Target
    application = models.ForeignKey(
        'application_portfolio.Application',
        on_delete=models.CASCADE,
        related_name='policies'
    )
    application_version = models.ForeignKey(
        'application_portfolio.ApplicationVersion',
        on_delete=models.CASCADE,
        null=True, blank=True,
        help_text="Apply to specific version only (null = all versions)"
    )

    # Scope
    platform = models.CharField(max_length=32)  # windows, macos, linux, ios, android

    # Policy Status
    is_active = models.BooleanField(default=True)
    is_default = models.BooleanField(default=False)  # Default policy for app

    # Audit
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True)

    class Meta:
        unique_together = ['application', 'application_version', 'platform']


class PolicySetting(TimeStampedModel):
    """Individual policy settings."""

    class SettingCategory(models.TextChoices):
        INSTALLATION = "installation", "Installation"
        UNINSTALL = "uninstall", "Uninstall"
        UPDATE = "update", "Update"
        CONFIGURATION = "configuration", "Configuration"
        RESTART = "restart", "Device Restart"
        DEPENDENCY = "dependency", "Dependencies"
        COMPLIANCE = "compliance", "Compliance"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    policy = models.ForeignKey(ApplicationPolicy, on_delete=models.CASCADE, related_name='settings')

    category = models.CharField(max_length=32, choices=SettingCategory.choices)
    setting_key = models.CharField(max_length=64)
    setting_value = models.JSONField()  # Flexible value storage

    # Execution plane mapping
    intune_mapping = models.JSONField(default=dict, blank=True)
    jamf_mapping = models.JSONField(default=dict, blank=True)
    sccm_mapping = models.JSONField(default=dict, blank=True)

    class Meta:
        unique_together = ['policy', 'category', 'setting_key']


class PolicyTemplate(TimeStampedModel):
    """Reusable policy templates."""

    class TemplateType(models.TextChoices):
        STANDARD = "standard", "Standard Application"
        SECURITY = "security", "Security-Critical"
        PRODUCTIVITY = "productivity", "Productivity Suite"
        BROWSER = "browser", "Web Browser"
        DEVELOPMENT = "development", "Development Tool"
        ENTERPRISE = "enterprise", "Enterprise Required"
        OPTIONAL = "optional", "Optional/Self-Service"
        CUSTOM = "custom", "Custom Template"

    id = models.UUIDField(primary_key=True, default=uuid.uuid4)
    name = models.CharField(max_length=128)
    template_type = models.CharField(max_length=32, choices=TemplateType.choices)
    description = models.TextField()

    # Template settings (JSON blob)
    settings = models.JSONField(default=dict)

    # Metadata
    is_system = models.BooleanField(default=False)
    platform = models.CharField(max_length=32, blank=True)  # Empty = all platforms

    class Meta:
        ordering = ['template_type', 'name']
```

---

## Policy Templates (Pre-configured)

```python
# backend/apps/policy_engine/templates.py

POLICY_TEMPLATES = {
    "enterprise_required": {
        "name": "Enterprise Required",
        "description": "Mandatory enterprise application with strict controls",
        "settings": {
            "installation": {
                "require_admin": True,
                "silent_install": True,
                "block_manual": True,
            },
            "uninstall": {
                "mode": "disabled",
            },
            "update": {
                "mode": "auto",
                "notify_user": False,
            },
            "configuration": {
                "enforce": True,
                "detect_drift": True,
                "remediate_drift": True,
            },
            "restart": {
                "mode": "prompt",
                "deferral_hours": 4,
            },
            "compliance": {
                "required_for_compliance": True,
                "conditional_access": True,
            },
        },
    },
    "security_critical": {
        "name": "Security-Critical",
        "description": "Security tools that must always be present and running",
        "settings": {
            "installation": {
                "require_admin": True,
                "silent_install": True,
                "block_manual": True,
            },
            "uninstall": {
                "mode": "disabled",
            },
            "update": {
                "mode": "auto",
                "force_update": True,
            },
            "configuration": {
                "enforce": True,
                "remediate_drift": True,
            },
            "restart": {
                "mode": "force",
                "grace_period_minutes": 15,
            },
            "compliance": {
                "required_for_compliance": True,
                "conditional_access": True,
                "block_on_failure": True,
            },
        },
    },
    "self_service": {
        "name": "Self-Service Optional",
        "description": "Optional application available in company portal",
        "settings": {
            "installation": {
                "require_admin": False,
                "silent_install": True,
                "allow_manual": True,
            },
            "uninstall": {
                "mode": "user_allowed",
            },
            "update": {
                "mode": "notify",
            },
            "configuration": {
                "enforce": False,
                "allow_user_config": True,
            },
            "restart": {
                "mode": "none",
            },
            "compliance": {
                "required_for_compliance": False,
            },
        },
    },
    # ... more templates
}
```

---

## API Endpoints

```python
# backend/apps/policy_engine/urls.py

# Policy Templates
GET    /api/v1/policies/templates/                      # List templates
GET    /api/v1/policies/templates/{id}/                 # Template details

# Application Policies
GET    /api/v1/policies/                                # List policies
POST   /api/v1/policies/                                # Create policy
GET    /api/v1/policies/{id}/                           # Policy details
PUT    /api/v1/policies/{id}/                           # Update policy
DELETE /api/v1/policies/{id}/                           # Delete policy

# Settings
GET    /api/v1/policies/{id}/settings/                  # Get policy settings
PUT    /api/v1/policies/{id}/settings/                  # Update settings
POST   /api/v1/policies/{id}/apply-template/            # Apply template

# Validation
POST   /api/v1/policies/{id}/validate/                  # Validate policy
POST   /api/v1/policies/{id}/preview-mapping/           # Preview execution plane mapping

# Application Policies
GET    /api/v1/applications/{id}/policies/              # Get app policies
POST   /api/v1/applications/{id}/policies/              # Create app policy
```

---

## Frontend Components

### Policy Configuration Page

```tsx
// frontend/src/routes/deployments/PolicyConfiguration.tsx

interface Props {
  applicationId: string;
  versionId?: string;
}

export default function PolicyConfiguration({ applicationId, versionId }: Props) {
  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold">Deployment Policies</h2>
          <p className="text-muted-foreground">
            Configure how this application is installed, updated, and managed
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setShowTemplates(true)}>
            Apply Template
          </Button>
          <Button onClick={handleSave}>
            Save Policies
          </Button>
        </div>
      </div>

      {/* Platform Tabs */}
      <Tabs defaultValue="windows">
        <TabsList>
          <TabsTrigger value="windows">Windows</TabsTrigger>
          <TabsTrigger value="macos">macOS</TabsTrigger>
          <TabsTrigger value="linux">Linux</TabsTrigger>
          <TabsTrigger value="ios">iOS</TabsTrigger>
          <TabsTrigger value="android">Android</TabsTrigger>
        </TabsList>

        <TabsContent value="windows">
          <PolicySettingsForm platform="windows" />
        </TabsContent>
        {/* ... other platforms */}
      </Tabs>

      {/* Template Picker Dialog */}
      <TemplatePickerDialog
        open={showTemplates}
        onOpenChange={setShowTemplates}
        onSelect={handleApplyTemplate}
      />
    </div>
  );
}
```

### Policy Settings Form

```tsx
// frontend/src/components/policies/PolicySettingsForm.tsx

export function PolicySettingsForm({ platform }: { platform: string }) {
  return (
    <div className="grid gap-6 lg:grid-cols-2">
      {/* Installation Policies */}
      <PolicySection title="Installation" icon={<Download />}>
        <PolicyToggle
          label="Require Administrator"
          description="Install with admin privileges"
          settingKey="installation.require_admin"
        />
        <PolicyToggle
          label="Silent Installation"
          description="Install without user interaction"
          settingKey="installation.silent_install"
        />
        <PolicyToggle
          label="Block Manual Installation"
          description="Prevent users from installing outside MDM"
          settingKey="installation.block_manual"
        />
      </PolicySection>

      {/* Uninstall Policies */}
      <PolicySection title="Uninstall" icon={<Trash2 />}>
        <PolicySelect
          label="Uninstall Mode"
          options={[
            { value: "disabled", label: "Disabled (Users cannot uninstall)" },
            { value: "admin_only", label: "Admin Only" },
            { value: "user_allowed", label: "User Allowed" },
          ]}
          settingKey="uninstall.mode"
        />
      </PolicySection>

      {/* Update Policies */}
      <PolicySection title="Updates" icon={<RefreshCw />}>
        <PolicySelect
          label="Update Mode"
          options={[
            { value: "auto", label: "Automatic Updates" },
            { value: "notify", label: "Notify Before Update" },
            { value: "admin_only", label: "Admin Triggered Only" },
            { value: "blocked", label: "Block Updates" },
          ]}
          settingKey="update.mode"
        />
        <PolicyToggle
          label="Force Updates"
          description="Apply updates without user deferral"
          settingKey="update.force_update"
          showIf="update.mode !== 'blocked'"
        />
      </PolicySection>

      {/* Configuration Enforcement */}
      <PolicySection title="Configuration" icon={<Settings />}>
        <PolicyToggle
          label="Enforce Configuration"
          description="Apply and maintain settings profile"
          settingKey="configuration.enforce"
        />
        <PolicyToggle
          label="Detect Drift"
          description="Report configuration changes"
          settingKey="configuration.detect_drift"
        />
        <PolicyToggle
          label="Auto-Remediate"
          description="Automatically fix drift"
          settingKey="configuration.remediate_drift"
          showIf="configuration.enforce"
        />
      </PolicySection>

      {/* Restart Policies */}
      <PolicySection title="Device Restart" icon={<Power />}>
        <PolicySelect
          label="Restart Behavior"
          options={[
            { value: "none", label: "No Restart Required" },
            { value: "prompt", label: "Prompt User" },
            { value: "defer", label: "Allow Deferral" },
            { value: "force", label: "Force Restart" },
          ]}
          settingKey="restart.mode"
        />
        <PolicyInput
          label="Deferral Period (hours)"
          type="number"
          settingKey="restart.deferral_hours"
          showIf="restart.mode === 'defer'"
        />
        <PolicyInput
          label="Grace Period (minutes)"
          type="number"
          settingKey="restart.grace_period_minutes"
          showIf="restart.mode === 'force'"
        />
      </PolicySection>

      {/* Compliance Policies */}
      <PolicySection title="Compliance" icon={<Shield />}>
        <PolicyToggle
          label="Required for Compliance"
          description="Device marked non-compliant without this app"
          settingKey="compliance.required_for_compliance"
        />
        <PolicyToggle
          label="Conditional Access Integration"
          description="Block resources if app not installed"
          settingKey="compliance.conditional_access"
          showIf="compliance.required_for_compliance"
        />
      </PolicySection>
    </div>
  );
}
```

### Template Picker

```tsx
// frontend/src/components/policies/TemplatePickerDialog.tsx

const TEMPLATE_CARDS = [
  {
    id: "enterprise_required",
    name: "Enterprise Required",
    description: "Mandatory app with strict controls, no user uninstall",
    icon: <Building />,
    color: "text-blue-500",
  },
  {
    id: "security_critical",
    name: "Security-Critical",
    description: "Security tools, always present, auto-updated",
    icon: <Shield />,
    color: "text-red-500",
  },
  {
    id: "self_service",
    name: "Self-Service",
    description: "Optional app, user can install/uninstall",
    icon: <ShoppingBag />,
    color: "text-green-500",
  },
  {
    id: "productivity",
    name: "Productivity Suite",
    description: "Office apps with managed updates",
    icon: <FileText />,
    color: "text-orange-500",
  },
  {
    id: "browser",
    name: "Web Browser",
    description: "Browser with extension management",
    icon: <Globe />,
    color: "text-purple-500",
  },
];
```

---

## Execution Plane Mapping

### Policy Translator Service

```python
# backend/apps/policy_engine/services/translator.py

class PolicyTranslator:
    """Translate application policies to execution plane configurations."""

    def translate(
        self,
        policy: ApplicationPolicy,
        target_plane: str,  # intune, jamf, sccm
    ) -> dict:
        """Translate policy to target execution plane configuration."""
        if target_plane == "intune":
            return self._translate_to_intune(policy)
        elif target_plane == "jamf":
            return self._translate_to_jamf(policy)
        elif target_plane == "sccm":
            return self._translate_to_sccm(policy)
        raise ValueError(f"Unknown target plane: {target_plane}")

    def _translate_to_intune(self, policy: ApplicationPolicy) -> dict:
        """Translate to Intune Win32 app configuration."""
        settings = policy.get_settings_dict()

        config = {
            "installExperience": {
                "runAsAccount": "system" if settings.get("installation.require_admin") else "user",
                "deviceRestartBehavior": self._map_restart_mode(settings.get("restart.mode")),
            },
            "allowAvailableUninstall": settings.get("uninstall.mode") == "user_allowed",
            "supersedence": {
                "enabled": settings.get("update.mode") == "auto",
            },
        }

        # Compliance integration
        if settings.get("compliance.required_for_compliance"):
            config["requirementRules"] = [
                {"type": "registry", "operator": "exists", "path": "..."}
            ]

        return config

    def _translate_to_jamf(self, policy: ApplicationPolicy) -> dict:
        """Translate to Jamf Pro policy configuration."""
        settings = policy.get_settings_dict()

        return {
            "general": {
                "enabled": True,
                "trigger": "recurring" if settings.get("update.mode") == "auto" else "manual",
            },
            "scope": {
                "all_computers": False,
            },
            "self_service": {
                "use_for_self_service": settings.get("installation.allow_manual", True),
            },
            "package_configuration": {
                "no_uninstall": settings.get("uninstall.mode") == "disabled",
            },
            "reboot": {
                "message_enabled": settings.get("restart.mode") == "prompt",
                "no_user_logged_in": settings.get("restart.mode") == "force",
            },
        }
```

---

## Integration with Deployment Wizard

```tsx
// In DeploymentWizard.tsx, add policy step

const WIZARD_STEPS = [
  { id: "application", title: "Select Application" },
  { id: "version", title: "Select Version" },
  { id: "policy", title: "Configure Policies" },  // NEW
  { id: "targeting", title: "Target Scope" },
  { id: "schedule", title: "Schedule" },
  { id: "review", title: "Review & Submit" },
];
```

---

## Deliverables

1. `backend/apps/policy_engine/` enhancements for application policies
2. Policy templates with pre-configured settings
3. Policy translator for execution plane mapping
4. `frontend/src/components/policies/` component library
5. Integration with Deployment Wizard
6. API documentation in `docs/api/policies-api.yaml`
7. Policy guide in `docs/runbooks/application-policies.md`
