// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { EmptyState } from './empty-state';
import { Package } from 'lucide-react';

describe('EmptyState', () => {
  it('renders title and description', () => {
    render(
      <EmptyState
        title="No Items"
        description="There are no items to display"
      />
    );
    expect(screen.getByText('No Items')).toBeInTheDocument();
    expect(screen.getByText('There are no items to display')).toBeInTheDocument();
  });

  it('renders icon when provided', () => {
    const { container } = render(
      <EmptyState
        icon={Package}
        title="No Packages"
        description="No packages found"
      />
    );
    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });

  it('renders action button when provided', async () => {
    const handleClick = vi.fn();
    const user = userEvent.setup();
    render(
      <EmptyState
        title="No Items"
        description="Add an item"
        action={{
          label: 'Add Item',
          onClick: handleClick,
        }}
      />
    );
    
    const button = screen.getByRole('button', { name: /add item/i });
    expect(button).toBeInTheDocument();
    
    await user.click(button);
    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('does not render action button when not provided', () => {
    render(
      <EmptyState
        title="No Items"
        description="No items"
      />
    );
    const button = screen.queryByRole('button');
    expect(button).not.toBeInTheDocument();
  });
});

