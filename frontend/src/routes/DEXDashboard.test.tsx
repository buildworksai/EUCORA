// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import DEXDashboard from './DEXDashboard';

vi.mock('@tanstack/react-query', async () => {
  const actual = await vi.importActual<typeof import('@tanstack/react-query')>('@tanstack/react-query');
  return {
    ...actual,
    useQuery: () => ({
      data: [
        {
          dexScore: 8,
          bootTime: 30,
          carbonFootprint: 200,
          userSentiment: 'Positive',
        },
      ],
    }),
  };
});

vi.mock('recharts', () => {
  const ChartStub = ({ children }: { children?: React.ReactNode }) => <div>{children}</div>;
  const EmptyStub = () => <div />;
  return {
    BarChart: ChartStub,
    Bar: ChartStub,
    XAxis: EmptyStub,
    YAxis: EmptyStub,
    Tooltip: EmptyStub,
    ResponsiveContainer: ChartStub,
    PieChart: ChartStub,
    Pie: ChartStub,
    Cell: EmptyStub,
    Legend: EmptyStub,
  };
});

describe('DEXDashboard', () => {
  it('renders DEX metrics', () => {
    render(<DEXDashboard />);
    expect(screen.getByText('Digital Employee Experience (DEX)')).toBeInTheDocument();
    expect(screen.getByText(/DEX Score/)).toBeInTheDocument();
  });
});
