# UI Wireframes — Application & Portfolio Management

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Phase**: 0 — Foundation
**Document Version**: 1.0
**Date**: 2026-01-30

---

## Overview

This document provides wireframes and UI specifications for the Application Manager and Portfolio Manager dashboards, following the persona requirements defined in [01-persona-requirements.md](./01-persona-requirements.md).

### Design Principles

1. **Persona-Centric**: Separate dashboards optimized for each persona's primary workflows
2. **Data Density with Clarity**: Show comprehensive metrics without overwhelming the user
3. **Action-Oriented**: Primary actions prominently placed (Create Deployment, Request Packaging, Trigger AI Agent)
4. **Real-Time Updates**: Health metrics, deployment status, and alerts update automatically
5. **Responsive Design**: Desktop-first (1920×1080 target), tablet-compatible (1024×768)
6. **Accessibility**: WCAG 2.1 AA compliance (color contrast, keyboard navigation, screen reader support)

---

## Application Manager Dashboard

### Page Route
`/applications/my-applications`

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│ EUCORA Header                                                           │
│ [Logo] Dashboard  DEX  Assets  Compliance  [Packaging Factory]  ...    │
└─────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  MY APPLICATIONS                                         [Quick Actions▾]│
│  Application Manager Dashboard                                          │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────────┐│
│  │  📦 APPS      │ │  🚀 ACTIVE    │ │  💚 HEALTH    │ │  📜 LICENSE  ││
│  │  Owned        │ │  Deployments  │ │  Score        │ │  Utilization ││
│  │               │ │               │ │               │ │              ││
│  │     12        │ │      3        │ │    87%        │ │    78%       ││
│  │  applications │ │  in progress  │ │  ↑ 2% (7d)   │ │  ↓ 3% (7d)  ││
│  └───────────────┘ └───────────────┘ └───────────────┘ └──────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  🎯 My Applications                                      [🔍 Search...] │
│  [All ▾] [Healthy ▾] [Platform ▾] [Portfolio ▾]                       │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ Name            │ Health │ Deployments │ Licenses │ Actions        ││
│  ├─────────────────────────────────────────────────────────────────────┤│
│  │ Office 365      │ ●●●○○  │ Ring 3      │ 450/500  │ [View] [Deploy]││
│  │ v16.0.16227     │ 92%    │ ⏳ Pilot    │ 90% ↓3%  │                ││
│  │                                                                     ││
│  │ Adobe Acrobat   │ ●●○○○  │ Ring 2      │ 145/200  │ [View] [⚠️ Fix]││
│  │ v2024.001       │ 68%    │ ❌ Issues   │ 73% ↓12% │                ││
│  │                                                                     ││
│  │ Zoom Client     │ ●●●●○  │ Global      │ 320/350  │ [View]         ││
│  │ v5.17.5         │ 95%    │ ✅ Live     │ 91% ↑1%  │                ││
│  │                                                                     ││
│  │ Chrome Browser  │ ●●●●●  │ Global      │ 480/500  │ [View]         ││
│  │ v122.0.6261     │ 98%    │ ✅ Live     │ 96%      │                ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ⚠️ Health Alerts (3)                                   [View All →]    │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ 🔴 CRITICAL │ Adobe Acrobat - Health degraded to 68% (↓15% in 3d)  ││
│  │             │ [AI: Diagnose] [View Details]                        ││
│  ├─────────────────────────────────────────────────────────────────────┤│
│  │ 🟡 WARNING  │ Office 365 - License utilization trending down (90%) ││
│  │             │ [Right-Size] [View Details]                          ││
│  ├─────────────────────────────────────────────────────────────────────┤│
│  │ 🔵 INFO     │ Java Runtime - Security update available (v17.0.10)  ││
│  │             │ [Create Deployment] [View Details]                   ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📊 Performance Scorecard                               [Last 30 Days]  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                                                                     ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   ││
│  │  │ Success Rate    │  │ Time-to-Deploy  │  │ Avg Health      │   ││
│  │  │   92%  Target   │  │   16 days       │  │   87%           │   ││
│  │  │  (Target: 95%)  │  │  (Target: 14d)  │  │  (Target: 90%)  │   ││
│  │  │  ▁▂▃▅▆▇█        │  │  █▇▆▅▃▂▁        │  │  ▃▄▅▆▆▆█        │   ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘   ││
│  │                                                                     ││
│  │  ┌─────────────────┐  ┌─────────────────┐  ┌─────────────────┐   ││
│  │  │ License Util    │  │ MTTR            │  │ Composite Score │   ││
│  │  │   78%           │  │   5.2 hours     │  │   82/100        │   ││
│  │  │  (Target: 75%)  │  │  (Target: 4h)   │  │  ↑ 3 pts (7d)   │   ││
│  │  │  ▃▄▄▅▅▆▇        │  │  █▇▆▆▅▄▃        │  │  ▂▃▄▅▆▇█        │   ││
│  │  └─────────────────┘  └─────────────────┘  └─────────────────┘   ││
│  │                                                                     ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. KPI Cards (Top Row)
```tsx
<Card className="glass">
  <CardHeader>
    <div className="flex items-center gap-2">
      <Package className="h-5 w-5 text-eucora-teal" />
      <CardTitle className="text-sm font-medium">Applications Owned</CardTitle>
    </div>
  </CardHeader>
  <CardContent>
    <div className="text-3xl font-bold">12</div>
    <p className="text-xs text-muted-foreground">applications</p>
  </CardContent>
</Card>
```

