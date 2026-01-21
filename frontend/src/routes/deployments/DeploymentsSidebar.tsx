// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState, useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Badge } from '@/components/ui/badge';
import { SkeletonList } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible';
import {
  ChevronRight,
  Package,
  CheckCircle2,
  AlertCircle,
  Clock,
  Search,
} from 'lucide-react';
import { useSidebarApplications } from '@/lib/api/hooks/useSidebarApplications';
import { cn } from '@/lib/utils';
import type { SidebarApplicationGroup, SidebarVersionEntry } from '@/routes/deployments/sidebar-contracts';

/**
 * Status-to-icon mapping with color.
 */
const STATUS_ICONS: Record<
  string,
  { icon: React.ComponentType<{ className?: string }>; color: string }
> = {
  COMPLETED: {
    icon: CheckCircle2,
    color: 'text-eucora-green',
  },
  APPROVED: {
    icon: CheckCircle2,
    color: 'text-eucora-green',
  },
  DEPLOYING: {
    icon: Clock,
    color: 'text-eucora-teal',
  },
  AWAITING_CAB: {
    icon: AlertCircle,
    color: 'text-eucora-gold',
  },
  PENDING: {
    icon: Clock,
    color: 'text-muted-foreground',
  },
  REJECTED: {
    icon: AlertCircle,
    color: 'text-eucora-red',
  },
  FAILED: {
    icon: AlertCircle,
    color: 'text-eucora-red',
  },
  ROLLED_BACK: {
    icon: AlertCircle,
    color: 'text-eucora-gold',
  },
};

const RING_COLORS: Record<string, string> = {
  LAB: 'bg-slate-500/10 text-slate-700 border-slate-200',
  CANARY: 'bg-eucora-teal/10 text-eucora-teal border-eucora-teal/30',
  PILOT: 'bg-blue-500/10 text-blue-700 border-blue-200',
  DEPARTMENT: 'bg-purple-500/10 text-purple-700 border-purple-200',
  GLOBAL: 'bg-eucora-green/10 text-eucora-green border-eucora-green/30',
};

/**
 * Single deployment row within a version.
 */
function DeploymentRow({
  deployment,
}: {
  deployment: SidebarApplicationGroup['versions'][0]['deployments'][0];
}) {
  const statusIcon = STATUS_ICONS[deployment.status] || STATUS_ICONS.PENDING;
  const StatusIcon = statusIcon.icon;

  return (
    <div className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-white/5 transition-colors text-xs group">
      <div className="flex items-center gap-2 flex-1 min-w-0">
        <StatusIcon className={cn('w-3 h-3 flex-shrink-0', statusIcon.color)} />
        <span className="text-muted-foreground truncate">{deployment.target_ring}</span>
        <Badge
          variant="outline"
          className={cn('text-[10px] h-5 flex-shrink-0', RING_COLORS[deployment.target_ring])}
        >
          {deployment.status}
        </Badge>
      </div>
      {deployment.risk_score !== null && (
        <div
          className={cn(
            'ml-2 px-2 py-0.5 rounded text-[10px] font-mono flex-shrink-0',
            deployment.risk_score > 50
              ? 'bg-eucora-red/20 text-eucora-red'
              : 'bg-eucora-green/20 text-eucora-green'
          )}
        >
          R:{deployment.risk_score}
        </div>
      )}
    </div>
  );
}

/**
 * Version entry (collapsible list of deployments).
 */
function VersionEntry({
  version,
}: {
  version: SidebarVersionEntry;
}) {
  const [isOpen, setIsOpen] = useState(false);
  const deploymentCount = version.deployments.length;
  const latestDeployment = version.deployments[0];

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="w-full">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors text-sm group cursor-pointer">
          <ChevronRight
            className={cn(
              'w-4 h-4 text-muted-foreground transition-transform flex-shrink-0',
              isOpen && 'rotate-90'
            )}
          />
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="font-mono text-xs font-semibold text-foreground">
              v{version.version}
            </span>
            <Badge variant="secondary" className="text-[10px] h-5 flex-shrink-0">
              {deploymentCount}
            </Badge>
          </div>
          {latestDeployment && (
            <span className="text-[10px] text-muted-foreground whitespace-nowrap flex-shrink-0">
              {new Date(latestDeployment.created_at).toLocaleDateString()}
            </span>
          )}
        </div>
      </CollapsibleTrigger>
      {isOpen && (
        <CollapsibleContent className="pl-6 space-y-1 mt-1 border-l border-white/10">
          {version.deployments.map((deployment) => (
            <DeploymentRow key={deployment.correlation_id} deployment={deployment} />
          ))}
        </CollapsibleContent>
      )}
    </Collapsible>
  );
}

/**
 * Application entry (collapsible list of versions).
 */
function ApplicationEntry({
  app,
}: {
  app: SidebarApplicationGroup;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="w-full">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors font-semibold group cursor-pointer">
          <ChevronRight
            className={cn(
              'w-5 h-5 text-muted-foreground transition-transform flex-shrink-0',
              isOpen && 'rotate-90'
            )}
          />
          <Package className="w-4 h-4 text-eucora-teal flex-shrink-0" />
          <div className="flex items-center gap-2 flex-1 min-w-0">
            <span className="truncate text-foreground">{app.app_name}</span>
            <Badge variant="outline" className="text-[10px] h-5 flex-shrink-0">
              {app.deployment_count}
            </Badge>
          </div>
        </div>
      </CollapsibleTrigger>
      {isOpen && (
        <CollapsibleContent className="pl-6 space-y-0.5 mt-1 border-l border-white/10">
          {app.versions.map((version) => (
            <VersionEntry
              key={version.version}
              version={version}
            />
          ))}
        </CollapsibleContent>
      )}
    </Collapsible>
  );
}

/**
 * Sidebar component displaying all applications with versions and deployments.
 * Tree structure: App → Version → Deployment with inline filtering.
 */
export default function DeploymentsSidebar() {
  const [searchTerm, setSearchTerm] = useState('');
  const { data: applications, isLoading } = useSidebarApplications(
    searchTerm ? { app_name: searchTerm } : undefined
  );

  const filteredApps = useMemo(() => {
    if (!applications) return [];
    if (!searchTerm) return applications;

    // Additional client-side filtering (though server already filters)
    return applications.filter((app: SidebarApplicationGroup) =>
      app.app_name.toLowerCase().includes(searchTerm.toLowerCase())
    );
  }, [applications, searchTerm]);

  return (
    <div className="h-full flex flex-col">
      <Card className="glass flex-none">
        <CardHeader className="pb-3">
          <CardTitle className="text-lg">Applications</CardTitle>
          <CardDescription>
            Deployments by application and version
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <Search className="absolute left-2 top-1/2 -translate-y-1/2 w-4 h-4 text-muted-foreground" />
            <Input
              placeholder="Search applications..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-8 bg-background/50"
              aria-label="Search applications"
            />
          </div>
        </CardContent>
      </Card>

      {/* Application list */}
      <div className="flex-1 overflow-y-auto mt-4 pr-2">
        {isLoading ? (
          <SkeletonList items={5} />
        ) : filteredApps.length === 0 ? (
          <EmptyState
            icon={Package}
            title="No applications found"
            description={
              searchTerm
                ? 'No applications match your search'
                : 'Create a deployment to see applications here'
            }
          />
        ) : (
          <div className="space-y-1">
            {filteredApps.map((app) => (
              <ApplicationEntry key={app.app_name} app={app} />
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
