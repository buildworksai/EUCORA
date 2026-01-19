// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { AIApprovalDialog } from './AIApprovalDialog';
import type { AIAgentTask } from '@/lib/api/hooks/useAI';

const approveMock = vi.fn((_, options) => options?.onSuccess?.());
const rejectMock = vi.fn((_, options) => options?.onSuccess?.());
const revisionMock = vi.fn((_, options) =>
  options?.onSuccess?.({ task: { revised_recommendation: 'Updated' } })
);

vi.mock('@/lib/api/hooks/useAI', () => ({
  useApproveTask: () => ({ mutate: approveMock, isPending: false }),
  useRejectTask: () => ({ mutate: rejectMock, isPending: false }),
  useRequestRevision: () => ({ mutate: revisionMock, isPending: false }),
}));

vi.mock('@/lib/hooks/useAuth', () => ({
  useAuth: () => ({
    user: { role: 'admin', is_staff: true },
  }),
}));

vi.mock('sonner', () => ({
  toast: {
    success: vi.fn(),
    error: vi.fn(),
    info: vi.fn(),
  },
}));

const task: AIAgentTask = {
  id: 't1',
  title: 'Task One',
  description: 'Do something',
  agent_type: 'amani',
  task_type: 'ai_recommendation',
  status: 'awaiting_approval',
  created_at: new Date().toISOString(),
  input_data: {},
  output_data: {},
  correlation_id: 'corr-1',
};

describe('AIApprovalDialog', () => {
  it('approves a task', async () => {
    const user = userEvent.setup();
    render(<AIApprovalDialog task={task} open onOpenChange={vi.fn()} />);

    await user.click(screen.getByText('Approve'));
    await user.click(screen.getByText('Confirm Approval'));
    expect(approveMock).toHaveBeenCalled();
  });

  it('rejects a task with reason', async () => {
    const user = userEvent.setup();
    render(<AIApprovalDialog task={task} open onOpenChange={vi.fn()} />);

    await user.click(screen.getByText('Reject'));
    await user.type(screen.getByLabelText('Rejection Reason (Required)'), 'Not ok');
    await user.click(screen.getByText('Confirm Rejection'));
    expect(rejectMock).toHaveBeenCalled();
  });
});
