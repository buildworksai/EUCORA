// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { LoadingButton } from './loading-button';

describe('LoadingButton', () => {
  it('renders button with children', () => {
    render(<LoadingButton>Click me</LoadingButton>);
    expect(screen.getByRole('button', { name: /click me/i })).toBeInTheDocument();
  });

  it('shows loading spinner when loading', () => {
    const { container } = render(<LoadingButton loading>Submit</LoadingButton>);
    const spinner = container.querySelector('svg');
    expect(spinner).toBeInTheDocument();
  });

  it('is disabled when loading', () => {
    render(<LoadingButton loading>Submit</LoadingButton>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('is disabled when disabled prop is true', () => {
    render(<LoadingButton disabled>Submit</LoadingButton>);
    const button = screen.getByRole('button');
    expect(button).toBeDisabled();
  });

  it('does not show spinner when not loading', () => {
    const { container } = render(<LoadingButton>Submit</LoadingButton>);
    const spinner = container.querySelector('[class*="animate-spin"]');
    expect(spinner).not.toBeInTheDocument();
  });
});