**Behavior**:
- Auto-refresh every 30 seconds
- Hover shows tooltip with breakdown (Healthy: 9, Degraded: 2, Critical: 1)
- Click navigates to filtered view

#### 2. Applications Grid (Main Table)
```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Name</TableHead>
      <TableHead>Health</TableHead>
      <TableHead>Deployments</TableHead>
      <TableHead>Licenses</TableHead>
      <TableHead>Actions</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {applications.map((app) => (
      <TableRow key={app.id}>
        <TableCell>
          <div className="flex items-center gap-2">
            <img src={app.icon} className="h-8 w-8" />
            <div>
              <div className="font-medium">{app.name}</div>
              <div className="text-xs text-muted-foreground">v{app.version}</div>
            </div>
          </div>
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <HealthIndicator value={app.health_score} />
            <span>{app.health_score}%</span>
          </div>
        </TableCell>
        <TableCell>
          <Badge variant={app.deployment_status === 'live' ? 'default' : 'secondary'}>
            {app.deployment_ring} - {app.deployment_status}
          </Badge>
        </TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <Progress value={app.license_utilization} />
            <span className="text-sm">{app.licenses_consumed}/{app.licenses_entitled}</span>
            <TrendIcon trend={app.license_trend} />
          </div>
        </TableCell>
        <TableCell>
          <Button variant="ghost" size="sm" onClick={() => navigateTo(`/applications/${app.id}`)}>
            View
          </Button>
          {app.deployment_status !== 'live' && (
            <Button variant="outline" size="sm" onClick={() => createDeployment(app.id)}>
              Deploy
            </Button>
          )}
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

**Behavior**:
- Sortable columns (click header to sort)
- Row hover highlights entire row
- Click row (outside actions) navigates to Application Detail View
- Health indicator: ●●●●● (5 filled dots = 90-100%, 4 dots = 80-90%, etc.)

#### 3. Health Alerts Card
```tsx
<Card>
  <CardHeader>
    <CardTitle>Health Alerts</CardTitle>
    <Badge variant="destructive">3</Badge>
  </CardHeader>
  <CardContent>
    {alerts.map((alert) => (
      <div key={alert.id} className="flex items-start gap-3 p-3 rounded-lg bg-red-50">
        <AlertTriangle className={`h-5 w-5 ${getSeverityColor(alert.severity)}`} />
        <div className="flex-1">
          <p className="font-medium">{alert.application} - {alert.message}</p>
          <div className="flex gap-2 mt-2">
            <Button size="sm" variant="outline" onClick={() => triggerAIAgent('health_diagnosis', alert)}>
              AI: Diagnose
            </Button>
            <Button size="sm" variant="ghost" onClick={() => viewDetails(alert)}>
              View Details
            </Button>
          </div>
        </div>
      </div>
    ))}
  </CardContent>
</Card>
```

**Behavior**:
- Auto-refresh every 60 seconds
- Severity colors: 🔴 Critical (red), 🟡 Warning (yellow), 🔵 Info (blue)
- Click "AI: Diagnose" opens AI Agent Modal with health diagnosis
- Click "View Details" navigates to Application Detail View → Health Tab

#### 4. Performance Scorecard
```tsx
<Card>
  <CardHeader>
    <CardTitle>Performance Scorecard</CardTitle>
    <Select value={period} onValueChange={setPeriod}>
      <SelectTrigger>
        <SelectValue placeholder="Last 30 Days" />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="7d">Last 7 Days</SelectItem>
        <SelectItem value="30d">Last 30 Days</SelectItem>
        <SelectItem value="90d">Last 90 Days</SelectItem>
      </SelectContent>
    </Select>
  </CardHeader>
  <CardContent>
    <div className="grid grid-cols-3 gap-4">
      {metrics.map((metric) => (
        <div key={metric.id} className="p-4 rounded-lg bg-white/5">
          <h4 className="text-sm font-medium text-muted-foreground">{metric.name}</h4>
          <div className="flex items-baseline gap-2 mt-2">
            <span className="text-2xl font-bold">{metric.value}</span>
            <span className="text-xs text-muted-foreground">(Target: {metric.target})</span>
          </div>
          <Sparkline data={metric.trend} className="mt-2" />
          <TrendIndicator value={metric.trend_percent} />
        </div>
      ))}
    </div>
  </CardContent>
