// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Label } from './label';

describe('Label', () => {
  it('renders label element', () => {
    render(<Label>Test Label</Label>);
    expect(screen.getByText('Test Label')).toBeInTheDocument();
  });

  it('associates with input via htmlFor', () => {
    render(
      <>
        <Label htmlFor="test-input">Test Label</Label>
        <input id="test-input" />
      </>
    );
    const label = screen.getByText('Test Label');
    const input = screen.getByLabelText('Test Label');
    expect(label).toHaveAttribute('for', 'test-input');
    expect(input).toBeInTheDocument();
  });

  it('applies custom className', () => {
    render(<Label className="custom-class">Custom</Label>);
    const label = screen.getByText('Custom');
    expect(label).toHaveClass('custom-class');
  });
});
