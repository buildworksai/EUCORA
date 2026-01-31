# E6: Application Stack UX — Best-in-Class Deployment Visualization

**SPDX-License-Identifier: Apache-2.0**
**Copyright (c) 2026 BuildWorks.AI**

**Document Version**: 1.0
**Date**: 2026-01-30
**Status**: Draft for Implementation
**Priority**: P2-High
**Dependencies**: E5 (Application Policy UI)

---

## Overview

Transform the current Application Stack page (DeploymentsSidebar) into a comprehensive, best-in-class deployment visualization with:
- Rich tree hierarchy (App → Version → Deployment → Ring)
- Real-time status updates
- Dependency visualization
- Timeline view
- Quick actions
- Advanced filtering and search

---

## Current State Analysis

The existing `DeploymentsSidebar.tsx` provides:
- Basic tree structure (App → Version → Deployment)
- Status icons
- Ring badges
- Search functionality

**Gaps to address**:
- No dependency visualization
- No timeline view
- Limited actions
- No real-time updates
- Basic UX patterns
- No drill-down details

---

## Design Requirements

### 1. Tree Visualization Enhancements

```
Application Stack (Best-in-Class)
├── [Expand All] [Collapse All] [Refresh]
├── Search: [____________] [Filters ▼]
│
├── 📦 Microsoft Office 365 ───────────────── [3 versions] [12 deployments]
│   ├── ▶ v16.0.17328.20162 (Latest) ──────── [Active] [Global]
│   │   ├── 🟢 Ring 4: Global ─────────────── 99.2% success │ 45,230 devices
│   │   ├── 🟢 Ring 3: Department ─────────── 99.5% success │ 8,450 devices
│   │   ├── 🟢 Ring 2: Pilot ──────────────── 98.1% success │ 1,200 devices
│   │   └── 🟢 Ring 1: Canary ─────────────── 97.8% success │ 150 devices
│   ├── ▶ v16.0.17231.20236 ───────────────── [Deprecated] [Rollback Available]
│   └── ▶ v16.0.17126.20132 ───────────────── [Archived]
│
├── 📦 Google Chrome ──────────────────────── [2 versions] [8 deployments]
│   ├── ▶ v120.0.6099.130 (Latest) ────────── [In Progress] [Ring 3]
│   │   ├── 🔵 Ring 3: Department ─────────── Deploying... │ 2,340 / 8,450
│   │   ├── 🟢 Ring 2: Pilot ──────────────── 99.1% success │ 1,200 devices
│   │   └── 🟢 Ring 1: Canary ─────────────── 98.5% success │ 150 devices
│   └── ▶ v120.0.6099.71 ──────────────────── [Active] [Global]
```

### 2. Detail Panel

When an item is selected, show a detail panel with:

**Application Level**:
- Application metadata (owner, category, policies)
- Version history timeline
- Health score trend
- License usage (if tracked)

**Version Level**:
- Artifact details (hash, signature, SBOM summary)
- Vulnerability scan status
- CAB approval status
- Evidence pack link

**Deployment Level**:
- Ring progression chart
- Success/failure breakdown
- Device distribution
- Timeline of events

**Ring Level**:
- Device list with status
- Error log (failures)
- Performance metrics
- Quick actions (pause, resume, rollback)

### 3. View Modes

| Mode | Description | Use Case |
|------|-------------|----------|
| **Tree View** | Hierarchical app/version/ring | Default navigation |
| **Timeline View** | Chronological deployment events | Audit and history |
| **Grid View** | Card-based overview | Quick scanning |
| **Dependency View** | Graph of app dependencies | Impact analysis |

---

## Component Architecture

### Main Page Component

```tsx
// frontend/src/routes/deployments/ApplicationStack.tsx

export default function ApplicationStack() {
  const [viewMode, setViewMode] = useState<'tree' | 'timeline' | 'grid' | 'dependency'>('tree');
  const [selectedItem, setSelectedItem] = useState<StackItem | null>(null);
  const [filters, setFilters] = useState<StackFilters>(defaultFilters);

  return (
    <div className="flex h-full">
      {/* Left Panel: Navigation */}
      <div className="w-[400px] border-r flex flex-col">
        {/* Header */}
        <StackHeader
          viewMode={viewMode}
          onViewModeChange={setViewMode}
          filters={filters}
          onFiltersChange={setFilters}
        />

        {/* View Content */}
        {viewMode === 'tree' && (
          <TreeView
            filters={filters}
            selectedItem={selectedItem}
            onSelectItem={setSelectedItem}
          />
        )}
        {viewMode === 'timeline' && (
          <TimelineView filters={filters} onSelectItem={setSelectedItem} />
        )}
        {viewMode === 'grid' && (
          <GridView filters={filters} onSelectItem={setSelectedItem} />
        )}
        {viewMode === 'dependency' && (
          <DependencyGraph filters={filters} onSelectItem={setSelectedItem} />
        )}
      </div>

      {/* Right Panel: Details */}
      <div className="flex-1">
        {selectedItem ? (
          <DetailPanel item={selectedItem} />
        ) : (
          <EmptyDetailPanel />
        )}
      </div>
    </div>
  );
}
```

