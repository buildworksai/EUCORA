// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Zustand store for session-based authentication state.
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User, LoginCredentials } from '@/types/auth';
import { DEFAULT_PERMISSIONS, MOCK_USERS } from '@/types/auth';

interface AuthStore {
  user: User | null;
  isAuthenticated: boolean;
  isLoading: boolean;
  error: string | null;
  sessionExpiresAt: string | null;

  // Actions
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => Promise<void>;
  checkSession: () => Promise<void>;
  clearError: () => void;
  updateUser: (updates: Partial<User>) => void;
}

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export const useAuthStore = create<AuthStore>()(
  persist(
    (set, get) => ({
      user: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
      sessionExpiresAt: null,

      login: async (credentials: LoginCredentials) => {
        set({ isLoading: true, error: null });

        try {
          // Check if we're in mock mode
          const isMock = import.meta.env.VITE_USE_MOCK_AUTH === 'true';

          if (isMock) {
            // Mock authentication
            const mockUser = MOCK_USERS[credentials.email];

            if (mockUser && mockUser.password === credentials.password) {
              // eslint-disable-next-line @typescript-eslint/no-unused-vars
              const { password, ...user } = mockUser;
              const expiresAt = new Date();
              expiresAt.setHours(expiresAt.getHours() + 24);

              set({
                user: { ...user, lastLogin: new Date() },
                isAuthenticated: true,
                isLoading: false,
                sessionExpiresAt: expiresAt.toISOString(),
              });
              return true;
            } else {
              set({
                error: 'Invalid email or password',
                isLoading: false,
              });
              return false;
            }
          }

          // Real API authentication
          const response = await fetch(`${API_BASE_URL}/api/v1/auth/login`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            credentials: 'include',
            body: JSON.stringify({
              email: credentials.email,
              password: credentials.password,
            }),
          });

          if (response.ok) {
            const data = await response.json();
            const user: User = {
              id: data.user.id || '1',
              email: data.user.email || data.user.username,
              firstName: data.user.first_name || 'User',
              lastName: data.user.last_name || '',
              role: data.user.is_superuser ? 'admin' : 'operator',
              isActive: true,
              permissions: data.user.is_superuser
                ? DEFAULT_PERMISSIONS.admin
                : DEFAULT_PERMISSIONS.operator,
              lastLogin: new Date(),
            };

            const expiresAt = new Date();
            expiresAt.setHours(expiresAt.getHours() + 24);

            set({
              user,
              isAuthenticated: true,
              isLoading: false,
              sessionExpiresAt: expiresAt.toISOString(),
            });
            return true;
          } else {
            const errorData = await response.json().catch(() => ({}));
            set({
              error: errorData.error || 'Invalid email or password',
              isLoading: false,
            });
            return false;
          }
        } catch (error) {
          console.error('Login error:', error);
          set({
            error: 'Network error. Please try again.',
            isLoading: false,
          });
          return false;
        }
      },

      logout: async () => {
        try {
          const isMock = import.meta.env.VITE_USE_MOCK_AUTH === 'true';

          if (!isMock) {
            await fetch(`${API_BASE_URL}/api/v1/auth/logout`, {
              method: 'POST',
              credentials: 'include',
            });
          }
        } catch (error) {
          console.error('Logout error:', error);
        } finally {
          set({
            user: null,
            isAuthenticated: false,
            sessionExpiresAt: null,
            error: null,
          });
        }
      },

      checkSession: async () => {
        const { sessionExpiresAt, isAuthenticated } = get();

        // Check local expiration first
        if (sessionExpiresAt) {
          const expiresAt = new Date(sessionExpiresAt);
          if (expiresAt < new Date()) {
            await get().logout();
            return;
          }
        }

        // Always validate session with backend if authenticated
        // This ensures we catch expired sessions even if local expiration hasn't passed
        if (isAuthenticated) {
          const isMock = import.meta.env.VITE_USE_MOCK_AUTH === 'true';

          if (isMock) {
            // In mock mode, just check local expiration
            return;
          }

          try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
              credentials: 'include',
            });

            if (!response.ok) {
              // Session invalid - logout
              await get().logout();
              return;
            }

            // Update user data from backend
            const data = await response.json();
            const user: User = {
              id: data.user.id?.toString() || '1',
              email: data.user.email || data.user.username,
              firstName: data.user.first_name || 'User',
              lastName: data.user.last_name || '',
              role: data.user.is_superuser ? 'admin' : (data.user.is_staff ? 'operator' : 'viewer'),
              isActive: true,
              permissions: data.user.is_superuser
                ? DEFAULT_PERMISSIONS.admin
                : (data.user.is_staff ? DEFAULT_PERMISSIONS.operator : DEFAULT_PERMISSIONS.viewer),
              lastLogin: new Date(),
            };

            set({ user });
          } catch (error) {
            // Network error - keep session for offline support
            // But if it's a 401, logout
            if (error instanceof Error && error.message.includes('401')) {
              await get().logout();
            }
          }
        }
      },

      clearError: () => set({ error: null }),

      updateUser: (updates: Partial<User>) => {
        const { user } = get();
        if (user) {
          set({ user: { ...user, ...updates } });
        }
      },
    }),
    {
      name: 'eucora-auth',
      storage: createJSONStorage(() => sessionStorage),
      partialize: (state) => ({
        user: state.user,
        isAuthenticated: state.isAuthenticated,
        sessionExpiresAt: state.sessionExpiresAt,
      }),
    }
  )
);
