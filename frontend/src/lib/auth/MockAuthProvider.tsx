import { createContext, useContext, useState, ReactNode } from 'react';

/**
 * Interface definition for Authentication Context
 */
export interface AuthContextType {
    isAuthenticated: boolean;
    user: {
        name: string;
        username: string;
    } | null;
    login: () => Promise<void>;
    logout: () => Promise<void>;
}

const MockAuthContext = createContext<AuthContextType | undefined>(undefined);

export function MockAuthProvider({ children }: { children: ReactNode }) {
    const [user, setUser] = useState<{ name: string; username: string } | null>(null);

    const login = async () => {
        console.log('[MockAuth] Logging in...');
        try {
            // For mock auth, we'll use the admin user we created
            // In a real scenario, this would use MSAL
            const response = await fetch(`${import.meta.env.VITE_API_URL}/auth/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                credentials: 'include',
                body: JSON.stringify({
                    username: 'admin',
                    password: 'admin123',
                }),
            });

            if (response.ok) {
                const data = await response.json();
                setUser({
                    name: `${data.user?.first_name || ''} ${data.user?.last_name || ''}`.trim() || 'Admin User',
                    username: data.user?.username || 'admin@eucora.com',
                });
            } else {
                // Fallback to mock user if backend auth fails
                setUser({
                    name: 'Mock User',
                    username: 'mockuser@eucora.com',
                });
            }
        } catch (error) {
            console.error('[MockAuth] Login failed, using mock user:', error);
            // Fallback to mock user
            setUser({
                name: 'Mock User',
                username: 'mockuser@eucora.com',
            });
        }
    };

    const logout = async () => {
        console.log('[MockAuth] Logging out...');
        setUser(null);
    };

    const value = {
        isAuthenticated: !!user,
        user,
        login,
        logout,
    };

    return <MockAuthContext.Provider value={value}>{children}</MockAuthContext.Provider>;
}

// eslint-disable-next-line react-refresh/only-export-components
export function useMockAuth() {
    const context = useContext(MockAuthContext);
    if (context === undefined) {
        throw new Error('useMockAuth must be used within a MockAuthProvider');
    }
    return context;
}
