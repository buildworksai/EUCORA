// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Workflow Execution Component.
 *
 * Main component for displaying workflow execution with 3-panel layout:
 * - Left: Step progress
 * - Center: Current step detail
 * - Right: Policy context panel
 */
import { useWorkflowExecution } from '@/lib/api/hooks/useWorkflow';
import { StepProgress } from './StepProgress';
import { CurrentStepDetail } from './CurrentStepDetail';
import { PolicyContextPanel } from './PolicyContextPanel';
import { Skeleton } from '@/components/ui/skeleton';

interface WorkflowExecutionProps {
  executionId: string;
}

export function WorkflowExecution({ executionId }: WorkflowExecutionProps) {
  const { data: execution, isLoading, refetch } = useWorkflowExecution(executionId);

  if (isLoading) {
    return (
      <div className="flex h-full">
        <div className="w-80 border-r p-4">
          <Skeleton className="h-8 w-32 mb-4" />
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <Skeleton key={i} className="h-20 w-full" />
            ))}
          </div>
        </div>
        <div className="flex-1 p-6">
          <Skeleton className="h-64 w-full" />
        </div>
        <div className="w-96 border-l p-4">
          <Skeleton className="h-8 w-32 mb-4" />
          <div className="space-y-2">
            {[1, 2].map((i) => (
              <Skeleton key={i} className="h-32 w-full" />
            ))}
          </div>
        </div>
      </div>
    );
  }

  if (!execution) {
    return <div className="p-6">Workflow execution not found</div>;
  }

  const currentStep = execution.steps[execution.current_step_index];

  return (
    <div className="flex h-full">
      {/* Left: Step Progress */}
      <div className="w-80 border-r p-4">
        <h3 className="font-semibold mb-4">Workflow Steps</h3>
        <StepProgress steps={execution.steps} currentIndex={execution.current_step_index} />
      </div>

      {/* Center: Current Step Detail */}
      <div className="flex-1 p-6">
        {currentStep ? (
          <CurrentStepDetail step={currentStep} executionId={executionId} onUpdate={() => refetch()} />
        ) : (
          <div>No current step</div>
        )}
      </div>

      {/* Right: Policy Context */}
      <div className="w-96 border-l p-4">
        <h3 className="font-semibold mb-4">Policies Considered</h3>
        <PolicyContextPanel policies={execution.policy_context} />
      </div>
    </div>
  );
}
