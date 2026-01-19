import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { ScrollArea } from '@/components/ui/scroll-area';
import { LoadingButton } from '@/components/ui/loading-button';
import { SkeletonList } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Plus, AlertOctagon, CheckCircle2, Clock, FileText } from 'lucide-react';
import { useCABApprovals, useApproveDeployment, useRejectDeployment } from '@/lib/api/hooks/useCAB';
import { useEvidencePack } from '@/lib/api/hooks/useEvidence';
import { useNavigate } from 'react-router-dom';
import { Dialog, DialogContent, DialogDescription, DialogHeader, DialogTitle } from '@/components/ui/dialog';

const STATUS_COLUMNS = [
    { id: 'New', label: 'New Requests', color: 'border-blue-500/50' },
    { id: 'Assessing', label: 'Technical Assessment', color: 'border-yellow-500/50' },
    { id: 'CAB Review', label: 'CAB Review', color: 'border-purple-500/50' },
    { id: 'Approved', label: 'Approved', color: 'border-green-500/50' },
];

export default function CABPortal() {
    const navigate = useNavigate();
    const [selectedApproval, setSelectedApproval] = useState<CABApproval | null>(null);
    const [comments, setComments] = useState('');
    const [conditions, setConditions] = useState<string[]>([]);

    // Fetch all CAB approvals (not just pending) to show all workflow stages
    const { data: approvals = [], isLoading } = useCABApprovals();
    const approveMutation = useApproveDeployment();
    const rejectMutation = useRejectDeployment();

    // Group approvals by status
    const groupedApprovals = {
        'New': approvals.filter(a => !a.reviewed_at && a.decision === 'PENDING' && (!a.comments || !a.comments.includes('CAB review'))),
        'Assessing': approvals.filter(a => a.reviewed_at && a.decision === 'PENDING'), // Under technical assessment (reviewed but still pending)
        'CAB Review': approvals.filter(a => a.decision === 'PENDING' && !a.reviewed_at && a.comments && a.comments.includes('CAB review')), // Explicitly awaiting CAB review
        'Approved': approvals.filter(a => a.decision === 'APPROVED' || a.decision === 'CONDITIONAL'),
    };

    const handleApprove = async (correlationId: string) => {
        await approveMutation.mutateAsync({
            correlationId,
            data: {
                comments,
                conditions: conditions.length > 0 ? conditions : undefined,
            },
        });
        setSelectedApproval(null);
        setComments('');
        setConditions([]);
    };

    const handleReject = async (correlationId: string) => {
        if (!comments.trim()) {
            alert('Please provide rejection comments');
            return;
        }
        await rejectMutation.mutateAsync({
            correlationId,
            comments,
        });
        setSelectedApproval(null);
        setComments('');
    };

    return (
        <div className="flex flex-col h-[calc(100vh-100px)] space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">CAB Portal</h2>
                    <p className="text-muted-foreground">Change Advisory Board management and approval workflow.</p>
                </div>
                <Button className="bg-eucora-deepBlue hover:bg-eucora-deepBlue-dark text-white" onClick={() => navigate('/deploy')}>
                    <Plus className="mr-2 h-4 w-4" /> New Change Request
                </Button>
            </div>

            {isLoading ? (
                <SkeletonList items={5} />
            ) : approvals.length === 0 ? (
                <EmptyState
                    icon={FileText}
                    title="No pending approvals"
                    description="All deployment requests have been reviewed. New high-risk deployments will appear here."
                />
            ) : (
                <div className="flex-1 overflow-x-auto">
                    <div className="flex h-full gap-4 min-w-[1000px] pb-4">
                        {STATUS_COLUMNS.map((column) => {
                            const columnItems = groupedApprovals[column.id as keyof typeof groupedApprovals] || [];
                            return (
                                <div key={column.id} className="w-[350px] flex flex-col rounded-xl bg-white/5 border border-white/10 overflow-hidden">
                                    <div className={`p-4 border-b-2 bg-white/5 ${column.color}`}>
                                        <h3 className="font-semibold flex items-center justify-between">
                                            {column.label}
                                            <Badge variant="secondary" className="glass bg-white/10">
                                                {columnItems.length}
                                            </Badge>
                                        </h3>
                                    </div>
                                    <ScrollArea className="flex-1 p-3">
                                        <div className="space-y-3">
                                            {columnItems.map((approval) => (
                                                <ChangeCard
                                                    key={approval.correlation_id}
                                                    approval={approval}
                                                    isSelected={selectedApproval?.correlation_id === approval.correlation_id}
                                                    onSelect={() => setSelectedApproval(approval)}
                                                />
                                            ))}
                                            {columnItems.length === 0 && (
                                                <div className="flex flex-col items-center justify-center py-10 opacity-50 border-2 border-dashed border-white/10 rounded-lg">
                                                    <span className="text-sm">No requests</span>
                                                </div>
                                            )}
                                        </div>
                                    </ScrollArea>
                                </div>
                            );
                        })}
                    </div>
                </div>
            )}

            {/* Approval Detail Dialog */}
            {selectedApproval && (
                <Dialog open={!!selectedApproval} onOpenChange={(open) => !open && setSelectedApproval(null)}>
                    <DialogContent className="max-w-2xl max-h-[80vh] overflow-y-auto">
                        <DialogHeader>
                            <DialogTitle>Review Deployment Request</DialogTitle>
                            <DialogDescription>
                                Review evidence pack and make approval decision
                            </DialogDescription>
                        </DialogHeader>
                        <ApprovalDetail
                            correlationId={selectedApproval.evidence_pack_correlation_id || selectedApproval.correlation_id}
                            comments={comments}
                            setComments={setComments}
                            onApprove={() => handleApprove(selectedApproval.correlation_id)}
                            onReject={() => handleReject(selectedApproval.correlation_id)}
                            approveLoading={approveMutation.isPending}
                            rejectLoading={rejectMutation.isPending}
                        />
                    </DialogContent>
                </Dialog>
            )}
        </div>
    );
}

