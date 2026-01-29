// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * License Dashboard - P8 D8.6.
 *
 * Comprehensive license management dashboard with:
 * - KPI summary cards (Entitled, Consumed, Remaining, Alerts)
 * - Consumption trend chart
 * - SKU utilization table
 * - Active alerts list
 * - Evidence pack access
 * - Reconciliation status
 */
import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Progress } from '@/components/ui/progress';
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from '@/components/ui/tooltip';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
} from 'recharts';
import {
  AlertTriangle,
  CheckCircle,
  Clock,
  Download,
  FileKey,
  Loader2,
  RefreshCcw,
  XCircle,
  Package,
  TrendingUp,
} from 'lucide-react';
import { cn } from '@/lib/utils';
import {
  useLicenseSummary,
  useSKUs,
  useLicenseAlerts,
  useReconciliationStatus,
  useTriggerReconciliation,
  useAcknowledgeAlert,
} from '@/lib/api/hooks/useLicenses';
import {
  AlertSeverity,
  AlertType,
  HealthStatus,
  LicenseModelType,
  LicenseSKUListItem,
  LicenseAlert,
} from './contracts';

// ============================================================================
// TYPES
// ============================================================================

interface ConsumptionTrendData {
  date: string;
  entitled: number;
  consumed: number;
}

// ============================================================================
// CONSTANTS
// ============================================================================

const healthStatusConfig: Record<HealthStatus, {
  icon: typeof CheckCircle;
  color: string;
  bgColor: string;
  borderColor: string;
  label: string;
}> = {
  ok: {
    icon: CheckCircle,
    color: 'text-eucora-green',
    bgColor: 'bg-eucora-green/10',
    borderColor: 'border-l-eucora-green',
    label: 'Healthy',
  },
  degraded: {
    icon: AlertTriangle,
    color: 'text-eucora-gold',
    bgColor: 'bg-eucora-gold/10',
    borderColor: 'border-l-eucora-gold',
    label: 'Degraded',
  },
  failed: {
    icon: XCircle,
    color: 'text-red-500',
    bgColor: 'bg-red-500/10',
    borderColor: 'border-l-red-500',
    label: 'Failed',
  },
  stale: {
    icon: Clock,
    color: 'text-orange-400',
    bgColor: 'bg-orange-400/10',
    borderColor: 'border-l-orange-400',
    label: 'Stale Data',
  },
};

const alertSeverityConfig: Record<AlertSeverity, {
  color: string;
  bgColor: string;
  label: string;
}> = {
  info: { color: 'text-eucora-teal', bgColor: 'bg-eucora-teal/10', label: 'Info' },
  warning: { color: 'text-eucora-gold', bgColor: 'bg-eucora-gold/10', label: 'Warning' },
  critical: { color: 'text-red-500', bgColor: 'bg-red-500/10', label: 'Critical' },
};

const alertTypeLabels: Record<AlertType, string> = {
  overconsumption: 'Overconsumption',
  expiring: 'Expiring Soon',
  spike: 'Usage Spike',
  underutilized: 'Underutilized',
  reconciliation_failed: 'Reconciliation Failed',
  stale_data: 'Stale Data',
};

const licenseModelLabels: Record<LicenseModelType, string> = {
  device: 'Device',
  user: 'User',
  concurrent: 'Concurrent',
  subscription: 'Subscription',
  feature: 'Feature',
  core: 'Core',
  instance: 'Instance',
};

// Mock trend data - in production this would come from an API
function generateMockTrendData(): ConsumptionTrendData[] {
  const data: ConsumptionTrendData[] = [];
  const now = new Date();
  for (let i = 29; i >= 0; i--) {
    const date = new Date(now);
    date.setDate(date.getDate() - i);
    data.push({
      date: date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }),
      entitled: 10000,
      consumed: 7500 + Math.floor(Math.random() * 500),
    });
  }
  return data;
}

// ============================================================================
// HELPER FUNCTIONS
// ============================================================================

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

function calculateUtilization(consumed: number, entitled: number): number {
  if (entitled === 0) return 0;
  return Math.round((consumed / entitled) * 100);
}

function getUtilizationColor(utilization: number): string {
  if (utilization >= 95) return 'text-red-500';
  if (utilization >= 80) return 'text-eucora-gold';
  return 'text-eucora-green';
}

// ============================================================================
// COMPONENTS
// ============================================================================

interface KPICardProps {
  title: string;
  value: number | string;
  icon: React.ReactNode;
  borderColor: string;
  isLoading?: boolean;
  subtitle?: string;
  trend?: { value: number; isPositive: boolean };
}

