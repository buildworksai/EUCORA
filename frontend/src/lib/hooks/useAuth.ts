// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Custom hook for authentication state and actions.
 * Uses session-based auth via Zustand store.
 */
import { useNavigate } from 'react-router-dom';
import { useAuthStore } from '@/lib/stores/authStore';
import type { LoginCredentials, User } from '@/types/auth';

export interface UseAuthReturn {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  loginAndNavigate: (credentials: LoginCredentials) => Promise<void>;
  logout: () => Promise<void>;
  clearError: () => void;
}

export function useAuth(): UseAuthReturn {
  const navigate = useNavigate();
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    clearError,
  } = useAuthStore();

  const loginAndNavigate = async (credentials: LoginCredentials) => {
    const success = await login(credentials);
    if (success) {
      navigate('/dashboard');
    }
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  return {
    isAuthenticated,
    isLoading,
    user,
    error,
    login,
    loginAndNavigate,
    logout: handleLogout,
    clearError,
  };
}
