import { useEffect } from 'react';
import { useUIStore } from '@/lib/stores/uiStore';

export function ThemeProvider({ children }: { children: React.ReactNode }) {
    const { theme } = useUIStore();

    useEffect(() => {
        const root = window.document.documentElement;
        root.classList.remove('light', 'dark');

        if (theme === 'system') {
            const systemTheme = window.matchMedia('(prefers-color-scheme: dark)').matches
                ? 'dark'
                : 'light';
            root.classList.add(systemTheme);
            return;
        }

        root.classList.add(theme);
    }, [theme]);

    return <>{children}</>;
}
