// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import { Routes, Route } from 'react-router-dom';
import { AppLayout } from './AppLayout';

vi.mock('../ai/AmaniChatBubble', () => ({
  AmaniChatBubble: () => <div>Chat Bubble</div>,
}));

describe('AppLayout', () => {
  it('renders layout with nested route content', () => {
    window.history.pushState({}, 'Test', '/');
    render(
      <Routes>
        <Route element={<AppLayout />}>
          <Route path="/" element={<div>Child Content</div>} />
        </Route>
      </Routes>
    );

    expect(screen.getByText('Child Content')).toBeInTheDocument();
    expect(screen.getByText('Chat Bubble')).toBeInTheDocument();
  });
});