function KPICard({ title, value, icon, borderColor, isLoading, subtitle, trend }: KPICardProps) {
  return (
    <Card className={cn('glass border-l-4', borderColor)}>
      <CardHeader className="py-4">
        <div className="flex items-center justify-between">
          <CardTitle className="text-xs font-medium uppercase text-muted-foreground">
            {title}
          </CardTitle>
          <div className="text-muted-foreground">{icon}</div>
        </div>
        {isLoading ? (
          <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
        ) : (
          <div className="flex items-baseline gap-2">
            <div className="text-2xl font-bold">
              {typeof value === 'number' ? value.toLocaleString() : value}
            </div>
            {trend && (
              <span className={cn(
                'text-xs font-medium',
                trend.isPositive ? 'text-eucora-green' : 'text-red-500'
              )}>
                {trend.isPositive ? '+' : ''}{trend.value}%
              </span>
            )}
          </div>
        )}
        {subtitle && (
          <p className="text-xs text-muted-foreground">{subtitle}</p>
        )}
      </CardHeader>
    </Card>
  );
}

interface SKUTableProps {
  skus: LicenseSKUListItem[];
  isLoading: boolean;
}

function SKUTable({ skus, isLoading }: SKUTableProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-48">
        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (skus.length === 0) {
    return (
      <div className="flex items-center justify-center h-48 text-muted-foreground">
        No SKUs found
      </div>
    );
  }

  return (
    <Table>
      <TableHeader>
        <TableRow>
          <TableHead>SKU</TableHead>
          <TableHead>Vendor</TableHead>
          <TableHead>Model</TableHead>
          <TableHead className="text-right">Entitled</TableHead>
          <TableHead className="text-right">Consumed</TableHead>
          <TableHead className="text-right">Remaining</TableHead>
          <TableHead>Utilization</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {skus.map((sku) => {
          const utilization = calculateUtilization(sku.consumed, sku.entitled);
          return (
            <TableRow key={sku.id}>
              <TableCell>
                <div className="flex flex-col">
                  <span className="font-medium">{sku.name}</span>
                  <span className="text-xs text-muted-foreground">{sku.sku_code}</span>
                </div>
              </TableCell>
              <TableCell>{sku.vendor_name}</TableCell>
              <TableCell>
                <Badge variant="outline" className="text-xs">
                  {licenseModelLabels[sku.license_model_type]}
                </Badge>
              </TableCell>
              <TableCell className="text-right font-mono">
                {sku.entitled.toLocaleString()}
              </TableCell>
              <TableCell className="text-right font-mono">
                {sku.consumed.toLocaleString()}
              </TableCell>
              <TableCell className={cn('text-right font-mono', {
                'text-eucora-green': sku.remaining > 0,
                'text-red-500': sku.remaining <= 0,
              })}>
                {sku.remaining.toLocaleString()}
              </TableCell>
              <TableCell>
                <div className="flex items-center gap-2">
                  <Progress
                    value={Math.min(utilization, 100)}
                    className="h-2 w-16"
                  />
                  <span className={cn('text-sm font-medium', getUtilizationColor(utilization))}>
                    {utilization}%
                  </span>
                </div>
              </TableCell>
            </TableRow>
          );
        })}
      </TableBody>
    </Table>
  );
}

interface AlertsListProps {
  alerts: LicenseAlert[];
  isLoading: boolean;
  onAcknowledge: (id: string) => void;
  isAcknowledging: boolean;
}

function AlertsList({ alerts, isLoading, onAcknowledge, isAcknowledging }: AlertsListProps) {
  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-32">
        <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
      </div>
    );
  }

  if (alerts.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center h-32 text-muted-foreground">
        <CheckCircle className="h-8 w-8 mb-2 text-eucora-green" />
        <span>No active alerts</span>
      </div>
    );
  }

  return (
    <div className="space-y-3">
      {alerts.slice(0, 5).map((alert) => {
        const severityConfig = alertSeverityConfig[alert.severity];
        return (
          <div
            key={alert.id}
            className={cn(
              'p-3 rounded-lg border flex items-start justify-between gap-3',
              severityConfig.bgColor
            )}
          >
            <div className="flex-1 min-w-0">
              <div className="flex items-center gap-2 mb-1">
                <Badge variant="outline" className={cn('text-xs', severityConfig.color)}>
                  {severityConfig.label}
                </Badge>
                <Badge variant="outline" className="text-xs">
                  {alertTypeLabels[alert.alert_type]}
                </Badge>
              </div>
              <p className="text-sm font-medium truncate">{alert.message}</p>
              <p className="text-xs text-muted-foreground">
                {alert.sku_name} • {formatRelativeTime(alert.detected_at)}
              </p>
            </div>
            <TooltipProvider>
              <Tooltip>
                <TooltipTrigger asChild>
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => onAcknowledge(alert.id)}
                    disabled={isAcknowledging}
                  >
                    {isAcknowledging ? (
                      <Loader2 className="h-4 w-4 animate-spin" />
                    ) : (
                      <CheckCircle className="h-4 w-4" />
                    )}
                  </Button>
                </TooltipTrigger>
                <TooltipContent>Acknowledge alert</TooltipContent>
              </Tooltip>
            </TooltipProvider>
          </div>
        );
      })}
    </div>
  );
}

