// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { RiskScoreBadge } from './RiskScoreBadge';

describe('RiskScoreBadge', () => {
  it('renders "Not Scored" when score is null', () => {
    render(<RiskScoreBadge score={null} />);
    expect(screen.getByText('Not Scored')).toBeInTheDocument();
  });

  it('renders low risk badge for score <= 30', () => {
    render(<RiskScoreBadge score={25} />);
    const badge = screen.getByText(/25 - Low Risk/i);
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('text-eucora-green');
  });

  it('renders medium risk badge for score 31-50', () => {
    render(<RiskScoreBadge score={45} />);
    const badge = screen.getByText(/45 - Medium Risk/i);
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('text-eucora-gold');
  });

  it('renders high risk badge for score > 50', () => {
    render(<RiskScoreBadge score={75} />);
    const badge = screen.getByText(/75 - High Risk \(CAB Required\)/i);
    expect(badge).toBeInTheDocument();
    expect(badge).toHaveClass('bg-eucora-red');
  });

  it('renders correct label for boundary values', () => {
    const { rerender } = render(<RiskScoreBadge score={30} />);
    expect(screen.getByText(/30 - Low Risk/i)).toBeInTheDocument();

    rerender(<RiskScoreBadge score={50} />);
    expect(screen.getByText(/50 - Medium Risk/i)).toBeInTheDocument();

    rerender(<RiskScoreBadge score={51} />);
    expect(screen.getByText(/51 - High Risk \(CAB Required\)/i)).toBeInTheDocument();
  });
});