</Card>
```

**Behavior**:
- Sparkline charts show 7-day trend (mini line chart)
- Hover shows tooltip with exact values per day
- Green ↑ indicator if trending toward target, red ↓ if away from target
- Click metric card opens detailed analytics modal

#### 5. Quick Actions Menu (Top Right)
```tsx
<DropdownMenu>
  <DropdownMenuTrigger asChild>
    <Button variant="outline">
      Quick Actions <ChevronDown className="ml-2 h-4 w-4" />
    </Button>
  </DropdownMenuTrigger>
  <DropdownMenuContent align="end">
    <DropdownMenuItem onClick={() => navigate('/applications/create')}>
      <Plus className="mr-2 h-4 w-4" />
      Register New Application
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => openPackagingRequestModal()}>
      <Package className="mr-2 h-4 w-4" />
      Request Packaging
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => navigate('/deploy')}>
      <Rocket className="mr-2 h-4 w-4" />
      Create Deployment
    </DropdownMenuItem>
    <DropdownMenuSeparator />
    <DropdownMenuItem onClick={() => triggerLicenseHarvesting()}>
      <Key className="mr-2 h-4 w-4" />
      Run License Harvesting
    </DropdownMenuItem>
    <DropdownMenuItem onClick={() => navigate('/cab/my-requests')}>
      <FileCheck className="mr-2 h-4 w-4" />
      My CAB Requests
    </DropdownMenuItem>
  </DropdownMenuContent>
</DropdownMenu>
```

---

## Portfolio Manager Dashboard

### Page Route
`/portfolio/dashboard`

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│ EUCORA Header                                                           │
│ [Logo] Dashboard  DEX  Assets  Compliance  [Portfolio Management]  ... │
└─────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  PORTFOLIO MANAGEMENT                                   [Finance Apps ▾]│
│  Portfolio: Finance Applications                       [Quick Actions▾] │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐ ┌──────────────┐│
│  │  📱 APPS      │ │  💚 HEALTH    │ │  💰 TOTAL     │ │  📜 LICENSE  ││
│  │  Portfolio    │ │  Score        │ │  Cost         │ │  Utilization ││
│  │               │ │               │ │               │ │              ││
│  │     45        │ │    82/100     │ │  $1.2M/yr     │ │    76%       ││
│  │  applications │ │  ↑ 3 pts (7d) │ │  ↓ $45k (Q1) │ │  Target 75%  ││
│  └───────────────┘ └───────────────┘ └───────────────┘ └──────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  📊 Portfolio Overview               [Tabs: Apps | Team | Cost | Risk] │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                                                                     ││
│  │  APPLICATIONS (45)                          [🔍 Search] [Filter ▾] ││
│  │                                                                     ││
│  │  ┌──────────────────────────────────────────────────────────────┐  ││
│  │  │                                                              │  ││
│  │  │   Color-Coded Grid View (6×8 grid)                          │  ││
│  │  │                                                              │  ││
│  │  │   [🟢 Office365]  [🟢 Chrome]    [🟢 Zoom]     [🟢 Teams]    │  ││
│  │  │   98% Health     97% Health     95% Health    94% Health    │  ││
│  │  │   $285k/yr       $0 (free)      $68k/yr      Incl E5       │  ││
│  │  │                                                              │  ││
│  │  │   [🟡 Adobe]     [🟢 Slack]     [🟢 1Pass]    [🟢 Figma]    │  ││
│  │  │   68% Health     93% Health     91% Health    90% Health    │  ││
│  │  │   $145k/yr       $15k/yr        $24k/yr      $32k/yr       │  ││
│  │  │                                                              │  ││
│  │  │   [🔴 Java]      [🟢 Python]    [🟢 VSCode]   [🟢 Git]      │  ││
│  │  │   45% Health     89% Health     88% Health    87% Health    │  ││
│  │  │   $0 (OSS)       $0 (OSS)       $0 (free)    $0 (OSS)      │  ││
│  │  │                                                              │  ││
│  │  │   ... (more applications) ...                               │  ││
│  │  │                                                              │  ││
│  │  └──────────────────────────────────────────────────────────────┘  ││
│  │                                                                     ││
│  │  Legend: 🟢 Healthy (≥90%)  🟡 Degraded (70-89%)  🔴 Critical (<70%)││
│  │                                                                     ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  👥 Team Performance (8 Application Managers)          [View Details →] │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ Manager       │Apps│Success│Velocity│Health│License│Score│Trend    ││
│  ├─────────────────────────────────────────────────────────────────────┤│
│  │ Sarah Chen    │ 6  │ 98%   │ 11d    │ 94%  │ 79%   │94.2 │↑↑↑     ││
│  │ Mike Johnson  │ 5  │ 87%   │ 19d    │ 78%  │ 62%   │68.5 │↓↓      ││
│  │ Lisa Wong     │ 8  │ 95%   │ 13d    │ 91%  │ 82%   │89.7 │↑       ││
│  │ David Kim     │ 7  │ 92%   │ 15d    │ 85%  │ 74%   │84.3 │→       ││
│  │ ... (4 more managers) ...                                          ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
│  [AI: Generate Coaching Insights]                                      │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  🎯 Optimization Opportunities                         [AI-Generated]   │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │ 💰 License Optimization - Potential Savings: $45k/yr               ││
│  │    ├─ Right-Size Adobe CC: 200 → 160 licenses (-$26k)             ││
│  │    ├─ Harvest E5 Unused: 25 licenses (-$14k)                      ││
│  │    └─ Downgrade E5 → E3: 40 users (-$11k)                         ││
│  │    [Execute Playbook] [View Details]                              ││
│  ├─────────────────────────────────────────────────────────────────────┤│
│  │ 🗑️ Sunset Candidates - Potential Savings: $25k/yr                 ││
│  │    └─ Legacy CRM: 12 users, migrate to Salesforce                 ││
│  │    [Review] [Create Migration Plan]                               ││
│  ├─────────────────────────────────────────────────────────────────────┤│
│  │ 🔄 Consolidation Opportunities - Potential Savings: $15k/yr       ││
│  │    └─ Standardize on Teams, sunset Slack                          ││
│  │    [Review] [Create Plan]                                         ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Component Specifications

#### 1. Portfolio Selector (Top Bar)
```tsx
<Select value={selectedPortfolio} onValueChange={setSelectedPortfolio}>
  <SelectTrigger className="w-[280px]">
    <SelectValue />
  </SelectTrigger>
  <SelectContent>
    <SelectItem value="finance">Finance Applications</SelectItem>
    <SelectItem value="hr">HR Suite</SelectItem>
    <SelectItem value="engineering">Engineering Tools</SelectItem>
    <SelectItem value="all">All Portfolios (Consolidated)</SelectItem>
  </SelectContent>
