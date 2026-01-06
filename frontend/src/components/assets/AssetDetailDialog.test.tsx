// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { AssetDetailDialog } from './AssetDetailDialog';
import { Asset } from '@/lib/api/hooks/useAssets';

const mockAsset: Asset = {
  id: '1',
  name: 'Test Laptop',
  type: 'Laptop',
  serial_number: 'SN123456',
  status: 'active',
  os_version: 'Windows 11',
  last_seen: '2026-01-06T10:00:00Z',
  compliance_status: 'compliant',
  risk_score: 25,
};

describe('AssetDetailDialog', () => {
  it('does not render when asset is null', () => {
    render(<AssetDetailDialog asset={null} open={true} onOpenChange={vi.fn()} />);
    expect(screen.queryByText('Test Laptop')).not.toBeInTheDocument();
  });

  it('renders asset details when open', () => {
    render(<AssetDetailDialog asset={mockAsset} open={true} onOpenChange={vi.fn()} />);
    expect(screen.getByText('Test Laptop')).toBeInTheDocument();
    expect(screen.getByText('Laptop')).toBeInTheDocument();
    expect(screen.getByText('SN123456')).toBeInTheDocument();
  });

  it('closes dialog when onOpenChange is called', async () => {
    const handleOpenChange = vi.fn();
    const user = userEvent.setup();
    render(<AssetDetailDialog asset={mockAsset} open={true} onOpenChange={handleOpenChange} />);
    
    // Find and click close button
    const closeButton = screen.getByRole('button', { name: /close/i });
    await user.click(closeButton);
    
    expect(handleOpenChange).toHaveBeenCalledWith(false);
  });
});

