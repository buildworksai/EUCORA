// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render } from '@/test/utils';
import { ThemeProvider } from './ThemeProvider';

vi.mock('@/lib/stores/uiStore', () => ({
  useUIStore: () => ({ theme: 'dark' }),
}));

describe('ThemeProvider', () => {
  it('applies theme class to root', () => {
    render(
      <ThemeProvider>
        <div>child</div>
      </ThemeProvider>
    );

    expect(document.documentElement.classList.contains('dark')).toBe(true);
  });
});