</Select>
```

**Behavior**:
- Switches portfolio context (all metrics recalculate)
- "All Portfolios" shows aggregate view across all portfolios manager owns
- Selection persists in localStorage

#### 2. Portfolio Health KPI Cards
```tsx
<div className="grid grid-cols-4 gap-4">
  <Card>
    <CardContent className="pt-6">
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-xl bg-eucora-teal/20">
          <Package className="h-6 w-6 text-eucora-teal" />
        </div>
        <div>
          <p className="text-2xl font-bold">{portfolio.total_applications}</p>
          <p className="text-sm text-muted-foreground">applications</p>
        </div>
      </div>
    </CardContent>
  </Card>

  <Card>
    <CardContent className="pt-6">
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-xl bg-green-500/20">
          <Heart className="h-6 w-6 text-green-500" />
        </div>
        <div>
          <p className="text-2xl font-bold">{portfolio.health_score}/100</p>
          <p className="text-sm text-muted-foreground flex items-center gap-1">
            <TrendingUp className="h-3 w-3 text-green-500" />
            ↑ 3 pts (7d)
          </p>
        </div>
      </div>
    </CardContent>
  </Card>

  <Card>
    <CardContent className="pt-6">
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-xl bg-blue-500/20">
          <DollarSign className="h-6 w-6 text-blue-500" />
        </div>
        <div>
          <p className="text-2xl font-bold">${formatCurrency(portfolio.total_cost)}/yr</p>
          <p className="text-sm text-muted-foreground flex items-center gap-1">
            <TrendingDown className="h-3 w-3 text-green-500" />
            ↓ $45k (Q1)
          </p>
        </div>
      </div>
    </CardContent>
  </Card>

  <Card>
    <CardContent className="pt-6">
      <div className="flex items-center gap-4">
        <div className="p-3 rounded-xl bg-purple-500/20">
          <Key className="h-6 w-6 text-purple-500" />
        </div>
        <div>
          <p className="text-2xl font-bold">{portfolio.license_utilization}%</p>
          <p className="text-sm text-muted-foreground">Target: 70-85%</p>
        </div>
      </div>
    </CardContent>
  </Card>
</div>
```

#### 3. Application Grid (Color-Coded)
```tsx
<div className="grid grid-cols-6 gap-4">
  {applications.map((app) => (
    <Card
      key={app.id}
      className={cn(
        "cursor-pointer hover:border-eucora-teal transition-all",
        getHealthColorClass(app.health_score)
      )}
      onClick={() => navigate(`/applications/${app.id}`)}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center gap-2">
          <img src={app.icon} className="h-8 w-8" />
          <Badge variant={getHealthBadgeVariant(app.health_score)}>
            {app.health_score}%
          </Badge>
        </div>
        <CardTitle className="text-sm">{app.name}</CardTitle>
      </CardHeader>
      <CardContent className="pt-0">
        <p className="text-xs text-muted-foreground">
          {formatCurrency(app.annual_cost)}/yr
        </p>
        <p className="text-xs text-muted-foreground">
          Owner: {app.owner_name}
        </p>
      </CardContent>
    </Card>
  ))}