import type { CABApproval } from '@/lib/api/hooks/useCAB';

function ChangeCard({ approval, isSelected, onSelect }: { approval: CABApproval; isSelected: boolean; onSelect: () => void }) {
    return (
        <Card
            className={`glass cursor-pointer hover:border-primary/50 transition-colors group ${
                isSelected ? 'border-primary bg-primary/10' : ''
            }`}
            onClick={onSelect}
        >
            <CardHeader className="p-4 pb-2 space-y-2">
                <div className="flex justify-between items-start">
                    <Badge variant="outline" className="font-mono text-[10px] tracking-wider text-muted-foreground border-white/20">
                        {approval.correlation_id.slice(0, 8)}
                    </Badge>
                    <Badge
                        variant={approval.risk_score > 70 ? 'destructive' : 'secondary'}
                        className="text-[10px]"
                    >
                        Risk: {approval.risk_score}
                    </Badge>
                </div>
                <CardTitle className="text-sm font-medium leading-snug group-hover:text-primary transition-colors">
                    {approval.app_name} v{approval.version}
                </CardTitle>
            </CardHeader>
            <CardContent className="p-4 pt-2">
                <div className="flex items-center justify-between text-xs">
                    <div className="flex items-center gap-1 text-muted-foreground">
                        <Clock className="w-3 h-3" />
                        <span>{new Date(approval.submitted_at).toLocaleDateString()}</span>
                    </div>
                    {approval.risk_score > 70 ? (
                        <div className="flex items-center gap-1 text-eucora-red font-bold">
                            <AlertOctagon className="w-3 h-3" />
                            <span>High Risk</span>
                        </div>
                    ) : (
                        <div className="flex items-center gap-1 text-eucora-green font-bold">
                            <CheckCircle2 className="w-3 h-3" />
                            <span>Safe</span>
                        </div>
                    )}
                </div>
            </CardContent>
        </Card>
    );
}

function ApprovalDetail({
    correlationId,
    comments,
    setComments,
    onApprove,
    onReject,
    approveLoading,
    rejectLoading,
}: {
    correlationId: string;
    comments: string;
    setComments: (value: string) => void;
    onApprove: () => void;
    onReject: () => void;
    approveLoading: boolean;
    rejectLoading: boolean;
}) {
    const { data: evidencePack, isLoading: evidenceLoading } = useEvidencePack(correlationId);
    const navigate = useNavigate();

    return (
        <div className="space-y-4">
            {/* Evidence Pack Summary */}
            {evidenceLoading ? (
                <div>Loading evidence pack...</div>
            ) : evidencePack ? (
                <Card className="glass">
                    <CardHeader>
                        <CardTitle className="text-sm">Evidence Pack</CardTitle>
                    </CardHeader>
                    <CardContent className="space-y-2 text-sm">
                        <div className="flex justify-between">
                            <span className="text-muted-foreground">Artifact Hash:</span>
                            <span className="font-mono text-xs">{evidencePack.artifact_hash.slice(0, 16)}...</span>
                        </div>
                        <div className="flex justify-between">
                            <span className="text-muted-foreground">SBOM Status:</span>
                            <Badge variant={evidencePack.is_validated ? 'default' : 'destructive'}>
                                {evidencePack.is_validated ? 'Validated' : 'Invalid'}
                            </Badge>
                        </div>
                        <Button
                            variant="outline"
                            size="sm"
                            onClick={() => navigate(`/evidence/${correlationId}`)}
                            className="w-full mt-2"
                        >
                            View Full Evidence Pack
                        </Button>
                    </CardContent>
                </Card>
            ) : null}

            {/* Comments */}
            <div className="space-y-2">
                <label className="text-sm font-medium">Reviewer Comments</label>
                <Textarea
                    placeholder="Enter approval/rejection reason..."
                    value={comments}
                    onChange={(e) => setComments(e.target.value)}
                    rows={5}
                    aria-label="Review comments"
                />
            </div>

            {/* Action Buttons */}
            <div className="flex gap-2">
                <LoadingButton
                    onClick={onApprove}
                    loading={approveLoading}
                    className="flex-1 bg-eucora-green hover:bg-eucora-green-dark"
                >
                    Approve
                </LoadingButton>
                <LoadingButton
                    onClick={onReject}
                    loading={rejectLoading}
                    variant="destructive"
                    className="flex-1"
                >
                    Reject
                </LoadingButton>
            </div>
        </div>
    );
}