### Enhanced Tree View

```tsx
// frontend/src/components/stack/TreeView.tsx

interface TreeNode {
  id: string;
  type: 'application' | 'version' | 'deployment' | 'ring';
  data: any;
  children?: TreeNode[];
  status: 'healthy' | 'deploying' | 'warning' | 'error' | 'archived';
}

export function TreeView({ filters, selectedItem, onSelectItem }: Props) {
  const { data: applications, isLoading } = useStackApplications(filters);

  return (
    <ScrollArea className="flex-1">
      <div className="p-4 space-y-1">
        {applications?.map(app => (
          <ApplicationNode
            key={app.id}
            application={app}
            isSelected={selectedItem?.id === app.id}
            onSelect={() => onSelectItem({ type: 'application', ...app })}
          >
            {app.versions.map(version => (
              <VersionNode
                key={version.id}
                version={version}
                isSelected={selectedItem?.id === version.id}
                onSelect={() => onSelectItem({ type: 'version', ...version })}
              >
                {version.deployments.map(deployment => (
                  <DeploymentNode
                    key={deployment.id}
                    deployment={deployment}
                    isSelected={selectedItem?.id === deployment.id}
                    onSelect={() => onSelectItem({ type: 'deployment', ...deployment })}
                  >
                    {deployment.rings.map(ring => (
                      <RingNode
                        key={ring.ring}
                        ring={ring}
                        isSelected={selectedItem?.id === `${deployment.id}-${ring.ring}`}
                        onSelect={() => onSelectItem({ type: 'ring', ...ring, deploymentId: deployment.id })}
                      />
                    ))}
                  </DeploymentNode>
                ))}
              </VersionNode>
            ))}
          </ApplicationNode>
        ))}
      </div>
    </ScrollArea>
  );
}
```

### Timeline View

```tsx
// frontend/src/components/stack/TimelineView.tsx

export function TimelineView({ filters, onSelectItem }: Props) {
  const { data: events } = useDeploymentEvents(filters);

  return (
    <ScrollArea className="flex-1">
      <div className="relative p-4">
        {/* Timeline line */}
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-border" />

        {/* Events */}
        <div className="space-y-4">
          {events?.map(event => (
            <TimelineEvent
              key={event.id}
              event={event}
              onClick={() => onSelectItem(event.item)}
            />
          ))}
        </div>
      </div>
    </ScrollArea>
  );
}

function TimelineEvent({ event, onClick }: { event: DeploymentEvent; onClick: () => void }) {
  const statusIcon = EVENT_STATUS_ICONS[event.status];

  return (
    <div className="relative pl-12 cursor-pointer group" onClick={onClick}>
      {/* Timeline dot */}
      <div className={cn(
        "absolute left-6 w-4 h-4 rounded-full border-2 border-background",
        EVENT_COLORS[event.status]
      )}>
        <statusIcon.icon className="w-2 h-2 text-white" />
      </div>

      {/* Event card */}
      <Card className="group-hover:border-eucora-teal/50 transition-colors">
        <CardContent className="p-3">
          <div className="flex items-center justify-between">
            <div>
              <p className="font-medium">{event.title}</p>
              <p className="text-sm text-muted-foreground">{event.description}</p>
            </div>
            <div className="text-right text-sm text-muted-foreground">
              <p>{formatRelativeTime(event.timestamp)}</p>
              <p>{event.user}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### Dependency Graph

```tsx
// frontend/src/components/stack/DependencyGraph.tsx

import ReactFlow, { Node, Edge, Background, Controls } from 'reactflow';