</div>
```

**Behavior**:
- Color coding: 🟢 Green border (≥90% health), 🟡 Yellow border (70-89%), 🔴 Red border (<70%)
- Hover effect: Border brightens, card elevates slightly
- Click navigates to Application Detail View
- Grid responsive: 6 cols desktop, 4 cols tablet, 2 cols mobile

#### 4. Team Performance Table
```tsx
<Table>
  <TableHeader>
    <TableRow>
      <TableHead>Manager</TableHead>
      <TableHead>Apps</TableHead>
      <TableHead>Success Rate</TableHead>
      <TableHead>Velocity</TableHead>
      <TableHead>Health</TableHead>
      <TableHead>License</TableHead>
      <TableHead>Score</TableHead>
      <TableHead>Trend</TableHead>
    </TableRow>
  </TableHeader>
  <TableBody>
    {managers.map((manager) => (
      <TableRow key={manager.id} className="cursor-pointer hover:bg-white/5">
        <TableCell>
          <div className="flex items-center gap-2">
            <Avatar src={manager.avatar} />
            <span className="font-medium">{manager.name}</span>
          </div>
        </TableCell>
        <TableCell>{manager.applications_count}</TableCell>
        <TableCell>
          <div className="flex items-center gap-2">
            <Progress value={manager.success_rate} className="w-16" />
            <span>{manager.success_rate}%</span>
          </div>
        </TableCell>
        <TableCell>{manager.avg_deployment_days}d</TableCell>
        <TableCell>{manager.avg_health_score}%</TableCell>
        <TableCell>{manager.license_utilization}%</TableCell>
        <TableCell>
          <Badge variant={getScoreBadgeVariant(manager.composite_score)}>
            {manager.composite_score}
          </Badge>
        </TableCell>
        <TableCell>
          <TrendIndicator trend={manager.trend} />
        </TableCell>
      </TableRow>
    ))}
  </TableBody>
</Table>
```

**Behavior**:
- Sortable by any column (click header)
- Click row navigates to Manager Detail View (performance deep-dive)
- Trend: ↑↑↑ Strong improvement, ↑ Improvement, → Stable, ↓ Declining, ↓↓ Strong decline
- Score badge colors: Green (≥85), Yellow (70-84), Red (<70)

#### 5. AI Optimization Opportunities Card
```tsx
<Card>
  <CardHeader>
    <CardTitle className="flex items-center gap-2">
      <Sparkles className="h-5 w-5 text-eucora-teal" />
      Optimization Opportunities
      <Badge variant="outline">AI-Generated</Badge>
    </CardTitle>
  </CardHeader>
  <CardContent>
    {opportunities.map((opp) => (
      <div key={opp.id} className="mb-4 p-4 rounded-lg bg-white/5 border border-white/10">
        <div className="flex items-start justify-between">
          <div className="flex-1">
            <h4 className="font-medium flex items-center gap-2">
              {opp.icon}
              {opp.title} - Potential Savings: {formatCurrency(opp.savings)}/yr
            </h4>
            <ul className="mt-2 space-y-1 text-sm text-muted-foreground">
              {opp.actions.map((action, idx) => (
                <li key={idx}>├─ {action.description} ({formatCurrency(action.savings)})</li>
              ))}
            </ul>
          </div>
          <div className="flex gap-2">
            <Button size="sm" variant="outline" onClick={() => executePlaybook(opp)}>
              Execute Playbook
            </Button>
            <Button size="sm" variant="ghost" onClick={() => viewDetails(opp)}>
              View Details
            </Button>
          </div>
        </div>
      </div>
    ))}

    <Button
      variant="outline"
      className="w-full mt-4"
      onClick={() => triggerAIAgent('portfolio_optimization')}
    >
      <Sparkles className="mr-2 h-4 w-4" />
      AI: Generate More Insights
    </Button>
  </CardContent>
