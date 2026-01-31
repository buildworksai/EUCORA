// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Workflow Execution Page.
 *
 * Displays workflow execution with full visualization.
 */
import { useParams } from 'react-router-dom';
import { WorkflowExecution as WorkflowExecutionComponent } from '@/components/ai/WorkflowExecution';

export default function WorkflowPage() {
  const { executionId } = useParams<{ executionId: string }>();

  if (!executionId) {
    return <div className="p-6">Invalid execution ID</div>;
  }

  return (
    <div className="h-screen flex flex-col">
      <div className="border-b p-4">
        <h1 className="text-2xl font-bold">Workflow Execution</h1>
      </div>
      <div className="flex-1 overflow-hidden">
        <WorkflowExecutionComponent executionId={executionId} />
      </div>
    </div>
  );
}