export function DependencyGraph({ filters, onSelectItem }: Props) {
  const { data: dependencies } = useApplicationDependencies(filters);

  const nodes: Node[] = dependencies?.applications.map(app => ({
    id: app.id,
    type: 'applicationNode',
    position: app.position,
    data: { application: app },
  })) || [];

  const edges: Edge[] = dependencies?.relationships.map(rel => ({
    id: `${rel.source}-${rel.target}`,
    source: rel.source,
    target: rel.target,
    label: rel.type,
    animated: rel.type === 'runtime',
  })) || [];

  return (
    <div className="h-full">
      <ReactFlow
        nodes={nodes}
        edges={edges}
        nodeTypes={{ applicationNode: ApplicationGraphNode }}
        fitView
      >
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}
```

### Detail Panel

```tsx
// frontend/src/components/stack/DetailPanel.tsx

export function DetailPanel({ item }: { item: StackItem }) {
  switch (item.type) {
    case 'application':
      return <ApplicationDetail application={item} />;
    case 'version':
      return <VersionDetail version={item} />;
    case 'deployment':
      return <DeploymentDetail deployment={item} />;
    case 'ring':
      return <RingDetail ring={item} />;
    default:
      return <EmptyDetailPanel />;
  }
}

function ApplicationDetail({ application }: { application: Application }) {
  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-start justify-between">
        <div className="flex items-center gap-4">
          <div className="w-12 h-12 rounded-lg bg-eucora-teal/10 flex items-center justify-center">
            <Package className="w-6 h-6 text-eucora-teal" />
          </div>
          <div>
            <h2 className="text-xl font-bold">{application.name}</h2>
            <p className="text-muted-foreground">{application.vendor}</p>
          </div>
        </div>
        <QuickActions application={application} />
      </div>

      {/* Stats */}
      <div className="grid grid-cols-4 gap-4">
        <StatCard label="Health Score" value={application.healthScore} trend="+2.3%" />
        <StatCard label="Devices" value={formatNumber(application.deviceCount)} />
        <StatCard label="Versions" value={application.versionCount} />
        <StatCard label="Active Deployments" value={application.activeDeployments} />
      </div>

      {/* Tabs */}
      <Tabs defaultValue="overview">
        <TabsList>
          <TabsTrigger value="overview">Overview</TabsTrigger>
          <TabsTrigger value="versions">Versions</TabsTrigger>
          <TabsTrigger value="deployments">Deployments</TabsTrigger>
          <TabsTrigger value="policies">Policies</TabsTrigger>
          <TabsTrigger value="dependencies">Dependencies</TabsTrigger>
          <TabsTrigger value="audit">Audit Log</TabsTrigger>
        </TabsList>

        <TabsContent value="overview">
          <ApplicationOverview application={application} />
        </TabsContent>
        <TabsContent value="versions">
          <VersionHistory applicationId={application.id} />
        </TabsContent>
        <TabsContent value="deployments">
          <DeploymentHistory applicationId={application.id} />
        </TabsContent>
        <TabsContent value="policies">
          <PolicySummary applicationId={application.id} />
        </TabsContent>
        <TabsContent value="dependencies">
          <DependencyList applicationId={application.id} />
        </TabsContent>
        <TabsContent value="audit">
          <AuditLog resourceType="application" resourceId={application.id} />
        </TabsContent>
      </Tabs>
    </div>
  );
}
```

### Quick Actions

```tsx
// frontend/src/components/stack/QuickActions.tsx

interface QuickActionsProps {
  item: StackItem;
}

export function QuickActions({ item }: QuickActionsProps) {
  const actions = getActionsForItem(item);

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild>
        <Button variant="outline" size="icon">
          <MoreHorizontal className="w-4 h-4" />
        </Button>
      </DropdownMenuTrigger>
      <DropdownMenuContent align="end" className="w-56">
        <DropdownMenuLabel>Actions</DropdownMenuLabel>
        <DropdownMenuSeparator />

        {actions.includes('deploy') && (
          <DropdownMenuItem onClick={() => navigate(`/deploy?app=${item.id}`)}>
            <Rocket className="mr-2 h-4 w-4" />
            New Deployment
          </DropdownMenuItem>
        )}

        {actions.includes('promote') && (
          <DropdownMenuItem onClick={() => handlePromote(item)}>
            <ArrowUpCircle className="mr-2 h-4 w-4" />
            Promote to Next Ring
          </DropdownMenuItem>
        )}

        {actions.includes('rollback') && (
          <DropdownMenuItem onClick={() => handleRollback(item)} className="text-orange-500">
            <RotateCcw className="mr-2 h-4 w-4" />
            Rollback
          </DropdownMenuItem>
        )}

        {actions.includes('pause') && (
          <DropdownMenuItem onClick={() => handlePause(item)}>
            <Pause className="mr-2 h-4 w-4" />
            Pause Deployment
          </DropdownMenuItem>
        )}

        {actions.includes('cancel') && (
          <DropdownMenuItem onClick={() => handleCancel(item)} className="text-red-500">
            <XCircle className="mr-2 h-4 w-4" />
            Cancel Deployment
          </DropdownMenuItem>
        )}

        <DropdownMenuSeparator />

        <DropdownMenuItem onClick={() => handleViewEvidence(item)}>
          <FileText className="mr-2 h-4 w-4" />
          View Evidence Pack
        </DropdownMenuItem>

        <DropdownMenuItem onClick={() => handleExport(item)}>
          <Download className="mr-2 h-4 w-4" />
          Export Report
        </DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  );
}
```

---

## Real-Time Updates

### WebSocket Integration

```tsx
// frontend/src/lib/websocket/useDeploymentUpdates.ts

