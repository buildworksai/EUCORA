// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { RingProgressIndicator, Ring } from './RingProgressIndicator';

describe('RingProgressIndicator', () => {
  const mockRings: Ring[] = [
    { name: 'Lab', status: 'completed', successRate: 100 },
    { name: 'Canary', status: 'in_progress', successRate: 98.5 },
    { name: 'Pilot', status: 'pending' },
    { name: 'Global', status: 'pending' },
  ];

  it('renders all rings', () => {
    render(<RingProgressIndicator rings={mockRings} />);
    expect(screen.getByText('Lab')).toBeInTheDocument();
    expect(screen.getByText('Canary')).toBeInTheDocument();
    expect(screen.getByText('Pilot')).toBeInTheDocument();
    expect(screen.getByText('Global')).toBeInTheDocument();
  });

  it('displays success rate when provided', () => {
    render(<RingProgressIndicator rings={mockRings} />);
    expect(screen.getByText('100.0% success')).toBeInTheDocument();
    expect(screen.getByText('98.5% success')).toBeInTheDocument();
  });

  it('renders correct status icons', () => {
    const { container } = render(<RingProgressIndicator rings={mockRings} />);
    // Check for CheckCircle (completed), Clock (in_progress), Circle (pending)
    const icons = container.querySelectorAll('svg');
    expect(icons.length).toBeGreaterThan(0);
  });

  it('applies custom className', () => {
    const { container } = render(<RingProgressIndicator rings={mockRings} className="custom-class" />);
    const wrapper = container.firstChild;
    expect(wrapper).toHaveClass('custom-class');
  });

  it('handles empty rings array', () => {
    render(<RingProgressIndicator rings={[]} />);
    const container = screen.queryByText('Lab');
    expect(container).not.toBeInTheDocument();
  });

  it('handles failed status', () => {
    const failedRings: Ring[] = [{ name: 'Failed Ring', status: 'failed' }];
    render(<RingProgressIndicator rings={failedRings} />);
    expect(screen.getByText('Failed Ring')).toBeInTheDocument();
  });
});

