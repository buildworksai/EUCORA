// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render, screen } from '@testing-library/react';
import { Alert, AlertTitle, AlertDescription } from './alert';

describe('Alert', () => {
  it('renders alert with default variant', () => {
    render(
      <Alert>
        <AlertDescription>Test alert</AlertDescription>
      </Alert>
    );
    expect(screen.getByRole('alert')).toBeInTheDocument();
    expect(screen.getByText('Test alert')).toBeInTheDocument();
  });

  it('renders alert with destructive variant', () => {
    render(
      <Alert variant="destructive">
        <AlertDescription>Error alert</AlertDescription>
      </Alert>
    );
    const alert = screen.getByRole('alert');
    expect(alert).toBeInTheDocument();
    expect(alert).toHaveClass('border-destructive/50');
  });

  it('renders alert with title and description', () => {
    render(
      <Alert>
        <AlertTitle>Alert Title</AlertTitle>
        <AlertDescription>Alert description text</AlertDescription>
      </Alert>
    );
    expect(screen.getByText('Alert Title')).toBeInTheDocument();
    expect(screen.getByText('Alert description text')).toBeInTheDocument();
  });

  it('accepts custom className', () => {
    render(
      <Alert className="custom-class">
        <AlertDescription>Test</AlertDescription>
      </Alert>
    );
    expect(screen.getByRole('alert')).toHaveClass('custom-class');
  });

  it('renders with icon slot', () => {
    const TestIcon = () => <svg data-testid="test-icon" />;
    render(
      <Alert>
        <TestIcon />
        <AlertDescription>Alert with icon</AlertDescription>
      </Alert>
    );
    expect(screen.getByTestId('test-icon')).toBeInTheDocument();
    expect(screen.getByText('Alert with icon')).toBeInTheDocument();
  });
});
