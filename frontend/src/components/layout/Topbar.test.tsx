// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import { Topbar } from './Topbar';

const navigateMock = vi.fn();
const logoutMock = vi.fn().mockResolvedValue(undefined);

vi.mock('react-router-dom', async () => {
  const actual = await vi.importActual<typeof import('react-router-dom')>('react-router-dom');
  return {
    ...actual,
    useNavigate: () => navigateMock,
  };
});

vi.mock('@/lib/stores/uiStore', () => ({
  useUIStore: () => ({
    toggleSidebar: vi.fn(),
    setTheme: vi.fn(),
  }),
}));

vi.mock('@/lib/stores/authStore', () => ({
  useAuthStore: () => ({
    user: {
      id: '1',
      email: 'admin@eucora.com',
      firstName: 'Admin',
      lastName: 'User',
      role: 'admin',
      department: 'IT',
      isActive: true,
      permissions: [],
    },
    logout: logoutMock,
  }),
}));

describe('Topbar', () => {
  it('opens user menu and logs out', async () => {
    const user = userEvent.setup();
    render(<Topbar />);

    await user.click(screen.getByText('Admin User'));
    await user.click(screen.getByText('Sign Out'));

    expect(logoutMock).toHaveBeenCalled();
    expect(navigateMock).toHaveBeenCalledWith('/login');
  });
});
