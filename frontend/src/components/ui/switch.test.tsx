// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { Switch } from './switch';

describe('Switch', () => {
  it('renders switch component', () => {
    render(<Switch />);
    const switchElement = screen.getByRole('switch');
    expect(switchElement).toBeInTheDocument();
  });

  it('toggles switch state when clicked', async () => {
    const user = userEvent.setup();
    render(<Switch />);
    const switchElement = screen.getByRole('switch');
    
    expect(switchElement).not.toBeChecked();
    await user.click(switchElement);
    expect(switchElement).toBeChecked();
  });

  it('is disabled when disabled prop is true', () => {
    render(<Switch disabled />);
    const switchElement = screen.getByRole('switch');
    expect(switchElement).toBeDisabled();
  });

  it('handles onChange events', async () => {
    const handleChange = vi.fn();
    const user = userEvent.setup();
    render(<Switch onCheckedChange={handleChange} />);
    
    const switchElement = screen.getByRole('switch');
    await user.click(switchElement);
    
    expect(handleChange).toHaveBeenCalledWith(true);
  });

  it('applies custom className', () => {
    const { container } = render(<Switch className="custom-switch" />);
    const switchElement = container.querySelector('[role="switch"]');
    expect(switchElement).toHaveClass('custom-switch');
  });
});

