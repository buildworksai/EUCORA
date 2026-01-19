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
            retryOnMount: false,
        },
        mutations: {
            retry: 1,
        },
    },
});