</Card>
```

**Behavior**:
- Auto-generated weekly (or on-demand via button)
- "Execute Playbook" opens confirmation modal with approval workflow
- "View Details" opens AI Agent Modal with full recommendation breakdown
- Savings calculated by AI License Management Agent

---

## Application Detail View

### Page Route
`/applications/:id`

### Layout Structure

```
┌─────────────────────────────────────────────────────────────────────────┐
│ EUCORA Header                                                           │
└─────────────────────────────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────────────────────────────┐
│                                                                         │
│  ← Back to Applications                                                 │
│                                                                         │
│  ┌──────────┐                                                          │
│  │   ICON   │  Office 365                                              │
│  │  [Logo]  │  v16.0.16227.20318                                       │
│  └──────────┘  Owner: Sarah Chen  |  Portfolio: Finance Applications   │
│                 Category: Productivity  |  Platforms: Win, Mac         │
│                                                                         │
│  ┌───────────────┐ ┌───────────────┐ ┌───────────────┐               │
│  │  💚 HEALTH    │ │  🚀 DEPLOY    │ │  📜 LICENSE   │               │
│  │     92%       │ │  Ring 3       │ │  450/500      │               │
│  │  ●●●●○ Good   │ │  ⏳ Pilot     │ │  90% (↓3%)    │               │
│  └───────────────┘ └───────────────┘ └───────────────┘               │
│                                                                         │
│  [Create Deployment] [Request Packaging] [AI: Analyze Health] [...]   │
│                                                                         │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                         │
│  TABS: [Overview] [Versions] [Deployments] [Health] [Licenses] [Deps]  │
│                                                                         │
│  ┌─────────────────────────────────────────────────────────────────────┐│
│  │                        OVERVIEW TAB                                 ││
│  │                                                                     ││
│  │  📝 Description                                                     ││
│  │  Microsoft Office 365 suite including Word, Excel, PowerPoint,     ││
│  │  Outlook, Teams, and OneDrive. Enterprise E5 licenses with         ││
│  │  advanced security and compliance features.                        ││
│  │                                                                     ││
│  │  🏷️ Metadata                                                        ││
│  │  Publisher: Microsoft Corporation (Verified ✓)                     ││
│  │  Trust Score: 95/100                                               ││
│  │  Risk Score: 45/100 (Medium)                                       ││
│  │  Requires CAB: No (Risk ≤ 50)                                      ││
│  │  Is Privileged: No                                                 ││
│  │                                                                     ││
│  │  🔗 Dependencies (3)                                                ││
│  │  ├─ .NET Runtime 8.0 (Required)                                    ││
│  │  ├─ Visual C++ Redistributable (Required)                          ││
│  │  └─ Microsoft Edge WebView2 (Required)                             ││
│  │                                                                     ││
│  │  👥 Dependent Applications (5)                                      ││
│  │  ├─ Power BI Desktop (uses Office data connectors)                 ││
│  │  ├─ Adobe Acrobat (integrates with Outlook)                        ││
│  │  └─ ... (3 more)                                                   ││
│  │                                                                     ││
│  └─────────────────────────────────────────────────────────────────────┘│
│                                                                         │
└─────────────────────────────────────────────────────────────────────────┘
```

### Tab Specifications

#### Tab 1: Overview
- Description, metadata (publisher, trust score, risk score, CAB requirement)
- Dependencies (required, optional, build-time)
- Dependent applications (apps that depend on this one)
- Recent activity feed (deployments, health changes, incidents)

#### Tab 2: Versions
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Version History                                    [Register New Version]│
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────┐│
│ │ v16.0.16227.20318  |  2024-01-15  |  ✓ Latest  |  [View Artifacts]  ││
│ │ Release Notes: Security updates, performance improvements            ││
│ │ Artifacts: Win32 (x64), Win32 (ARM64), macOS (Universal)            ││
│ │ SBOM: ✓ Generated  |  Scan: ✓ Passed  |  Signature: ✓ Valid         ││
│ ├─────────────────────────────────────────────────────────────────────┤│
│ │ v16.0.16130.20942  |  2023-12-10  |  Deprecated  |  [View]           ││
│ │ ... (older versions) ...                                            ││
│ └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

#### Tab 3: Deployments
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Deployment History                                  [Create Deployment] │
│                                                                         │
│ ┌─────────────────────────────────────────────────────────────────────┐│
│ │ Ring 3 (Pilot) - v16.0.16227  |  In Progress  |  Started: Jan 20    ││
│ │ Progress: 1,245/1,500 devices (83%)  |  Success Rate: 97%           ││
│ │ [View Details] [Pause] [Rollback]                                   ││
│ ├─────────────────────────────────────────────────────────────────────┤│
│ │ Ring 2 (Canary) - v16.0.16227  |  Completed  |  Jan 15 - Jan 18     ││
│ │ Progress: 150/150 devices (100%)  |  Success Rate: 98%              ││
│ │ [View Report]                                                       ││
│ └─────────────────────────────────────────────────────────────────────┘│
└─────────────────────────────────────────────────────────────────────────┘
```

