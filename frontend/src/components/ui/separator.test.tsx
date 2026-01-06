// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render } from '@/test/utils';
import { Separator } from './separator';

describe('Separator', () => {
  it('renders horizontal separator by default', () => {
    const { container } = render(<Separator />);
    const separator = container.querySelector('[class*="h-[1px]"]');
    expect(separator).toBeInTheDocument();
  });

  it('renders vertical separator when orientation is vertical', () => {
    const { container } = render(<Separator orientation="vertical" />);
    const separator = container.querySelector('[class*="w-[1px]"]');
    expect(separator).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(<Separator className="custom-separator" />);
    const separator = container.querySelector('[class*="custom-separator"]');
    expect(separator).toBeInTheDocument();
  });
});

