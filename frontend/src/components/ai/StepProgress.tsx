// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Step Progress Component for Workflow Visualization.
 *
 * Displays a list of workflow steps with status indicators.
 */
import { CheckCircle, Loader2, AlertCircle, Circle, XCircle } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';
import type { WorkflowStep } from '@/routes/ai/contracts';

interface StepProgressProps {
  steps: WorkflowStep[];
  currentIndex: number;
}

function formatDuration(startedAt?: string, completedAt?: string): string {
  if (!startedAt || !completedAt) return '';
  const start = new Date(startedAt);
  const end = new Date(completedAt);
  const seconds = Math.floor((end.getTime() - start.getTime()) / 1000);
  if (seconds < 60) return `${seconds}s`;
  const minutes = Math.floor(seconds / 60);
  return `${minutes}m ${seconds % 60}s`;
}

export function StepProgress({ steps, currentIndex }: StepProgressProps) {
  return (
    <div className="space-y-2">
      {steps.map((step, index) => {
        const isCurrent = index === currentIndex;
        const isCompleted = step.status === 'completed';
        const isRunning = step.status === 'running';
        const isAwaitingApproval = step.status === 'awaiting_approval';
        const isFailed = step.status === 'failed';

        return (
          <div
            key={step.id}
            className={cn(
              'flex items-start gap-3 p-3 rounded-lg transition-colors',
              isCurrent && 'bg-eucora-teal/10 border border-eucora-teal/30',
              isCompleted && 'opacity-60',
            )}
          >
            {/* Status Icon */}
            <div className="flex-shrink-0 mt-0.5">
              {isCompleted && <CheckCircle className="w-5 h-5 text-green-500" />}
              {isRunning && <Loader2 className="w-5 h-5 text-eucora-teal animate-spin" />}
              {isAwaitingApproval && <AlertCircle className="w-5 h-5 text-yellow-500" />}
              {isFailed && <XCircle className="w-5 h-5 text-red-500" />}
              {step.status === 'pending' && <Circle className="w-5 h-5 text-muted-foreground" />}
            </div>

            {/* Step Info */}
            <div className="flex-1 min-w-0">
              <p className="font-medium text-sm">{step.name}</p>
              <p className="text-xs text-muted-foreground line-clamp-2">{step.description}</p>

              {/* Status Badge */}
              {isAwaitingApproval && (
                <Badge className="mt-1 bg-yellow-500/20 text-yellow-600">Awaiting Your Approval</Badge>
              )}
            </div>

            {/* Duration */}
            {step.completed_at && step.started_at && (
              <span className="text-xs text-muted-foreground">{formatDuration(step.started_at, step.completed_at)}</span>
            )}
          </div>
        );
      })}
    </div>
  );
}
