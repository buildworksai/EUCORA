// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Current Step Detail Component.
 *
 * Displays the current workflow step with appropriate view based on status.
 */
import { useState } from 'react';
import { Shield, CheckCircle, XCircle, Loader2 } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Dialog, DialogContent, DialogDescription, DialogFooter, DialogHeader, DialogTitle } from '@/components/ui/dialog';
import { useApproveWorkflowStep, useRejectWorkflowStep } from '@/lib/api/hooks/useWorkflow';
import { toast } from 'sonner';
import type { WorkflowStep } from '@/routes/ai/contracts';

interface CurrentStepDetailProps {
  step: WorkflowStep;
  executionId: string;
  onUpdate?: () => void;
}

function ApprovalGateView({ step, executionId, onUpdate }: CurrentStepDetailProps) {
  const [notes, setNotes] = useState('');
  const [rejectDialogOpen, setRejectDialogOpen] = useState(false);
  const [rejectReason, setRejectReason] = useState('');
  const approveMutation = useApproveWorkflowStep();
  const rejectMutation = useRejectWorkflowStep();

  const handleApprove = async () => {
    try {
      await approveMutation.mutateAsync({ executionId, notes });
      toast.success('Step approved');
      onUpdate?.();
    } catch {
      toast.error('Failed to approve step');
    }
  };

  const handleReject = async () => {
    if (!rejectReason.trim()) {
      toast.error('Please provide a rejection reason');
      return;
    }
    try {
      await rejectMutation.mutateAsync({ executionId, reason: rejectReason });
      toast.success('Step rejected');
      setRejectDialogOpen(false);
      onUpdate?.();
    } catch {
      toast.error('Failed to reject step');
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center gap-3">
        <div className="w-10 h-10 rounded-full bg-yellow-500/20 flex items-center justify-center">
          <Shield className="w-5 h-5 text-yellow-500" />
        </div>
        <div>
          <h2 className="text-xl font-bold">Approval Required</h2>
          <p className="text-muted-foreground">This action requires your explicit approval</p>
        </div>
      </div>

      {/* Proposed Action */}
      <Card>
        <CardHeader>
          <CardTitle className="text-base">Proposed Action</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="bg-muted p-4 rounded text-sm overflow-auto">
            {JSON.stringify(step.output_data, null, 2)}
          </pre>
        </CardContent>
      </Card>

      {/* Policies Considered */}
      {step.policies_considered && step.policies_considered.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Policies Considered</CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {step.policies_considered.map((policy, i) => (
                <div key={i} className="p-3 bg-muted rounded">
                  <p className="font-medium text-sm">{policy.document_title || 'Policy'}</p>
                  <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{policy.content}</p>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}

      {/* AI Reasoning */}
      {step.llm_response && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">AI Reasoning</CardTitle>
          </CardHeader>
          <CardContent>
            <p className="text-sm">{step.llm_response}</p>
          </CardContent>
        </Card>
      )}

      {/* Approval Notes */}
      <div className="space-y-2">
        <Label htmlFor="approval-notes">Approval Notes (Optional)</Label>
        <Textarea
          id="approval-notes"
          placeholder="Add any notes about your approval decision..."
          value={notes}
          onChange={(e) => setNotes(e.target.value)}
        />
      </div>

      {/* Action Buttons */}
      <div className="flex gap-4">
        <Button
          onClick={handleApprove}
          className="flex-1 bg-green-600 hover:bg-green-700"
          disabled={approveMutation.isPending}
        >
          {approveMutation.isPending ? (
            <>
              <Loader2 className="mr-2 h-4 w-4 animate-spin" />
              Approving...
            </>
          ) : (
            <>
              <CheckCircle className="mr-2 h-4 w-4" />
              Approve Action
            </>
          )}
        </Button>
        <Button
          onClick={() => setRejectDialogOpen(true)}
          variant="outline"
          className="flex-1 text-red-500"
          disabled={rejectMutation.isPending}
        >
          <XCircle className="mr-2 h-4 w-4" />
          Reject
        </Button>
      </div>

      {/* Reject Dialog */}
      <Dialog open={rejectDialogOpen} onOpenChange={setRejectDialogOpen}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Reject Step</DialogTitle>
            <DialogDescription>Please provide a reason for rejecting this step.</DialogDescription>
          </DialogHeader>
          <div className="space-y-2">
            <Label htmlFor="reject-reason">Rejection Reason</Label>
            <Textarea
              id="reject-reason"
              placeholder="Explain why you are rejecting this step..."
              value={rejectReason}
              onChange={(e) => setRejectReason(e.target.value)}
            />
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setRejectDialogOpen(false)}>
              Cancel
            </Button>
            <Button onClick={handleReject} variant="destructive" disabled={rejectMutation.isPending}>
              {rejectMutation.isPending ? 'Rejecting...' : 'Reject'}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}

function RunningStepView({ step }: CurrentStepDetailProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <Loader2 className="w-6 h-6 text-eucora-teal animate-spin" />
        <div>
          <h2 className="text-xl font-bold">{step.name}</h2>
          <p className="text-muted-foreground">{step.description}</p>
        </div>
      </div>
      <p className="text-sm text-muted-foreground">Processing step...</p>
    </div>
  );
}

function CompletedStepView({ step }: CurrentStepDetailProps) {
  return (
    <div className="space-y-4">
      <div className="flex items-center gap-3">
        <CheckCircle className="w-6 h-6 text-green-500" />
        <div>
          <h2 className="text-xl font-bold">{step.name}</h2>
          <p className="text-muted-foreground">{step.description}</p>
        </div>
      </div>
      {step.output_data && Object.keys(step.output_data).length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="text-base">Step Output</CardTitle>
          </CardHeader>
          <CardContent>
            <pre className="bg-muted p-4 rounded text-sm overflow-auto">
              {JSON.stringify(step.output_data, null, 2)}
            </pre>
          </CardContent>
        </Card>
      )}
    </div>
  );
}

function PendingStepView({ step }: CurrentStepDetailProps) {
  return (
    <div className="space-y-4">
      <div>
        <h2 className="text-xl font-bold">{step.name}</h2>
        <p className="text-muted-foreground">{step.description}</p>
      </div>
      <p className="text-sm text-muted-foreground">This step is pending execution.</p>
    </div>
  );
}

export function CurrentStepDetail({ step, executionId, onUpdate }: CurrentStepDetailProps) {
  if (step.status === 'awaiting_approval') {
    return <ApprovalGateView step={step} executionId={executionId} onUpdate={onUpdate} />;
  }

  if (step.status === 'running') {
    return <RunningStepView step={step} executionId={executionId} onUpdate={onUpdate} />;
  }

  if (step.status === 'completed') {
    return <CompletedStepView step={step} executionId={executionId} onUpdate={onUpdate} />;
  }

  return <PendingStepView step={step} executionId={executionId} onUpdate={onUpdate} />;
}
