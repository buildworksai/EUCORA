// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@/test/utils';
import userEvent from '@testing-library/user-event';
import Settings from './index';

const configureMock = vi.fn((_, options) => options?.onSuccess?.());

vi.mock('@/lib/stores/authStore', () => ({
  useAuthStore: () => ({
    user: {
      id: '1',
      email: 'admin@eucora.com',
      firstName: 'Admin',
      lastName: 'User',
      role: 'admin',
      isActive: true,
      permissions: [],
    },
  }),
}));

vi.mock('@/lib/api/hooks/useAI', () => ({
  useModelProviders: () => ({
    data: {
      providers: [
        {
          id: '1',
          provider_type: 'openai',
          display_name: 'OpenAI',
          model_name: 'gpt-4o',
          is_active: true,
          is_default: true,
          key_configured: true,
        },
      ],
    },
  }),
  useConfigureProvider: () => ({
    mutate: configureMock,
    isPending: false,
  }),
}));

vi.mock('sonner', () => ({
  toast: {
    info: vi.fn(),
    success: vi.fn(),
    error: vi.fn(),
  },
}));

describe('Settings', () => {
  it('renders tabs and integrations', async () => {
    const user = userEvent.setup();
    render(<Settings />);

    expect(screen.getByText('Profile')).toBeInTheDocument();
    expect(screen.getByText('AI Providers')).toBeInTheDocument();
    expect(screen.getByText('Users')).toBeInTheDocument();
    expect(screen.getByText('Integrations')).toBeInTheDocument();

    await user.click(screen.getByText('Integrations'));
    expect(screen.getByText('Microsoft Entra ID')).toBeInTheDocument();
  });

  it('saves AI provider configuration', async () => {
    const user = userEvent.setup();
    render(<Settings />);

    await user.click(screen.getByText('AI Providers'));
    const saveButtons = screen.getAllByRole('button', { name: /save/i });
    await user.click(saveButtons[0]);

    expect(configureMock).toHaveBeenCalled();
  });
});
