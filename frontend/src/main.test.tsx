// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';

const renderMock = vi.fn();

vi.mock('react-dom/client', () => ({
  default: {
    createRoot: vi.fn(() => ({ render: renderMock })),
  },
  createRoot: vi.fn(() => ({ render: renderMock })),
}));

vi.mock('./App', () => ({
  default: () => <div>App</div>,
}));

describe('main entry', () => {
  it('renders app into root', async () => {
    document.body.innerHTML = '<div id="root"></div>';
    await import('./main');

    expect(renderMock).toHaveBeenCalled();
  });
});
