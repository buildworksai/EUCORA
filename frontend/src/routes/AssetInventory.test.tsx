// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import AssetInventory from './AssetInventory';

vi.mock('@/lib/api/hooks/useAssets', () => ({
  useAssets: () => ({
    data: {
      assets: [
        {
          id: 'a1',
          name: 'Asset One',
          type: 'Laptop',
          os: 'Windows 11',
          status: 'Active',
          compliance_score: 95,
          location: 'NY',
          owner: 'Alice',
        },
      ],
      total: 1,
    },
    isLoading: false,
    error: null,
  }),
}));

vi.mock('@/components/assets/AssetDetailDialog', () => ({
  AssetDetailDialog: () => <div>Asset Detail</div>,
}));

describe('AssetInventory', () => {
  it('renders asset table', () => {
    render(<AssetInventory />);
    expect(screen.getByText('Global Asset Inventory (CMDB)')).toBeInTheDocument();
    expect(screen.getByText('Asset One')).toBeInTheDocument();
  });
});
