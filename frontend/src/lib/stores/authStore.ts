// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Zustand store for session-based authentication state.
 */
import { create } from 'zustand';
import { persist, createJSONStorage } from 'zustand/middleware';
import type { User, LoginCredentials, MOCK_USERS } from '@/types/auth';
import { MOCK_USERS as mockUsers, DEFAULT_PERMISSIONS } from '@/types/auth';

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
            const mockUser = mockUsers[credentials.email];
            
            if (mockUser && mockUser.password === credentials.password) {
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
        const { sessionExpiresAt } = get();
        
        if (sessionExpiresAt) {
          const expiresAt = new Date(sessionExpiresAt);
          if (expiresAt < new Date()) {
            await get().logout();
            return;
          }
        }
        
        // Optionally validate session with backend
        const isMock = import.meta.env.VITE_USE_MOCK_AUTH === 'true';
        if (!isMock && get().isAuthenticated) {
          try {
            const response = await fetch(`${API_BASE_URL}/api/v1/auth/me`, {
              credentials: 'include',
            });
            
            if (!response.ok) {
              await get().logout();
            }
          } catch {
            // Keep session if network error (offline support)
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

