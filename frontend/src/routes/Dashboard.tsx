import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { RingProgressIndicator, Ring } from '@/components/deployment/RingProgressIndicator';
import { RiskScoreBadge } from '@/components/deployment/RiskScoreBadge';
import { SkeletonCard, SkeletonList } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Activity, Box, ShieldCheck, CheckCircle2, AlertCircle } from 'lucide-react';
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { Button } from '@/components/ui/button';
import { useNavigate } from 'react-router-dom';
import { useDeployments } from '@/lib/api/hooks/useDeployments';
import { usePendingApprovals } from '@/lib/api/hooks/useCAB';
import { useHealth } from '@/lib/api/hooks/useHealth';
import { useMemo } from 'react';

export default function Dashboard() {
    const navigate = useNavigate();
    const { data: deployments = [], isLoading: deploymentsLoading, error: deploymentsError } = useDeployments();
    const { data: pendingApprovals = [], isLoading: approvalsLoading } = usePendingApprovals();
    const { data: health } = useHealth();

    // Calculate summary stats
    const stats = useMemo(() => {
        const total = deployments.length;
        const inProgress = deployments.filter(d => d.status === 'DEPLOYING').length;
        const completed = deployments.filter(d => d.status === 'COMPLETED').length;
        const failed = deployments.filter(d => d.status === 'FAILED' || d.status === 'ROLLED_BACK').length;
        const awaitingCAB = deployments.filter(d => d.status === 'AWAITING_CAB').length;

        return { total, inProgress, completed, failed, awaitingCAB };
    }, [deployments]);

    // Calculate ring progress for active deployments
    const activeDeployment = useMemo(() => {
        return deployments.find(d => d.status === 'DEPLOYING' || d.status === 'APPROVED');
    }, [deployments]);

    // Chart data for rollout velocity
    const chartData = useMemo(() => {
        const rings = ['LAB', 'CANARY', 'PILOT', 'DEPARTMENT', 'GLOBAL'];
        return rings.map(ring => {
            const ringDeployments = deployments.filter(d => d.target_ring === ring);
            const success = ringDeployments.filter(d => d.status === 'COMPLETED').length;
            const pending = ringDeployments.filter(d => 
                d.status === 'DEPLOYING' || d.status === 'APPROVED' || d.status === 'AWAITING_CAB'
            ).length;
            return {
                name: ring,
                success: ringDeployments.length > 0 ? (success / ringDeployments.length) * 100 : 0,
                pending: ringDeployments.length > 0 ? (pending / ringDeployments.length) * 100 : 0,
            };
        });
    }, [deployments]);

    // Ring status for active deployment
    const ringsStatus: Ring[] = useMemo(() => {
        if (!activeDeployment) {
            return [
                { name: 'Lab', status: 'pending' },
                { name: 'Canary', status: 'pending' },
                { name: 'Pilot', status: 'pending' },
                { name: 'Department', status: 'pending' },
                { name: 'Global', status: 'pending' },
            ];
        }

        const ringOrder = ['LAB', 'CANARY', 'PILOT', 'DEPARTMENT', 'GLOBAL'];
        const currentRingIndex = ringOrder.indexOf(activeDeployment.target_ring);

        return ringOrder.map((ring, index) => {
            if (index < currentRingIndex) {
                return { name: ring.charAt(0) + ring.slice(1).toLowerCase(), status: 'completed' as const, successRate: 100 };
            } else if (index === currentRingIndex) {
                return { name: ring.charAt(0) + ring.slice(1).toLowerCase(), status: 'in_progress' as const };
            } else {
                return { name: ring.charAt(0) + ring.slice(1).toLowerCase(), status: 'pending' as const };
            }
        });
    }, [activeDeployment]);

    if (deploymentsError) {
        return (
            <div className="space-y-6">
                <EmptyState
                    icon={AlertCircle}
                    title="Failed to load deployments"
                    description={deploymentsError instanceof Error ? deploymentsError.message : 'Unknown error occurred'}
                />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Dashboard</h2>
                    <p className="text-muted-foreground">Real-time deployment status across all rings</p>
                </div>
                <Button onClick={() => navigate('/deploy')} className="bg-eucora-deepBlue hover:bg-eucora-deepBlue-dark text-white">
                    New Deployment
                </Button>
            </div>

            {/* Stats Cards */}
            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {deploymentsLoading ? (
                    Array.from({ length: 4 }).map((_, i) => <SkeletonCard key={i} />)
                ) : (
                    <>
                        <Card className="glass">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Active Deployments</CardTitle>
                                <Activity className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{stats.total}</div>
                                <p className="text-xs text-muted-foreground">
                                    {stats.inProgress > 0 ? `+${stats.inProgress} in progress` : 'All stable'}
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="glass">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Pending Approvals</CardTitle>
                                <ShieldCheck className="h-4 w-4 text-eucora-gold" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{pendingApprovals.length}</div>
                                <p className="text-xs text-muted-foreground">
                                    {approvalsLoading ? 'Loading...' : 'High risk changes'}
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="glass">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">Completed</CardTitle>
                                <CheckCircle2 className="h-4 w-4 text-eucora-green" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">{stats.completed}</div>
                                <p className="text-xs text-muted-foreground">
                                    {stats.total > 0 ? `${Math.round((stats.completed / stats.total) * 100)}% success rate` : 'No deployments'}
                                </p>
                            </CardContent>
                        </Card>
                        <Card className="glass">
                            <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                                <CardTitle className="text-sm font-medium">System Health</CardTitle>
                                <Box className="h-4 w-4 text-muted-foreground" />
                            </CardHeader>
                            <CardContent>
                                <div className="text-2xl font-bold">
                                    {health?.status === 'healthy' ? '✓' : '⚠'}
                                </div>
                                <p className="text-xs text-muted-foreground">
                                    {health?.status === 'healthy' ? 'All systems operational' : 'Degraded'}
                                </p>
                            </CardContent>
                        </Card>
                    </>
                )}
            </div>

            <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-7">
                {/* Main Chart */}
                <Card className="col-span-4 glass">
                    <CardHeader>
                        <CardTitle>Rollout Velocity</CardTitle>
                        <CardDescription>Deployment completion across rings</CardDescription>
                    </CardHeader>
                    <CardContent className="pl-2">
                        {deploymentsLoading ? (
                            <div className="h-[300px] flex items-center justify-center">
                                <SkeletonCard />
                            </div>
                        ) : chartData.length > 0 ? (
                            <ResponsiveContainer width="100%" height={300}>
                                <BarChart data={chartData}>
                                    <XAxis dataKey="name" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} tickFormatter={(value) => `${value}%`} />
                                    <Tooltip
                                        contentStyle={{ backgroundColor: 'hsl(var(--card))', borderColor: 'hsl(var(--border))', borderRadius: '8px' }}
                                        itemStyle={{ color: 'hsl(var(--foreground))' }}
                                    />
                                    <Bar dataKey="success" fill="hsl(var(--primary))" radius={[4, 4, 0, 0]} stackId="a" />
                                    <Bar dataKey="pending" fill="hsl(var(--muted))" radius={[4, 4, 0, 0]} stackId="a" />
                                </BarChart>
                            </ResponsiveContainer>
                        ) : (
                            <EmptyState
                                title="No deployment data"
                                description="Deployments will appear here once created"
                            />
                        )}
                    </CardContent>
                </Card>

                {/* Recent Activity */}
                <Card className="col-span-3 glass">
                    <CardHeader>
                        <CardTitle>Recent Deployments</CardTitle>
                        <CardDescription>Latest packaging and rollout events</CardDescription>
                    </CardHeader>
                    <CardContent>
                        {deploymentsLoading ? (
                            <SkeletonList items={5} />
                        ) : deployments.length > 0 ? (
                            <div className="space-y-4">
                                {deployments.slice(0, 5).map((deployment) => (
                                    <div key={deployment.correlation_id} className="flex items-center justify-between border-b pb-2 last:border-0 last:pb-0">
                                        <div className="flex flex-col gap-1">
                                            <span className="font-medium text-sm">{deployment.app_name}</span>
                                            <span className="text-xs text-muted-foreground">v{deployment.version}</span>
                                        </div>
                                        <div className="flex flex-col items-end gap-1">
                                            {deployment.risk_score !== null && <RiskScoreBadge score={deployment.risk_score} />}
                                            <span className="text-xs text-muted-foreground uppercase">{deployment.target_ring}</span>
                                        </div>
                                    </div>
                                ))}
                            </div>
                        ) : (
                            <EmptyState
                                title="No deployments"
                                description="Create your first deployment to get started"
                                action={{
                                    label: 'New Deployment',
                                    onClick: () => navigate('/deploy'),
                                }}
                            />
                        )}
                    </CardContent>
                </Card>
            </div>

            {/* Active Ring Visualizer */}
            {activeDeployment && (
                <Card className="glass">
                    <CardHeader>
                        <CardTitle>Live Deployment: {activeDeployment.app_name} (v{activeDeployment.version})</CardTitle>
                        <CardDescription>Currently progressing through {activeDeployment.target_ring} Ring</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <RingProgressIndicator rings={ringsStatus} />
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
