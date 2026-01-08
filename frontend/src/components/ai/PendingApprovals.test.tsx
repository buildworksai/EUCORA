// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { PendingApprovals } from './PendingApprovals';

const pendingApprovalsMock = vi.fn();

vi.mock('@/lib/api/hooks/useAI', () => ({
  usePendingApprovals: () => pendingApprovalsMock(),
}));

vi.mock('./AIApprovalDialog', () => ({
  AIApprovalDialog: () => <div>Dialog</div>,
}));

describe('PendingApprovals', () => {
  it('renders compact list and handles clicks', async () => {
    pendingApprovalsMock.mockReturnValue({
      data: {
        pending_approvals: [
          {
            id: 't1',
            title: 'Task One',
            created_at: new Date().toISOString(),
            agent_type: 'amani',
          },
        ],
      },
      isLoading: false,
      refetch: vi.fn(),
      isRefetching: false,
    });
    const onTaskClick = vi.fn();
    const user = userEvent.setup();
    render(<PendingApprovals compact onTaskClick={onTaskClick} />);

    await user.click(screen.getByText('Task One'));
    expect(onTaskClick).toHaveBeenCalled();
  });

  it('renders empty state when no tasks', () => {
    pendingApprovalsMock.mockReturnValue({
      data: { pending_approvals: [] },
      isLoading: false,
      refetch: vi.fn(),
      isRefetching: false,
    });
    render(<PendingApprovals compact />);
    expect(screen.getByText('No pending approvals')).toBeInTheDocument();
  });
});
