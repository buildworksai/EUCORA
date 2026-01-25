// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render } from '@/test/utils';
import { ScrollArea, ScrollBar } from './scroll-area';

describe('ScrollArea', () => {
  it('renders scroll area with children', () => {
    const { container } = render(
      <ScrollArea>
        <div>Test Content</div>
      </ScrollArea>
    );
    expect(container.querySelector('[class*="overflow-hidden"]')).toBeInTheDocument();
  });

  it('renders scroll bar', () => {
    const { container } = render(<ScrollBar />);
    expect(container.querySelector('[class*="touch-none"]')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<ScrollArea className="custom-scroll" />);
    const scrollArea = container.querySelector('[class*="custom-scroll"]');
    expect(scrollArea).toBeInTheDocument();
  });
});