export function useDeploymentUpdates(applicationId?: string) {
  const queryClient = useQueryClient();

  useEffect(() => {
    const ws = new WebSocket(`${WS_URL}/deployments`);

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      // Update cache based on event type
      switch (update.type) {
        case 'ring_progress':
          queryClient.invalidateQueries(['stack', 'deployment', update.deploymentId]);
          break;
        case 'deployment_status':
          queryClient.invalidateQueries(['stack', 'applications']);
          break;
        case 'promotion_complete':
          queryClient.invalidateQueries(['stack']);
          toast.success(`${update.applicationName} promoted to ${update.ring}`);
          break;
      }
    };

    return () => ws.close();
  }, [applicationId, queryClient]);
}
```

---

## Filtering & Search

```tsx
// frontend/src/components/stack/StackFilters.tsx

interface StackFilters {
  search: string;
  status: ('active' | 'deploying' | 'paused' | 'completed' | 'failed' | 'archived')[];
  platform: ('windows' | 'macos' | 'linux' | 'ios' | 'android')[];
  ring: ('lab' | 'canary' | 'pilot' | 'department' | 'global')[];
  owner: string[];
  dateRange: { from: Date; to: Date } | null;
}

export function StackFiltersPanel({ filters, onChange }: Props) {
  return (
    <Popover>
      <PopoverTrigger asChild>
        <Button variant="outline" size="sm">
          <Filter className="mr-2 h-4 w-4" />
          Filters
          {activeFilterCount > 0 && (
            <Badge variant="secondary" className="ml-2">{activeFilterCount}</Badge>
          )}
        </Button>
      </PopoverTrigger>
      <PopoverContent className="w-80" align="start">
        <div className="space-y-4">
          {/* Status Filter */}
          <div className="space-y-2">
            <Label>Status</Label>
            <div className="flex flex-wrap gap-2">
              {STATUS_OPTIONS.map(status => (
                <Toggle
                  key={status.value}
                  pressed={filters.status.includes(status.value)}
                  onPressedChange={(pressed) => handleStatusToggle(status.value, pressed)}
                  size="sm"
                >
                  <status.icon className="mr-1 h-3 w-3" />
                  {status.label}
                </Toggle>
              ))}
            </div>
          </div>

          {/* Platform Filter */}
          <div className="space-y-2">
            <Label>Platform</Label>
            {/* Similar toggle group */}
          </div>

          {/* Ring Filter */}
          <div className="space-y-2">
            <Label>Ring</Label>
            {/* Similar toggle group */}
          </div>

          {/* Date Range */}
          <div className="space-y-2">
            <Label>Date Range</Label>
            <DateRangePicker
              value={filters.dateRange}
              onChange={(range) => onChange({ ...filters, dateRange: range })}
            />
          </div>

          <Button variant="outline" size="sm" onClick={resetFilters}>
            Reset Filters
          </Button>
        </div>
      </PopoverContent>
    </Popover>
  );
}
```

---

## API Enhancements

```python
# backend/apps/deployment_intents/urls.py

# Stack Data
GET    /api/v1/stack/applications/                   # List with nested structure
GET    /api/v1/stack/applications/{id}/              # Application details
GET    /api/v1/stack/applications/{id}/versions/     # Version list
GET    /api/v1/stack/applications/{id}/dependencies/ # Dependency graph

# Timeline
GET    /api/v1/stack/events/                         # Deployment events timeline
GET    /api/v1/stack/events/stream/                  # WebSocket event stream

# Actions
POST   /api/v1/stack/deployments/{id}/promote/       # Promote to next ring
POST   /api/v1/stack/deployments/{id}/pause/         # Pause deployment
POST   /api/v1/stack/deployments/{id}/resume/        # Resume deployment
POST   /api/v1/stack/deployments/{id}/rollback/      # Initiate rollback
POST   /api/v1/stack/deployments/{id}/cancel/        # Cancel deployment
```

---

## Deliverables

1. `frontend/src/routes/deployments/ApplicationStack.tsx` redesigned page
2. `frontend/src/components/stack/` component library
3. Tree, Timeline, Grid, and Dependency view components
4. Detail panel with tabs for different item types
5. Real-time WebSocket updates
6. Advanced filtering and search
7. Quick actions for common operations
8. API enhancements for nested data
9. Export functionality (CSV, PDF reports)
