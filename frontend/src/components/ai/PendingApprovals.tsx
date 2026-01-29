// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Pending Approvals Component.
 *
 * Displays a list of AI-generated tasks awaiting human approval.
 * Can be used as a standalone panel or embedded in other views.
 */
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Skeleton } from '@/components/ui/skeleton';
import {
    AlertTriangle,
    Clock,
    Sparkles,
    RefreshCw,
    ChevronRight,
    InboxIcon,
    User,
} from 'lucide-react';
import { usePendingApprovals, type AIAgentTask } from '@/lib/api/hooks/useAI';
import { AIApprovalDialog } from './AIApprovalDialog';
import { cn } from '@/lib/utils';
import { formatDistanceToNow } from 'date-fns';

interface PendingApprovalsProps {
    compact?: boolean;
    maxItems?: number;
    className?: string;
    onTaskClick?: (task: AIAgentTask) => void;
}

export function PendingApprovals({
    compact = false,
    maxItems,
    className,
    onTaskClick,
}: PendingApprovalsProps) {
    const { data, isLoading, refetch, isRefetching } = usePendingApprovals();
    const [selectedTask, setSelectedTask] = useState<AIAgentTask | null>(null);
    const [dialogOpen, setDialogOpen] = useState(false);

    const pendingTasks = data?.pending_approvals || [];
    const displayTasks = maxItems ? pendingTasks.slice(0, maxItems) : pendingTasks;
    const hasMore = maxItems && pendingTasks.length > maxItems;

    const handleTaskClick = (task: AIAgentTask) => {
        if (onTaskClick) {
            onTaskClick(task);
        } else {
            setSelectedTask(task);
            setDialogOpen(true);
        }
    };

    const agentTypeColors: Record<string, string> = {
        'amani': 'bg-eucora-teal/20 text-eucora-teal border-eucora-teal/30',
        'packaging': 'bg-blue-500/20 text-blue-500 border-blue-500/30',
        'cab_evidence': 'bg-purple-500/20 text-purple-500 border-purple-500/30',
        'deployment': 'bg-eucora-coral/20 text-eucora-coral border-eucora-coral/30',
        'compliance': 'bg-eucora-green/20 text-eucora-green border-eucora-green/30',
    };

    if (compact) {
        // Compact mode for sidebar or small spaces
        return (
            <>
                <div className={cn('space-y-2', className)}>
                    {isLoading ? (
                        <div className="space-y-2">
                            {[1, 2, 3].map((i) => (
                                <Skeleton key={i} className="h-12 w-full" />
                            ))}
                        </div>
                    ) : pendingTasks.length === 0 ? (
                        <div className="text-center py-4 text-sm text-muted-foreground">
                            <InboxIcon className="h-6 w-6 mx-auto mb-2 opacity-50" />
                            No pending approvals
                        </div>
                    ) : (
                        displayTasks.map((task) => (
                            <button
                                key={task.id}
                                onClick={() => handleTaskClick(task)}
                                className="w-full p-3 rounded-lg bg-muted/30 hover:bg-muted/50 border border-border/50 hover:border-eucora-teal/30 transition-all text-left group"
                            >
                                <div className="flex items-center justify-between gap-2">
                                    <div className="flex items-center gap-2 min-w-0">
                                        <AlertTriangle className="h-4 w-4 text-eucora-gold shrink-0" />
                                        <span className="text-sm font-medium truncate">
                                            {task.title}
                                        </span>
                                    </div>
                                    <ChevronRight className="h-4 w-4 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity" />
                                </div>
                                <div className="flex items-center gap-2 mt-1 text-xs text-muted-foreground">
                                    <Clock className="h-3 w-3" />
                                    {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                                </div>
                            </button>
                        ))
                    )}

                    {hasMore && (
                        <Button variant="ghost" size="sm" className="w-full text-xs">
                            View all ({pendingTasks.length} pending)
                        </Button>
                    )}
                </div>

                <AIApprovalDialog
                    task={selectedTask}
                    open={dialogOpen}
                    onOpenChange={setDialogOpen}
                />
            </>
        );
    }

    // Full card mode
    return (
        <>
            <Card className={cn('glass', className)}>
                <CardHeader className="pb-3">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-2">
                            <div className="p-2 rounded-lg bg-eucora-gold/20 border border-eucora-gold/30">
                                <AlertTriangle className="h-5 w-5 text-eucora-gold" />
                            </div>
                            <div>
                                <CardTitle className="text-lg">Pending Approvals</CardTitle>
                                <CardDescription>
                                    AI recommendations requiring human approval
                                </CardDescription>
                            </div>
                        </div>
                        <div className="flex items-center gap-2">
                            {data?.total_count !== undefined && data.total_count > 0 && (
                                <Badge variant="secondary" className="bg-eucora-gold/20 text-eucora-gold">
                                    {data.total_count} pending
                                </Badge>
                            )}
                            <Button
                                variant="ghost"
                                size="icon"
                                onClick={() => refetch()}
                                disabled={isRefetching}
                                className="h-8 w-8"
                            >
                                <RefreshCw className={cn('h-4 w-4', isRefetching && 'animate-spin')} />
                            </Button>
                        </div>
                    </div>
                </CardHeader>

                <CardContent>
                    {isLoading ? (
                        <div className="space-y-3">
                            {[1, 2, 3].map((i) => (
                                <Skeleton key={i} className="h-20 w-full" />
                            ))}
                        </div>
                    ) : pendingTasks.length === 0 ? (
                        <div className="text-center py-8">
                            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-muted/30 flex items-center justify-center">
                                <InboxIcon className="h-8 w-8 text-muted-foreground" />
                            </div>
                            <p className="text-muted-foreground">No pending approvals</p>
                            <p className="text-sm text-muted-foreground mt-1">
                                AI recommendations will appear here for review
                            </p>
                        </div>
                    ) : (
                        <ScrollArea className="max-h-[400px]">
                            <div className="space-y-3">
                                {displayTasks.map((task) => (
                                    <button
                                        key={task.id}
                                        onClick={() => handleTaskClick(task)}
                                        className="w-full p-4 rounded-xl bg-muted/30 hover:bg-muted/50 border border-border/50 hover:border-eucora-gold/30 transition-all text-left group"
                                    >
                                        <div className="flex items-start justify-between gap-3">
                                            <div className="flex-1 min-w-0">
                                                <div className="flex items-center gap-2 mb-1">
                                                    <Sparkles className="h-4 w-4 text-eucora-teal shrink-0" />
                                                    <span className="font-medium truncate">
                                                        {task.title}
                                                    </span>
                                                </div>
                                                <p className="text-sm text-muted-foreground line-clamp-2 mb-2">
                                                    {task.description}
                                                </p>
                                                <div className="flex items-center gap-3 text-xs text-muted-foreground">
                                                    <Badge
                                                        variant="outline"
                                                        className={cn(
                                                            'text-xs',
                                                            agentTypeColors[task.agent_type] || ''
                                                        )}
                                                    >
                                                        {task.agent_type_display || task.agent_type}
                                                    </Badge>
                                                    <span className="flex items-center gap-1">
                                                        <Clock className="h-3 w-3" />
                                                        {formatDistanceToNow(new Date(task.created_at), { addSuffix: true })}
                                                    </span>
                                                    {task.initiated_by && (
                                                        <span className="flex items-center gap-1">
                                                            <User className="h-3 w-3" />
                                                            {task.initiated_by.name || task.initiated_by.username}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <ChevronRight className="h-5 w-5 text-muted-foreground opacity-0 group-hover:opacity-100 transition-opacity shrink-0" />
                                        </div>
                                    </button>
                                ))}
                            </div>
                        </ScrollArea>
                    )}
                </CardContent>
            </Card>

            <AIApprovalDialog
                task={selectedTask}
                open={dialogOpen}
                onOpenChange={setDialogOpen}
            />
        </>
    );
}

export default PendingApprovals;
