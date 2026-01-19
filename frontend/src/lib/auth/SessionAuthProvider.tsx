// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Session-based authentication provider using Zustand store.
 */
import { createContext, useContext, useEffect, ReactNode } from 'react';
import { useAuthStore } from '@/lib/stores/authStore';
import type { User, LoginCredentials } from '@/types/auth';

export interface SessionAuthContextType {
  isAuthenticated: boolean;
  isLoading: boolean;
  user: User | null;
  error: string | null;
  login: (credentials: LoginCredentials) => Promise<boolean>;
  logout: () => Promise<void>;
  clearError: () => void;
}

const SessionAuthContext = createContext<SessionAuthContextType | undefined>(undefined);

export function SessionAuthProvider({ children }: { children: ReactNode }) {
  const {
    user,
    isAuthenticated,
    isLoading,
    error,
    login,
    logout,
    clearError,
    checkSession,
  } = useAuthStore();

  // Check session validity on mount and periodically
  useEffect(() => {
    checkSession();
    
    const interval = setInterval(() => {
      checkSession();
    }, 5 * 60 * 1000); // Check every 5 minutes
    
    return () => clearInterval(interval);
  }, [checkSession]);

  const value: SessionAuthContextType = {
    isAuthenticated,
    isLoading,
    user,
    error,
    login,
    logout,
    clearError,
  };

  return (
    <SessionAuthContext.Provider value={value}>
      {children}
    </SessionAuthContext.Provider>
  );
}

// eslint-disable-next-line react-refresh/only-export-components
export function useSessionAuth() {
  const context = useContext(SessionAuthContext);
  if (context === undefined) {
    throw new Error('useSessionAuth must be used within a SessionAuthProvider');
  }
  return context;
}

