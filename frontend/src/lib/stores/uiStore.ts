/**
 * Global UI state (theme, sidebar, notifications).
 * 
 * Zustand is the ONLY allowed client state container (Redux banned).
 */
import { create } from 'zustand';

interface UIState {
    theme: 'light' | 'dark' | 'system';
    sidebarOpen: boolean;
    toggleSidebar: () => void;
    setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

// Load theme from localStorage on initialization
const getStoredTheme = (): 'light' | 'dark' | 'system' => {
    if (typeof window === 'undefined') return 'system';
    try {
        const stored = localStorage.getItem('eucora-theme');
        if (stored === 'light' || stored === 'dark' || stored === 'system') {
            return stored;
        }
    } catch {
        // localStorage may be unavailable
    }
    return 'system';
};

// Load sidebar state from localStorage
const getStoredSidebarOpen = (): boolean => {
    if (typeof window === 'undefined') return true;
    try {
        const stored = localStorage.getItem('eucora-sidebar-open');
        return stored !== 'false'; // Default to true
    } catch {
        return true;
    }
};

export const useUIStore = create<UIState>((set) => ({
    theme: getStoredTheme(),
    sidebarOpen: getStoredSidebarOpen(),
    toggleSidebar: () => {
        set((state) => {
            const newState = { sidebarOpen: !state.sidebarOpen };
            try {
                localStorage.setItem('eucora-sidebar-open', String(newState.sidebarOpen));
            } catch {
                // Ignore localStorage errors
            }
            return newState;
        });
    },
    setTheme: (theme) => {
        set({ theme });
        try {
            localStorage.setItem('eucora-theme', theme);
        } catch {
            // Ignore localStorage errors
        }
    },
}));