// ============================================================================
// MAIN COMPONENT
// ============================================================================

export default function LicenseDashboard() {
  const [timeRange, setTimeRange] = useState('30d');
  const [vendorFilter, setVendorFilter] = useState<string | undefined>();

  // Data hooks
  const { data: summary, isLoading: summaryLoading } = useLicenseSummary();
  const { data: skus, isLoading: skusLoading } = useSKUs({ vendor: vendorFilter, is_active: true });
  const { data: alertsResponse, isLoading: alertsLoading } = useLicenseAlerts({ acknowledged: false });
  const { data: reconciliationStatus, isLoading: reconciliationLoading } = useReconciliationStatus();

  // Mutations
  const triggerReconciliation = useTriggerReconciliation();
  const acknowledgeAlert = useAcknowledgeAlert();

  // Derived data
  const alerts = alertsResponse?.results || [];
  const trendData = generateMockTrendData();
  const healthConfig = healthStatusConfig[summary?.health_status || 'ok'];
  const HealthIcon = healthConfig.icon;

  // Handlers
  const handleTriggerReconciliation = () => {
    triggerReconciliation.mutate();
  };

  const handleAcknowledgeAlert = (id: string) => {
    acknowledgeAlert.mutate({ id });
  };

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-3xl font-bold tracking-tight">License Management</h2>
          <p className="text-muted-foreground">
            Monitor license consumption, utilization, and compliance status.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Select value={timeRange} onValueChange={setTimeRange}>
            <SelectTrigger className="w-[140px]">
              <SelectValue placeholder="Time range" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="7d">Last 7 Days</SelectItem>
              <SelectItem value="30d">Last 30 Days</SelectItem>
              <SelectItem value="90d">Last 90 Days</SelectItem>
            </SelectContent>
          </Select>
          <TooltipProvider>
            <Tooltip>
              <TooltipTrigger asChild>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleTriggerReconciliation}
                  disabled={triggerReconciliation.isPending}
                >
                  {triggerReconciliation.isPending ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <RefreshCcw className="h-4 w-4" />
                  )}
                  <span className="ml-2">Reconcile</span>
                </Button>
              </TooltipTrigger>
              <TooltipContent>Trigger license reconciliation</TooltipContent>
            </Tooltip>
          </TooltipProvider>
          <Button variant="outline" size="sm">
            <Download className="h-4 w-4 mr-2" />
            Export Report
          </Button>
        </div>
      </div>

      {/* Health Status Banner */}
      {summary && summary.health_status !== 'ok' && (
        <Card className={cn('border-l-4', healthConfig.borderColor, healthConfig.bgColor)}>
          <CardContent className="py-4">
            <div className="flex items-center gap-3">
              <HealthIcon className={cn('h-5 w-5', healthConfig.color)} />
              <div>
                <p className={cn('font-medium', healthConfig.color)}>
                  {healthConfig.label}: {summary.health_message || 'System health issue detected'}
                </p>
                {summary.last_reconciled_at && (
                  <p className="text-xs text-muted-foreground">
                    Last reconciled: {formatRelativeTime(summary.last_reconciled_at)}
                  </p>
                )}
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* KPI Cards */}
      <div className="grid gap-4 md:grid-cols-4">
        <KPICard
          title="Total Entitled"
          value={summary?.total_entitled || 0}
          icon={<FileKey className="h-4 w-4" />}
          borderColor="border-l-eucora-deepBlue"
          isLoading={summaryLoading}
          subtitle={`${summary?.vendor_count || 0} vendors · ${summary?.sku_count || 0} SKUs`}
        />
        <KPICard
          title="Consumed"
          value={summary?.total_consumed || 0}
          icon={<Package className="h-4 w-4" />}
          borderColor="border-l-eucora-teal"
          isLoading={summaryLoading}
        />
        <KPICard
          title="Remaining"
          value={summary?.total_remaining || 0}
          icon={<TrendingUp className="h-4 w-4" />}
          borderColor={(summary?.total_remaining || 0) > 0 ? 'border-l-eucora-green' : 'border-l-red-500'}
          isLoading={summaryLoading}
        />
        <KPICard
          title="Active Alerts"
          value={summary?.active_alerts_count || 0}
          icon={<AlertTriangle className="h-4 w-4" />}
          borderColor={(summary?.active_alerts_count || 0) > 0 ? 'border-l-eucora-gold' : 'border-l-eucora-green'}
          isLoading={summaryLoading}
        />
      </div>

      {/* Charts Row */}
      <div className="grid gap-6 md:grid-cols-2">
        {/* Consumption Trend */}
        <Card className="glass col-span-2 lg:col-span-1">
          <CardHeader>
            <CardTitle>Consumption Trend</CardTitle>
            <CardDescription>License consumption vs entitlements over time</CardDescription>
          </CardHeader>
          <CardContent>
            <div className="h-[300px] w-full min-w-0">
              {summaryLoading ? (
                <div className="flex items-center justify-center h-full">
                  <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                </div>
              ) : (
                <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                  <AreaChart data={trendData}>
                    <defs>
                      <linearGradient id="colorEntitled" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#1E3A5F" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#1E3A5F" stopOpacity={0} />
                      </linearGradient>
                      <linearGradient id="colorConsumed" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#2DD4BF" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#2DD4BF" stopOpacity={0} />
                      </linearGradient>
                    </defs>
                    <XAxis
                      dataKey="date"
                      stroke="#888888"
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                    />
                    <YAxis
                      stroke="#888888"
                      fontSize={12}
                      tickLine={false}
                      axisLine={false}
                      tickFormatter={(value) => `${(value / 1000).toFixed(0)}k`}
                    />
                    <RechartsTooltip
                      contentStyle={{
                        backgroundColor: 'hsl(var(--card))',
                        borderRadius: '8px',
                        border: '1px solid hsl(var(--border))',
                      }}
                    />
                    <Area
                      type="monotone"
                      dataKey="entitled"
                      stroke="#1E3A5F"
                      fillOpacity={1}
                      fill="url(#colorEntitled)"
                      name="Entitled"
                    />
                    <Area
                      type="monotone"
                      dataKey="consumed"
                      stroke="#2DD4BF"
                      fillOpacity={1}
                      fill="url(#colorConsumed)"
                      name="Consumed"
                    />
                  </AreaChart>
                </ResponsiveContainer>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Active Alerts */}
        <Card className="glass col-span-2 lg:col-span-1">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle>Active Alerts</CardTitle>
                <CardDescription>Unacknowledged license alerts</CardDescription>
              </div>
              {alerts.length > 0 && (
                <Badge variant="destructive" className="font-mono">
                  {alerts.length}
                </Badge>
              )}
            </div>
          </CardHeader>
          <CardContent>
            <AlertsList
              alerts={alerts}
              isLoading={alertsLoading}
              onAcknowledge={handleAcknowledgeAlert}
              isAcknowledging={acknowledgeAlert.isPending}
            />
          </CardContent>
        </Card>
      </div>

      {/* SKU Utilization Table */}
      <Card className="glass">
        <CardHeader>
          <div className="flex items-center justify-between">
            <div>
              <CardTitle>SKU Utilization</CardTitle>
              <CardDescription>License consumption by SKU</CardDescription>
            </div>
            <div className="flex items-center gap-2">
              <Select value={vendorFilter || 'all'} onValueChange={(v) => setVendorFilter(v === 'all' ? undefined : v)}>
                <SelectTrigger className="w-[180px]">
                  <SelectValue placeholder="All vendors" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem value="all">All Vendors</SelectItem>
                  {/* Vendors would be loaded dynamically */}
                </SelectContent>
              </Select>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <SKUTable skus={skus || []} isLoading={skusLoading} />
        </CardContent>
      </Card>

      {/* Reconciliation Status */}
      <Card className="glass">
        <CardHeader>
          <CardTitle>Reconciliation Status</CardTitle>
          <CardDescription>Last reconciliation run details</CardDescription>
        </CardHeader>
        <CardContent>
          {reconciliationLoading ? (
            <div className="flex items-center justify-center h-24">
              <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
            </div>
          ) : reconciliationStatus && 'status' in reconciliationStatus && reconciliationStatus.status !== 'no_runs' ? (
            <div className="grid gap-4 md:grid-cols-4">
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase">Status</p>
                <Badge variant={reconciliationStatus.status === 'completed' ? 'default' : 'destructive'}>
                  {reconciliationStatus.status}
                </Badge>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase">Started</p>
                <p className="text-sm font-medium">
                  {formatRelativeTime(reconciliationStatus.started_at)}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase">SKUs Processed</p>
                <p className="text-sm font-medium">
                  {reconciliationStatus.skus_processed} / {reconciliationStatus.skus_total}
                </p>
              </div>
              <div className="space-y-1">
                <p className="text-xs text-muted-foreground uppercase">Snapshots Created</p>
                <p className="text-sm font-medium">{reconciliationStatus.snapshots_created}</p>
              </div>
            </div>
          ) : (
            <div className="flex flex-col items-center justify-center h-24 text-muted-foreground">
              <Clock className="h-6 w-6 mb-2" />
              <span>No reconciliation runs yet</span>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
