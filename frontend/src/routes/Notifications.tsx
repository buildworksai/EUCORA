// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Separator } from '@/components/ui/separator';
import { Bell, Clock, CheckCircle2, AlertCircle, ExternalLink } from 'lucide-react';
import { usePendingApprovals } from '@/lib/api/hooks/useCAB';
import { useDeployments } from '@/lib/api/hooks/useDeployments';
import { formatDistanceToNow } from 'date-fns';
import { useNavigate } from 'react-router-dom';
import { Loader2 } from 'lucide-react';

export default function Notifications() {
    const navigate = useNavigate();
    const { data: pendingApprovals = [], isLoading: approvalsLoading } = usePendingApprovals();
    const { data: deployments = [], isLoading: deploymentsLoading } = useDeployments();
    
    const isLoading = approvalsLoading || deploymentsLoading;
    
    // Get all notifications
    // CRITICAL FIX: Use unique keys by combining type and correlation_id to prevent duplicate key warnings
    const allNotifications = [
        // Pending CAB Approvals
        ...pendingApprovals.map(approval => ({
            id: `cab_approval_${approval.correlation_id}`, // Unique key: type + correlation_id
            type: 'cab_approval' as const,
            title: `CAB Review: ${approval.app_name} ${approval.version}`,
            description: `Risk Score: ${approval.risk_score} • Requires CAB approval`,
            timestamp: approval.submitted_at,
            status: 'pending' as const,
            icon: Clock,
            iconColor: 'text-eucora-gold',
            badgeColor: 'bg-eucora-gold/10 text-eucora-gold border-eucora-gold/30',
            onClick: () => navigate('/cab'),
        })),
        // Deployments awaiting CAB (exclude those already in pendingApprovals to avoid duplicates)
        ...deployments
            .filter(d => {
                // Only include if not already in pendingApprovals (avoid duplicate notifications)
                const hasPendingApproval = pendingApprovals.some(pa => pa.correlation_id === d.correlation_id);
                return d.status === 'AWAITING_CAB' && !hasPendingApproval;
            })
            .map(deployment => ({
                id: `deployment_awaiting_cab_${deployment.correlation_id}`, // Unique key: type + correlation_id
                type: 'deployment_awaiting_cab' as const,
                title: `Awaiting CAB: ${deployment.app_name} ${deployment.version}`,
                description: `Ring: ${deployment.target_ring} • Risk: ${deployment.risk_score || 'N/A'}`,
                timestamp: deployment.created_at,
                status: 'pending' as const,
                icon: AlertCircle,
                iconColor: 'text-eucora-gold',
                badgeColor: 'bg-eucora-gold/10 text-eucora-gold border-eucora-gold/30',
                onClick: () => navigate('/cab'),
            })),
        // Deployments in progress
        ...deployments
            .filter(d => d.status === 'DEPLOYING')
            .map(deployment => ({
                id: `deployment_in_progress_${deployment.correlation_id}`, // Unique key: type + correlation_id
                type: 'deployment_in_progress' as const,
                title: `Deploying: ${deployment.app_name} ${deployment.version}`,
                description: `Ring: ${deployment.target_ring} • Deployment in progress`,
                timestamp: deployment.created_at,
                status: 'active' as const,
                icon: CheckCircle2,
                iconColor: 'text-eucora-green',
                badgeColor: 'bg-eucora-green/10 text-eucora-green border-eucora-green/30',
                onClick: () => navigate('/dashboard'),
            })),
    ].sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
    
    const pendingCount = allNotifications.filter(n => n.status === 'pending').length;
    const activeCount = allNotifications.filter(n => n.status === 'active').length;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                        <Bell className="h-8 w-8 text-eucora-teal" />
                        Notifications
                    </h2>
                    <p className="text-muted-foreground mt-1">
                        View all pending approvals, deployments, and system notifications
                    </p>
                </div>
                <div className="flex items-center gap-3">
                    {pendingCount > 0 && (
                        <Badge variant="outline" className="text-eucora-gold border-eucora-gold/50 bg-eucora-gold/10">
                            {pendingCount} Pending
                        </Badge>
                    )}
                    {activeCount > 0 && (
                        <Badge variant="outline" className="text-eucora-green border-eucora-green/50 bg-eucora-green/10">
                            {activeCount} Active
                        </Badge>
                    )}
                </div>
            </div>

            {isLoading ? (
                <Card className="glass">
                    <CardContent className="flex items-center justify-center py-12">
                        <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                    </CardContent>
                </Card>
            ) : allNotifications.length === 0 ? (
                <Card className="glass">
                    <CardContent className="flex flex-col items-center justify-center py-12">
                        <Bell className="h-12 w-12 text-muted-foreground mb-4 opacity-50" />
                        <p className="text-lg font-medium text-muted-foreground">No notifications</p>
                        <p className="text-sm text-muted-foreground mt-2">
                            You're all caught up! New notifications will appear here.
                        </p>
                    </CardContent>
                </Card>
            ) : (
                <Card className="glass">
                    <CardHeader>
                        <CardTitle>All Notifications</CardTitle>
                        <CardDescription>
                            {allNotifications.length} total notification{allNotifications.length !== 1 ? 's' : ''}
                        </CardDescription>
                    </CardHeader>
                    <CardContent>
                        <ScrollArea className="h-[600px]">
                            <div className="space-y-2">
                                {allNotifications.map((notification, index) => {
                                    const Icon = notification.icon;
                                    return (
                                        <div key={notification.id}>
                                            <div
                                                className="flex items-start gap-4 p-4 rounded-lg hover:bg-muted/50 transition-colors cursor-pointer group"
                                                onClick={notification.onClick}
                                            >
                                                <div className={`p-2 rounded-lg ${notification.badgeColor} flex-shrink-0`}>
                                                    <Icon className={`h-5 w-5 ${notification.iconColor}`} />
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <div className="flex items-start justify-between gap-2">
                                                        <div className="flex-1 min-w-0">
                                                            <p className="text-sm font-medium text-foreground group-hover:text-eucora-teal transition-colors">
                                                                {notification.title}
                                                            </p>
                                                            <p className="text-xs text-muted-foreground mt-1">
                                                                {notification.description}
                                                            </p>
                                                            <p className="text-xs text-muted-foreground mt-2">
                                                                {formatDistanceToNow(new Date(notification.timestamp), { addSuffix: true })}
                                                            </p>
                                                        </div>
                                                        <Badge
                                                            variant="outline"
                                                            className={notification.badgeColor}
                                                        >
                                                            {notification.status === 'pending' ? 'Pending' : 'Active'}
                                                        </Badge>
                                                    </div>
                                                </div>
                                                <ExternalLink className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity flex-shrink-0 mt-1" />
                                            </div>
                                            {index < allNotifications.length - 1 && <Separator className="my-2" />}
                                        </div>
                                    );
                                })}
                            </div>
                        </ScrollArea>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