#### Tab 4: Health
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Application Health                              [AI: Diagnose Issues]   │
│                                                                         │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │                                                                    │ │
│ │  Health Trend (30 Days)                                            │ │
│ │  100% ┤                                                            │ │
│ │       │        ╭──────╮                                            │ │
│ │   92% ┤────────╯      ╰──╮                                         │ │
│ │       │                   ╰───────                                 │ │
│ │   80% ┤                            ╰──────────                     │ │
│ │       └──────────────────────────────────────────────────────────  │ │
│ │       Jan 1      Jan 10      Jan 20      Jan 30                    │ │
│ │                                                                    │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ Installation Breakdown                                                  │
│ ├─ Healthy: 4,140 devices (92%)                                        │
│ ├─ Degraded: 270 devices (6%)                                          │
│ ├─ Critical: 90 devices (2%)                                           │
│ └─ Total: 4,500 installations                                          │
│                                                                         │
│ Common Errors (Last 7 Days)                                             │
│ ├─ 0x80070643: Installation failure (45 occurrences)                   │
│ ├─ 0x80070005: Access denied (12 occurrences)                          │
│ └─ ... (more errors)                                                   │
│                                                                         │
│ [AI: Analyze Error Patterns] [Export Health Report]                    │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Tab 5: Licenses
```
┌─────────────────────────────────────────────────────────────────────────┐
│ License Management                                 [AI: Optimize]       │
│                                                                         │
│ Microsoft 365 E5                                                        │
│ ├─ Entitled: 500 licenses                                              │
│ ├─ Consumed: 450 licenses (90%)                                        │
│ ├─ Remaining: 50 licenses                                              │
│ └─ Annual Cost: $285,000 ($570/license)                                │
│                                                                         │
│ Utilization Trend (90 Days)                                             │
│ 100% ┤                                                                  │
│      │  ╭────────╮                                                      │
│  90% ┤──╯        ╰──╮                                                   │
│      │               ╰────────                                          │
│  80% ┤                        ╰────────                                 │
│      └──────────────────────────────────────────────────────────────── │
│                                                                         │
│ Optimization Opportunities                                              │
│ ├─ Harvest Inactive: 25 licenses (no usage >90d) - Save $14,250/yr    │
│ ├─ Downgrade E5→E3: 40 users (minimal feature usage) - Save $11,400/yr│
│ └─ Total Potential Savings: $25,650/yr                                 │
│                                                                         │
│ [Execute Harvesting] [Review Downgrade Candidates] [View Assignments]  │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Tab 6: Dependencies
```
┌─────────────────────────────────────────────────────────────────────────┐
│ Dependency Graph                                [AI: Analyze Conflicts] │
│                                                                         │
│ ┌────────────────────────────────────────────────────────────────────┐ │
│ │                                                                    │ │
│ │                     Dependency Visualization                       │ │
│ │                                                                    │ │
│ │         [.NET Runtime 8.0]                                         │ │
│ │               │                                                    │ │
│ │               ├────→ [Office 365] ←──── You are here              │ │
│ │               │            │                                       │ │
│ │               │            ├────→ [Power BI Desktop]              │ │
│ │               │            └────→ [Adobe Acrobat]                 │ │
│ │               │                                                    │ │
│ │         [Visual C++ Redist]                                        │ │
│ │               │                                                    │ │
│ │               └────→ [Office 365]                                  │ │
│ │                                                                    │ │
│ └────────────────────────────────────────────────────────────────────┘ │
│                                                                         │
│ Upstream Dependencies (Required by this app)                            │
│ ├─ .NET Runtime 8.0 (v8.0.1) - Status: ✓ Healthy                       │
│ ├─ Visual C++ Redistributable (v14.38) - Status: ✓ Healthy             │
│ └─ Microsoft Edge WebView2 (v120.0.2210) - Status: ✓ Healthy           │
│                                                                         │
│ Downstream Dependents (Apps that depend on this)                        │
│ ├─ Power BI Desktop - Status: ✓ Healthy                                │
│ ├─ Adobe Acrobat - Status: ⚠️ Degraded (68% health)                    │
│ └─ ... (3 more)                                                         │
│                                                                         │
│ [Update Dependency] [View Compatibility Matrix] [AI: Check Conflicts]  │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## AI Agent Modal (Universal)

### Component Specification

```tsx
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent className="max-w-4xl">
    <DialogHeader>
      <DialogTitle className="flex items-center gap-2">
        <Sparkles className="h-5 w-5 text-eucora-teal" />
        AI Recommendation: {task.agent_name}
      </DialogTitle>
      <DialogDescription>
        Review the AI-generated recommendation below. All actions require your explicit approval.
      </DialogDescription>
    </DialogHeader>

    <div className="space-y-6">
      {/* Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Summary</CardTitle>
        </CardHeader>
        <CardContent>
          <p>{recommendation.summary}</p>
        </CardContent>
      </Card>

      {/* Rationale */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Rationale</CardTitle>
        </CardHeader>
        <CardContent>
          <ul className="list-disc pl-5 space-y-1">
            {recommendation.rationale.map((item, idx) => (
              <li key={idx}>{item}</li>
            ))}
          </ul>
        </CardContent>
      </Card>

      {/* Impact Analysis */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Impact Analysis</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-2">
            <div className="flex justify-between">
              <span>Affected Users:</span>
              <span className="font-medium">{recommendation.impact.affected_users}</span>
            </div>
            <div className="flex justify-between">
              <span>Affected Devices:</span>
              <span className="font-medium">{recommendation.impact.affected_devices}</span>
            </div>
            <div className="flex justify-between">
              <span>Estimated Cost Impact:</span>
              <span className="font-medium">{formatCurrency(recommendation.impact.cost)}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Risk Assessment */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg flex items-center gap-2">
            Risk Assessment
            <Badge variant={getRiskBadgeVariant(recommendation.risk)}>
              {recommendation.risk}
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <p className="text-sm text-muted-foreground">{recommendation.risk_explanation}</p>
        </CardContent>
      </Card>

      {/* Approval Section */}
      <Card>
        <CardHeader>
          <CardTitle className="text-lg">Your Decision</CardTitle>
        </CardHeader>
        <CardContent>
          <Textarea
            placeholder="Add comments or rationale for your decision (optional)"
            value={comments}
            onChange={(e) => setComments(e.target.value)}
            className="mb-4"
          />
          <div className="flex gap-3">
            <Button
              variant="default"
              className="flex-1"
              onClick={() => handleApprove(task.id, comments)}
            >
              <CheckCircle className="mr-2 h-4 w-4" />
              Approve & Execute
            </Button>
            <Button
              variant="outline"
              className="flex-1"
              onClick={() => handleReject(task.id, comments)}
            >
              <XCircle className="mr-2 h-4 w-4" />
              Reject
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  </DialogContent>
</Dialog>
```

