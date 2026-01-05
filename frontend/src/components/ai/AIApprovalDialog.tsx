// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * AI Approval Dialog Component.
 * 
 * Provides human-in-the-loop approval workflow for AI recommendations.
 * All AI-generated actions require explicit human approval before execution.
 * 
 * Features:
 * - Approve: Accept the AI recommendation as-is
 * - Reject: Decline the recommendation with a reason
 * - Request Revision: Provide feedback to improve the AI's suggestion
 */
import { useState } from 'react';
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Badge } from '@/components/ui/badge';
import { Separator } from '@/components/ui/separator';
import { ScrollArea } from '@/components/ui/scroll-area';
import {
    AlertTriangle,
    CheckCircle2,
    XCircle,
    Sparkles,
    Clock,
    User,
    FileText,
    Shield,
    Loader2,
    MessageSquare,
    RotateCcw,
    History,
} from 'lucide-react';
import { useApproveTask, useRejectTask, useRequestRevision, type AIAgentTask } from '@/lib/api/hooks/useAI';
import { useAuth } from '@/lib/hooks/useAuth';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

interface AIApprovalDialogProps {
    task: AIAgentTask | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
    onApproved?: (task: AIAgentTask) => void;
    onRejected?: (task: AIAgentTask) => void;
    onRevisionRequested?: (task: AIAgentTask, revisedDescription: string) => void;
}

