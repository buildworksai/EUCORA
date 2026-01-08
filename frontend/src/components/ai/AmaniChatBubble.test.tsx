// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { AmaniChatBubble } from './AmaniChatBubble';

const sendMessageMock = vi.fn().mockResolvedValue({
  conversation_id: 'c1',
  message_id: 'm1',
  response: 'ok',
  requires_action: false,
});

vi.mock('@/lib/api/hooks/useAI', () => ({
  useAmaniChat: () => ({ mutateAsync: sendMessageMock, isPending: false }),
  useConversation: () => ({ data: { conversation_id: 'c1', messages: [] } }),
  useCreateTaskFromMessage: () => ({ mutateAsync: vi.fn().mockResolvedValue({}) }),
  usePendingApprovals: () => ({ data: { pending_approvals: [], total_count: 0 } }),
}));

vi.mock('./AIApprovalDialog', () => ({
  AIApprovalDialog: () => <div>Approval Dialog</div>,
}));

describe('AmaniChatBubble', () => {
  it('opens chat panel and shows header', async () => {
    const user = userEvent.setup();
    render(<AmaniChatBubble />);

    await user.click(screen.getByLabelText('Open Amani chat (Ctrl+K)'));
    expect(screen.getByText('Ask Amani')).toBeInTheDocument();
  });
});
