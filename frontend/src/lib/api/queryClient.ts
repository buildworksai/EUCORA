/**
 * TanStack Query client configuration.
 * 
 * Handles server state (deployments, evidence packs, etc.).
 */
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
    defaultOptions: {
        queries: {
            staleTime: 1000 * 60 * 5, // 5 minutes
            retry: 3,
            refetchOnWindowFocus: false,
            // Suppress authentication errors globally
            retryOnMount: false,
            onError: (error) => {
                // Suppress authentication errors for demo/testing
                const errorMessage = error instanceof Error ? error.message : String(error);
                if (
                    errorMessage.includes('401') ||
                    errorMessage.includes('403') ||
                    errorMessage.includes('Unauthorized') ||
                    errorMessage.includes('Forbidden')
                ) {
                    // Silently ignore authentication errors
                    if (import.meta.env.DEV) {
                        console.debug('Suppressed auth error in query:', errorMessage);
                    }
                    return;
                }
                // Log other errors normally
                console.error('Query error:', error);
            },
        },
        mutations: {
            retry: 1,
            // Suppress authentication errors in mutations
            onError: (error) => {
                const errorMessage = error instanceof Error ? error.message : String(error);
                if (
                    errorMessage.includes('401') ||
                    errorMessage.includes('403') ||
                    errorMessage.includes('Unauthorized') ||
                    errorMessage.includes('Forbidden')
                ) {
                    // Silently ignore authentication errors
                    if (import.meta.env.DEV) {
                        console.debug('Suppressed auth error in mutation:', errorMessage);
                    }
                    return;
                }
                // Log other errors normally
                console.error('Mutation error:', error);
            },
        },
    },
});