export function AIApprovalDialog({
    task,
    open,
    onOpenChange,
    onApproved,
    onRejected,
    onRevisionRequested,
}: AIApprovalDialogProps) {
    const { user } = useAuth();
    const [comment, setComment] = useState('');
    const [rejectionReason, setRejectionReason] = useState('');
    const [feedbackText, setFeedbackText] = useState('');
    const [mode, setMode] = useState<'view' | 'approve' | 'reject' | 'feedback'>('view');
    
    const { mutate: approveTask, isPending: isApproving } = useApproveTask();
    const { mutate: rejectTask, isPending: isRejecting } = useRejectTask();
    const { mutate: requestRevision, isPending: isRequestingRevision } = useRequestRevision();
    
    const canApprove = user?.is_staff || user?.is_superuser || user?.role === 'admin';
    const isPending = isApproving || isRejecting || isRequestingRevision;
    
    const handleApprove = () => {
        if (!task) return;
        
        approveTask(
            { taskId: task.id, comment },
            {
                onSuccess: () => {
                    toast.success('Task approved successfully', {
                        description: `"${task.title}" has been approved for execution.`,
                    });
                    setComment('');
                    setMode('view');
                    onOpenChange(false);
                    onApproved?.(task);
                },
                onError: (error: any) => {
                    toast.error('Failed to approve task', {
                        description: error?.response?.data?.error || 'An error occurred',
                    });
                },
            }
        );
    };
    
    const handleReject = () => {
        if (!task || !rejectionReason.trim()) {
            toast.error('Please provide a reason for rejection');
            return;
        }
        
        rejectTask(
            { taskId: task.id, reason: rejectionReason },
            {
                onSuccess: () => {
                    toast.info('Task rejected', {
                        description: `"${task.title}" has been rejected.`,
                    });
                    setRejectionReason('');
                    setMode('view');
                    onOpenChange(false);
                    onRejected?.(task);
                },
                onError: (error: any) => {
                    toast.error('Failed to reject task', {
                        description: error?.response?.data?.error || 'An error occurred',
                    });
                },
            }
        );
    };
    
    const handleRequestRevision = () => {
        if (!task || !feedbackText.trim()) {
            toast.error('Please provide feedback for improvement');
            return;
        }
        
        requestRevision(
            { taskId: task.id, feedback: feedbackText },
            {
                onSuccess: (response) => {
                    toast.success('Revision requested', {
                        description: response.task.revised_recommendation 
                            ? 'AI has generated a revised recommendation based on your feedback.'
                            : 'Your feedback has been recorded. AI will generate a revised recommendation.',
                    });
                    
                    // If AI responded with a revision, call the callback
                    if (response.task.revised_recommendation) {
                        onRevisionRequested?.(task, response.task.revised_recommendation);
                    }
                    
                    setFeedbackText('');
                    setMode('view');
                    // Keep dialog open to show the revised recommendation
                    // onOpenChange(false);
                },
                onError: (error: any) => {
                    toast.error('Failed to request revision', {
                        description: error?.response?.data?.error || 'An error occurred',
                    });
                },
            }
        );
    };
    
    const resetAndClose = () => {
        setComment('');
        setRejectionReason('');
        setFeedbackText('');
        setMode('view');
        onOpenChange(false);
    };
    
    if (!task) return null;
    
    const statusColors: Record<string, string> = {
        'awaiting_approval': 'bg-eucora-gold/20 text-eucora-gold border-eucora-gold/30',
        'revision_requested': 'bg-purple-500/20 text-purple-500 border-purple-500/30',
        'approved': 'bg-eucora-green/20 text-eucora-green border-eucora-green/30',
        'rejected': 'bg-destructive/20 text-destructive border-destructive/30',
        'executing': 'bg-blue-500/20 text-blue-500 border-blue-500/30',
        'completed': 'bg-eucora-green/20 text-eucora-green border-eucora-green/30',
        'failed': 'bg-destructive/20 text-destructive border-destructive/30',
    };
    
    // Safely get status display text
    const statusDisplay = task.status ? task.status.replace('_', ' ') : 'pending';
    const agentDisplay = task.agent_type_display || task.agent_type || 'AI Agent';
    const taskTypeDisplay = task.task_type ? task.task_type.replace('_', ' ') : 'recommendation';
    
    return (
        <Dialog open={open} onOpenChange={resetAndClose}>
            <DialogContent className="sm:max-w-[600px] glass border-border/50">
                <DialogHeader>
                    <div className="flex items-center gap-3">
                        <div className="p-2 rounded-xl bg-gradient-to-br from-eucora-teal/20 to-eucora-coral/10 border border-eucora-teal/30">
                            <Sparkles className="h-5 w-5 text-eucora-teal" />
                        </div>
                        <div>
                            <DialogTitle className="text-lg flex items-center gap-2">
                                AI Recommendation
                                <Badge variant="outline" className={cn('text-xs', statusColors[task.status || 'awaiting_approval'] || '')}>
                                    {statusDisplay}
                                </Badge>
                            </DialogTitle>
                            <DialogDescription className="text-sm">
                                Review and approve this AI-generated action
                            </DialogDescription>
                        </div>
                    </div>
                </DialogHeader>
                
                <ScrollArea className="max-h-[400px] pr-4">
                    <div className="space-y-4 py-4">
                        {/* Task Info */}
                        <div className="space-y-3">
                            <div className="flex items-center gap-2 text-sm font-medium">
                                <FileText className="h-4 w-4 text-muted-foreground" />
                                <span>{task.title}</span>
                            </div>
                            
                            <div className="p-4 rounded-lg bg-muted/30 border border-border/50">
                                <p className="text-sm whitespace-pre-wrap">{task.description}</p>
                            </div>
                        </div>
                        
                        {/* Metadata */}
                        <div className="grid grid-cols-2 gap-4 text-sm">
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <Sparkles className="h-4 w-4" />
                                <span>Agent: {agentDisplay}</span>
                            </div>
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <Clock className="h-4 w-4" />
                                <span>{task.created_at ? new Date(task.created_at).toLocaleString() : 'Just now'}</span>
                            </div>
                            {task.initiated_by && (
                                <div className="flex items-center gap-2 text-muted-foreground">
                                    <User className="h-4 w-4" />
                                    <span>Requested by: {task.initiated_by.name || task.initiated_by.username}</span>
                                </div>
                            )}
                            <div className="flex items-center gap-2 text-muted-foreground">
                                <Shield className="h-4 w-4" />
                                <span>Type: {taskTypeDisplay}</span>
                            </div>
                        </div>
                        
                        {/* Input Data Preview (if any) */}
                        {task.input_data && Object.keys(task.input_data).length > 0 && (
                            <>
                                <Separator />
                                <div className="space-y-2">
                                    <Label className="text-xs text-muted-foreground uppercase tracking-wider">
                                        Input Parameters
                                    </Label>
                                    <div className="p-3 rounded-lg bg-background/50 border border-border/50 font-mono text-xs">
                                        <pre className="whitespace-pre-wrap overflow-x-auto">
                                            {JSON.stringify(task.input_data, null, 2)}
                                        </pre>
                                    </div>
                                </div>
                            </>
                        )}
                        
                        {/* Output/Recommendation Preview (if any) */}
                        {task.output_data && Object.keys(task.output_data).length > 0 && !task.output_data.approval && !task.output_data.rejection && (
                            <>
                                <Separator />
                                <div className="space-y-2">
                                    <Label className="text-xs text-muted-foreground uppercase tracking-wider">
                                        AI Recommendation Details
                                    </Label>
                                    <div className="p-3 rounded-lg bg-background/50 border border-border/50 font-mono text-xs">
                                        <pre className="whitespace-pre-wrap overflow-x-auto">
                                            {JSON.stringify(task.output_data, null, 2)}
                                        </pre>
                                    </div>
                                </div>
                            </>
                        )}
                        
                        <Separator />
                        
                        {/* Warning Banner */}
                        <div className="flex items-start gap-3 p-4 rounded-lg bg-eucora-gold/10 border border-eucora-gold/30">
                            <AlertTriangle className="h-5 w-5 text-eucora-gold shrink-0 mt-0.5" />
                            <div className="text-sm">
                                <p className="font-medium text-eucora-gold-dark dark:text-eucora-gold">
                                    Human Approval Required
                                </p>
                                <p className="text-muted-foreground mt-1">
                                    This AI recommendation requires explicit human approval before any action is taken.
                                    Please review the details carefully before approving or rejecting.
                                </p>
                            </div>
                        </div>
                        
                        {/* Revision History */}
                        {task.output_data?.revisions && task.output_data.revisions.length > 0 && (
                            <>
                                <Separator />
                                <div className="space-y-3">
                                    <div className="flex items-center gap-2 text-sm font-medium">
                                        <History className="h-4 w-4 text-purple-500" />
                                        <span>Revision History ({task.output_data.revisions.length})</span>
                                    </div>
                                    <div className="space-y-2 max-h-[200px] overflow-y-auto">
                                        {task.output_data.revisions.map((revision: any, index: number) => (
                                            <div 
                                                key={index} 
                                                className="p-3 rounded-lg bg-purple-500/10 border border-purple-500/30 text-sm"
                                            >
                                                <div className="flex items-center justify-between mb-2">
                                                    <Badge variant="outline" className="text-xs bg-purple-500/20 text-purple-400 border-purple-500/30">
                                                        Revision #{revision.revision_number}
                                                    </Badge>
                                                    <span className="text-xs text-muted-foreground">
                                                        {new Date(revision.requested_at).toLocaleString()}
                                                    </span>
                                                </div>
                                                <p className="text-xs text-muted-foreground mb-1">
                                                    <span className="font-medium">Feedback by {revision.requested_by}:</span>
                                                </p>
                                                <p className="text-sm italic text-purple-300">"{revision.feedback}"</p>
                                                {revision.ai_response && (
                                                    <div className="mt-2 pt-2 border-t border-purple-500/20">
                                                        <p className="text-xs text-muted-foreground mb-1">
                                                            <span className="font-medium text-eucora-teal">AI Revised Response:</span>
                                                        </p>
                                                        <p className="text-xs text-muted-foreground line-clamp-2">
                                                            {revision.ai_response.substring(0, 150)}...
                                                        </p>
                                                    </div>
                                                )}
                                            </div>
                                        ))}
                                    </div>
                                </div>
                            </>
                        )}
                        
                        {/* Approve/Reject/Feedback Inputs */}
                        {(task.status === 'awaiting_approval' || task.status === 'revision_requested') && canApprove && (
                            <>
                                {mode === 'approve' && (
                                    <div className="space-y-2">
                                        <Label htmlFor="approval-comment">Approval Comment (Optional)</Label>
                                        <Textarea
                                            id="approval-comment"
                                            value={comment}
                                            onChange={(e) => setComment(e.target.value)}
                                            placeholder="Add any notes or conditions for this approval..."
                                            className="min-h-[80px] bg-background/50"
                                        />
                                    </div>
                                )}
                                
                                {mode === 'reject' && (
                                    <div className="space-y-2">
                                        <Label htmlFor="rejection-reason" className="text-destructive">
                                            Rejection Reason (Required)
                                        </Label>
                                        <Textarea
                                            id="rejection-reason"
                                            value={rejectionReason}
                                            onChange={(e) => setRejectionReason(e.target.value)}
                                            placeholder="Explain why this recommendation is being rejected..."
                                            className="min-h-[80px] bg-background/50 border-destructive/50 focus:border-destructive"
                                            required
                                        />
                                    </div>
                                )}
                                
                                {mode === 'feedback' && (
                                    <div className="space-y-3 p-4 rounded-lg bg-purple-500/10 border border-purple-500/30">
                                        <div className="flex items-center gap-2">
                                            <MessageSquare className="h-4 w-4 text-purple-500" />
                                            <Label htmlFor="feedback-text" className="text-purple-400 font-medium">
                                                Provide Feedback for Improvement
                                            </Label>
                                        </div>
                                        <p className="text-xs text-muted-foreground">
                                            Tell the AI what to improve, correct, or change in the recommendation. 
                                            The AI will generate a revised suggestion based on your feedback.
                                        </p>
                                        <Textarea
                                            id="feedback-text"
                                            value={feedbackText}
                                            onChange={(e) => setFeedbackText(e.target.value)}
                                            placeholder="Example: Please consider the following constraints... / The deployment should also include... / Can you provide more detail about..."
                                            className="min-h-[100px] bg-background/50 border-purple-500/50 focus:border-purple-500"
                                            required
                                        />
                                        <div className="flex items-center gap-2 text-xs text-purple-400">
                                            <RotateCcw className="h-3 w-3" />
                                            <span>AI will generate a revised recommendation based on your feedback</span>
                                        </div>
                                    </div>
                                )}
                            </>
                        )}
                        
                        {/* Already Processed Info */}
                        {task.output_data?.approval && (
                            <div className="p-4 rounded-lg bg-eucora-green/10 border border-eucora-green/30">
                                <div className="flex items-center gap-2 text-eucora-green font-medium">
                                    <CheckCircle2 className="h-5 w-5" />
                                    Approved
                                </div>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Approved by {task.output_data.approval.approved_by} on{' '}
                                    {new Date(task.output_data.approval.approved_at).toLocaleString()}
                                </p>
                                {task.output_data.approval.comment && (
                                    <p className="text-sm mt-2 italic">
                                        "{task.output_data.approval.comment}"
                                    </p>
                                )}
                            </div>
                        )}
                        
                        {task.output_data?.rejection && (
                            <div className="p-4 rounded-lg bg-destructive/10 border border-destructive/30">
                                <div className="flex items-center gap-2 text-destructive font-medium">
                                    <XCircle className="h-5 w-5" />
                                    Rejected
                                </div>
                                <p className="text-sm text-muted-foreground mt-1">
                                    Rejected by {task.output_data.rejection.rejected_by} on{' '}
                                    {new Date(task.output_data.rejection.rejected_at).toLocaleString()}
                                </p>
                                <p className="text-sm mt-2">
                                    Reason: {task.output_data.rejection.reason}
                                </p>
                            </div>
                        )}
                        
                        {/* No permission message */}
                        {task.status === 'awaiting_approval' && !canApprove && (
                            <div className="p-4 rounded-lg bg-muted/30 border border-border/50 text-center">
                                <Shield className="h-8 w-8 text-muted-foreground mx-auto mb-2" />
                                <p className="text-sm text-muted-foreground">
                                    You don't have permission to approve or reject tasks.
                                    <br />
                                    Contact an administrator for approval.
                                </p>
                            </div>
                        )}
                    </div>
                </ScrollArea>
                
                <DialogFooter className="flex-col sm:flex-row gap-2">
                    {(task.status === 'awaiting_approval' || task.status === 'revision_requested') && canApprove ? (
                        <>
                            {mode === 'view' && (
                                <>
                                    <Button
                                        variant="outline"
                                        onClick={resetAndClose}
                                        className="sm:mr-auto"
                                    >
                                        Close
                                    </Button>
                                    <Button
                                        variant="outline"
                                        onClick={() => setMode('feedback')}
                                        className="border-purple-500/50 text-purple-400 hover:bg-purple-500/10 hover:text-purple-300"
                                    >
                                        <MessageSquare className="h-4 w-4 mr-2" />
                                        Request Revision
                                    </Button>
                                    <Button
                                        variant="destructive"
                                        onClick={() => setMode('reject')}
                                    >
                                        <XCircle className="h-4 w-4 mr-2" />
                                        Reject
                                    </Button>
                                    <Button
                                        onClick={() => setMode('approve')}
                                        className="bg-eucora-green hover:bg-eucora-green/90"
                                    >
                                        <CheckCircle2 className="h-4 w-4 mr-2" />
                                        Approve
                                    </Button>
                                </>
                            )}
                            
                            {mode === 'approve' && (
                                <>
                                    <Button
                                        variant="outline"
                                        onClick={() => setMode('view')}
                                        disabled={isPending}
                                    >
                                        Back
                                    </Button>
                                    <Button
                                        onClick={handleApprove}
                                        disabled={isPending}
                                        className="bg-eucora-green hover:bg-eucora-green/90"
                                    >
                                        {isApproving ? (
                                            <>
                                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                                Approving...
                                            </>
                                        ) : (
                                            <>
                                                <CheckCircle2 className="h-4 w-4 mr-2" />
                                                Confirm Approval
                                            </>
                                        )}
                                    </Button>
                                </>
                            )}
                            
                            {mode === 'reject' && (
                                <>
                                    <Button
                                        variant="outline"
                                        onClick={() => setMode('view')}
                                        disabled={isPending}
                                    >
                                        Back
                                    </Button>
                                    <Button
                                        variant="destructive"
                                        onClick={handleReject}
                                        disabled={isPending || !rejectionReason.trim()}
                                    >
                                        {isRejecting ? (
                                            <>
                                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                                Rejecting...
                                            </>
                                        ) : (
                                            <>
                                                <XCircle className="h-4 w-4 mr-2" />
                                                Confirm Rejection
                                            </>
                                        )}
                                    </Button>
                                </>
                            )}
                            
                            {mode === 'feedback' && (
                                <>
                                    <Button
                                        variant="outline"
                                        onClick={() => setMode('view')}
                                        disabled={isPending}
                                    >
                                        Back
                                    </Button>
                                    <Button
                                        onClick={handleRequestRevision}
                                        disabled={isPending || !feedbackText.trim()}
                                        className="bg-purple-600 hover:bg-purple-700 text-white"
                                    >
                                        {isRequestingRevision ? (
                                            <>
                                                <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                                                Requesting Revision...
                                            </>
                                        ) : (
                                            <>
                                                <RotateCcw className="h-4 w-4 mr-2" />
                                                Submit Feedback
                                            </>
                                        )}
                                    </Button>
                                </>
                            )}
                        </>
                    ) : (
                        <Button onClick={resetAndClose}>Close</Button>
                    )}
                </DialogFooter>
            </DialogContent>
        </Dialog>
    );
}

export default AIApprovalDialog;