**Behavior**:
- Modal opens when user clicks "AI: ..." button on any dashboard
- Recommendation displayed with full context (summary, rationale, impact, risk)
- User must explicitly approve or reject (no default action)
- Comments optional but recommended for audit trail
- On approve: Action executes with correlation ID, user notified of progress
- On reject: Feedback logged for AI model learning

---

## Responsive Breakpoints

```css
/* Desktop (default): 1920×1080 */
.application-grid { grid-template-columns: repeat(6, 1fr); }
.team-performance-table { display: table; }

/* Laptop: 1366×768 */
@media (max-width: 1536px) {
  .application-grid { grid-template-columns: repeat(4, 1fr); }
  .kpi-cards { grid-template-columns: repeat(2, 1fr); }
}

/* Tablet: 1024×768 */
@media (max-width: 1280px) {
  .application-grid { grid-template-columns: repeat(3, 1fr); }
  .team-performance-table { font-size: 0.875rem; }
  .sidebar { width: 200px; }
}

/* Mobile: 768×1024 (portrait tablet) */
@media (max-width: 1024px) {
  .application-grid { grid-template-columns: repeat(2, 1fr); }
  .kpi-cards { grid-template-columns: repeat(2, 1fr); }
  .team-performance-table { display: block; overflow-x: auto; }
}
```

---

## Accessibility Requirements

### Keyboard Navigation
- All interactive elements reachable via Tab key
- Modal focus trap (Tab cycles within modal)
- Escape key closes modals
- Enter key activates buttons

### Screen Reader Support
```tsx
<Card aria-label="Application health status">
  <div role="status" aria-live="polite">
    Health: {health}%
  </div>
</Card>

<Button aria-label="Trigger AI health diagnosis">
  AI: Diagnose
</Button>
```

### Color Contrast
- Text on background: ≥4.5:1 (WCAG AA)
- UI components: ≥3:1 (WCAG AA)
- Health indicators: Not color-only (use icons + text)

### Focus Indicators
```css
button:focus-visible {
  outline: 2px solid var(--eucora-teal);
  outline-offset: 2px;
}
```

---

## Performance Targets

| Metric | Target | Measurement |
|--------|--------|-------------|
| **Initial Page Load** | ≤2s | Time to interactive (TTI) |
| **Dashboard Refresh** | ≤500ms | API response + render |
| **Application Grid Render** | ≤1s | 100 applications |
| **AI Agent Modal** | ≤5s | Agent response time |
| **Tab Switch** | ≤100ms | No network request |

### Optimization Strategies
- **Code Splitting**: Lazy load tabs (React.lazy)
- **Data Pagination**: Application grid paginated (50/page)
- **Caching**: React Query with stale-while-revalidate
- **Virtualization**: Long lists (react-window for 100+ items)
- **Debouncing**: Search input debounced (300ms)

---

## Component Library (Shadcn/ui)

All components use Shadcn/ui with Eucora theme:

```tsx
// Theme colors
const colors = {
  'eucora-teal': 'hsl(180, 50%, 45%)',
  'eucora-coral': 'hsl(15, 75%, 60%)',
  'eucora-slate': 'hsl(215, 20%, 15%)',
};

// Components used
import { Card, CardHeader, CardTitle, CardContent } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Table, TableHeader, TableRow, TableHead, TableBody, TableCell } from '@/components/ui/table';
import { Select, SelectTrigger, SelectValue, SelectContent, SelectItem } from '@/components/ui/select';
import { Dialog, DialogContent, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { Progress } from '@/components/ui/progress';
import { Textarea } from '@/components/ui/textarea';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
```

---

## Next Steps

1. **Prototype in Figma**: Create high-fidelity mockups with interactive prototypes
2. **User Testing**: Validate with pilot Application Manager and Portfolio Manager
3. **Component Development**: Build reusable components (ApplicationCard, TeamPerformanceTable, AIAgentModal)
4. **Data Integration**: Connect to backend APIs (Phase 1 deliverables)
5. **Accessibility Audit**: Test with screen readers, keyboard navigation, color contrast tools

---

**Document Owner**: UX Design Lead
**Review Required From**: Application Manager (pilot user), Portfolio Manager (pilot user), Frontend Lead
**Next Review Date**: 2026-02-06
