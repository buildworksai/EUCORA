// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * License Summary Sidebar Widget.
 *
 * Displays license health status in the sidebar:
 * - Consumed/Entitled/Remaining quantities
 * - Health indicator (OK/Degraded/Failed/Stale)
 * - Stale data warning when > 2x schedule interval
 * - Polling from ConsumptionSnapshot API via useLicenseSummary hook
 *
 * Implements D8.5 from MASTER-IMPLEMENTATION-PLAN-2026.md.
 */
import { cn } from '@/lib/utils';
import { useLicenseSummary } from '@/lib/api/hooks/useLicenses';
import { HealthStatus } from '@/routes/licenses/contracts';
import { AlertTriangle, CheckCircle, Clock, FileKey, XCircle, AlertOctagon } from 'lucide-react';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';

// ============================================================================
// TYPES
// ============================================================================

interface LicenseSummaryWidgetProps {
  /** Additional CSS classes */
  className?: string;
  /** Compact mode for narrow sidebars */
  compact?: boolean;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const STALE_THRESHOLD_SECONDS = 2 * 60 * 60; // 2 hours (2x typical 1hr reconciliation interval)

const healthStatusConfig: Record<HealthStatus, {
  icon: typeof CheckCircle;
  color: string;
  bgColor: string;
  label: string;
}> = {
  ok: {
    icon: CheckCircle,
    color: 'text-eucora-green',
    bgColor: 'bg-eucora-green',
    label: 'Healthy',
  },
  degraded: {
    icon: AlertTriangle,
    color: 'text-eucora-gold',
    bgColor: 'bg-eucora-gold',
    label: 'Degraded',
  },
  failed: {
    icon: XCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500',
    label: 'Failed',
  },
  stale: {
    icon: Clock,
    color: 'text-orange-400',
    bgColor: 'bg-orange-400',
    label: 'Stale Data',
  },
};

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

/**
 * Format seconds into human-readable duration.
 */
function formatDuration(seconds: number): string {
  if (seconds < 60) {
    return `${seconds}s`;
  }
  if (seconds < 3600) {
    const mins = Math.floor(seconds / 60);
    return `${mins}m`;
  }
  const hours = Math.floor(seconds / 3600);
  const mins = Math.floor((seconds % 3600) / 60);
  if (mins === 0) {
    return `${hours}h`;
  }
  return `${hours}h ${mins}m`;
}

/**
 * Format relative time from ISO string.
 */
function formatRelativeTime(isoString: string | null): string {
  if (!isoString) {
    return 'Never';
  }

  const date = new Date(isoString);
  const now = new Date();
  const diffMs = now.getTime() - date.getTime();
  const diffSeconds = Math.floor(diffMs / 1000);

  if (diffSeconds < 60) {
    return 'Just now';
  }
  if (diffSeconds < 3600) {
    const mins = Math.floor(diffSeconds / 60);
    return `${mins}m ago`;
  }
  if (diffSeconds < 86400) {
    const hours = Math.floor(diffSeconds / 3600);
    return `${hours}h ago`;
  }
  const days = Math.floor(diffSeconds / 86400);
  return `${days}d ago`;
}

/**
 * Calculate utilization percentage.
 */
function calculateUtilization(consumed: number, entitled: number): number {
  if (entitled === 0) return 0;
  return Math.round((consumed / entitled) * 100);
}

// ============================================================================
// COMPONENT
// ============================================================================

/**
 * License Summary Widget for sidebar display.
 *
 * Shows license position (Consumed/Entitled/Remaining) with health status indicator.
 * Includes stale data warning when reconciliation is overdue.
 */
export function LicenseSummaryWidget({ className, compact = false }: LicenseSummaryWidgetProps) {
  const { data, isLoading, error } = useLicenseSummary();

  // Loading state
  if (isLoading) {
    return (
      <div className={cn('p-4 rounded-xl bg-white/5 border border-white/5 animate-pulse', className)}>
        <div className="flex items-center justify-between mb-3">
          <div className="h-3 w-16 bg-white/10 rounded" />
          <div className="h-2 w-2 rounded-full bg-white/10" />
        </div>
        <div className="space-y-2">
          <div className="h-3 w-24 bg-white/10 rounded" />
          <div className="h-3 w-20 bg-white/10 rounded" />
        </div>
      </div>
    );
  }

  // Error state
  if (error || !data) {
    return (
      <div className={cn('p-4 rounded-xl bg-white/5 border border-red-500/30', className)}>
        <div className="flex items-center gap-2 text-red-400">
          <AlertOctagon className="w-4 h-4" />
          <span className="text-xs font-medium">License data unavailable</span>
        </div>
      </div>
    );
  }

  const statusConfig = healthStatusConfig[data.health_status] || healthStatusConfig.ok;
  const StatusIcon = statusConfig.icon;
  const utilization = calculateUtilization(data.total_consumed, data.total_entitled);
  const isStale = data.stale_duration_seconds !== null && data.stale_duration_seconds > STALE_THRESHOLD_SECONDS;

  // Compact mode (icon + indicator only)
  if (compact) {
    return (
      <TooltipProvider>
        <Tooltip>
          <TooltipTrigger asChild>
            <div className={cn('p-3 rounded-lg bg-white/5 cursor-help', className)}>
              <div className="flex items-center justify-between">
                <FileKey className="w-4 h-4 text-muted-foreground" />
                <span className={cn('h-2 w-2 rounded-full', statusConfig.bgColor, {
                  'animate-pulse': data.health_status !== 'ok',
                })} />
              </div>
            </div>
          </TooltipTrigger>
          <TooltipContent side="right" className="p-3">
            <div className="space-y-2 text-xs">
              <div className="flex items-center gap-2">
                <StatusIcon className={cn('w-4 h-4', statusConfig.color)} />
                <span className="font-medium">{statusConfig.label}</span>
              </div>
              <div className="text-muted-foreground">
                {data.total_consumed.toLocaleString()} / {data.total_entitled.toLocaleString()} licenses
              </div>
              {data.active_alerts_count > 0 && (
                <div className="text-eucora-gold">
                  {data.active_alerts_count} active alert{data.active_alerts_count !== 1 ? 's' : ''}
                </div>
              )}
            </div>
          </TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );
  }

  // Full mode
  return (
    <div className={cn('p-4 rounded-xl bg-white/5 border border-white/5', className)}>
      {/* Header */}
      <div className="flex items-center justify-between mb-3">
        <div className="flex items-center gap-2">
          <FileKey className="w-4 h-4 text-muted-foreground" />
          <span className="text-xs font-semibold text-muted-foreground uppercase tracking-wide">
            Licenses
          </span>
        </div>
        <TooltipProvider>
          <Tooltip>
            <TooltipTrigger asChild>
              <span className={cn(
                'h-2 w-2 rounded-full cursor-help transition-all',
                statusConfig.bgColor,
                { 'animate-pulse': data.health_status !== 'ok' }
              )} />
            </TooltipTrigger>
            <TooltipContent side="left">
              <div className="flex items-center gap-2 text-xs">
                <StatusIcon className={cn('w-3 h-3', statusConfig.color)} />
                <span>{statusConfig.label}</span>
              </div>
              {data.health_message && (
                <div className="text-xs text-muted-foreground mt-1">{data.health_message}</div>
              )}
            </TooltipContent>
          </Tooltip>
        </TooltipProvider>
      </div>

      {/* Utilization bar */}
      <div className="mb-3">
        <div className="flex justify-between text-xs mb-1">
          <span className="text-muted-foreground">Utilization</span>
          <span className={cn('font-medium', {
            'text-eucora-green': utilization < 80,
            'text-eucora-gold': utilization >= 80 && utilization < 95,
            'text-red-500': utilization >= 95,
          })}>
            {utilization}%
          </span>
        </div>
        <div className="h-1.5 bg-white/10 rounded-full overflow-hidden">
          <div
            className={cn('h-full rounded-full transition-all duration-500', {
              'bg-eucora-green': utilization < 80,
              'bg-eucora-gold': utilization >= 80 && utilization < 95,
              'bg-red-500': utilization >= 95,
            })}
            style={{ width: `${Math.min(utilization, 100)}%` }}
          />
        </div>
      </div>

      {/* Quantities */}
      <div className="space-y-1 text-xs text-muted-foreground">
        <div className="flex justify-between">
          <span>Consumed</span>
          <span className="font-medium text-foreground">{data.total_consumed.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span>Entitled</span>
          <span className="font-medium text-foreground">{data.total_entitled.toLocaleString()}</span>
        </div>
        <div className="flex justify-between">
          <span>Remaining</span>
          <span className={cn('font-medium', {
            'text-eucora-green': data.total_remaining > 0,
            'text-red-500': data.total_remaining <= 0,
          })}>
            {data.total_remaining.toLocaleString()}
          </span>
        </div>
      </div>

      {/* Stale data warning */}
      {isStale && data.stale_duration_seconds && (
        <div className="mt-3 p-2 rounded-lg bg-orange-500/10 border border-orange-500/30">
          <div className="flex items-center gap-2 text-orange-400">
            <Clock className="w-3 h-3" />
            <span className="text-xs font-medium">
              Data stale ({formatDuration(data.stale_duration_seconds)})
            </span>
          </div>
        </div>
      )}

      {/* Active alerts */}
      {data.active_alerts_count > 0 && (
        <div className="mt-3 p-2 rounded-lg bg-eucora-gold/10 border border-eucora-gold/30">
          <div className="flex items-center gap-2 text-eucora-gold">
            <AlertTriangle className="w-3 h-3" />
            <span className="text-xs font-medium">
              {data.active_alerts_count} active alert{data.active_alerts_count !== 1 ? 's' : ''}
            </span>
          </div>
        </div>
      )}

      {/* Footer */}
      <div className="mt-3 pt-2 border-t border-white/5">
        <div className="flex justify-between text-[10px] text-muted-foreground/70">
          <span>{data.vendor_count} vendors · {data.sku_count} SKUs</span>
          <span>Synced {formatRelativeTime(data.last_reconciled_at)}</span>
        </div>
      </div>
    </div>
  );
}

export default LicenseSummaryWidget;
