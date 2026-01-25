/**
 * API client for Django backend with CSRF protection, error handling, and retry logic.
 */
import { toast } from 'sonner';

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Get or generate correlation ID for request tracing.
 */
function getCorrelationId(): string {
  // Try to get from sessionStorage
  let correlationId = sessionStorage.getItem('correlation_id');

  if (!correlationId) {
    // Generate new UUID v4
    correlationId = 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, function(c) {
      const r = (Math.random() * 16) | 0;
      const v = c === 'x' ? r : (r & 0x3) | 0x8;
      return v.toString(16);
    });
    sessionStorage.setItem('correlation_id', correlationId);
  }

  return correlationId;
}

/**
 * Get CSRF token from cookie (set by Django) or fetch from API.
 */
let csrfTokenCache: string | null = null;

async function getCsrfToken(): Promise<string | null> {
  // First, try to get from cookie
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  if (match) {
    csrfTokenCache = match[1];
    return csrfTokenCache;
  }

  // If not in cookie and we have a cached token, use it
  if (csrfTokenCache) {
    return csrfTokenCache;
  }

  // Try to fetch from API endpoint (for development/mock auth scenarios)
  try {
    // API_BASE_URL already includes /api/v1, so use it directly
    const csrfEndpoint = `${API_BASE_URL}/admin/csrf-token`;
    const response = await fetch(csrfEndpoint, {
      method: 'GET',
      credentials: 'include',
    });

    if (response.ok) {
      const data = await response.json();
      csrfTokenCache = data.csrf_token || null;
      return csrfTokenCache;
    }
  } catch (error) {
    // Silently fail - CSRF token might not be needed for GET requests
    console.debug('Failed to fetch CSRF token:', error);
  }

  return null;
}

/**
 * Retry configuration for transient failures.
 */
const RETRY_CONFIG = {
  maxRetries: 3,
  retryDelay: 1000, // ms
  retryableStatuses: [408, 429, 500, 502, 503, 504],
};

/**
 * Sleep utility for retry delays.
 */
function sleep(ms: number): Promise<void> {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

/**
 * Check if error is retryable based on status code.
 */
function isRetryable(status: number): boolean {
  return RETRY_CONFIG.retryableStatuses.includes(status);
}

/**
 * Generic fetch wrapper with Django session credentials, retry logic, and error handling.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {},
  retryCount = 0
): Promise<T> {
  const csrfToken = await getCsrfToken();
  const isMutation = options.method && options.method !== 'GET';

  // Normalize endpoint - ensure it starts with / and handle API_BASE_URL properly
  let normalizedEndpoint = endpoint.startsWith('/') ? endpoint : `/${endpoint}`;

  // If API_BASE_URL already includes /api/v1, don't add it again
  let fullUrl: string;
  if (API_BASE_URL.includes('/api/v1')) {
    // Remove /api/v1 from endpoint if present
    if (normalizedEndpoint.startsWith('/api/v1')) {
      normalizedEndpoint = normalizedEndpoint.replace('/api/v1', '');
    }
    fullUrl = `${API_BASE_URL}${normalizedEndpoint}`;
  } else {
    // API_BASE_URL doesn't have /api/v1, add it if endpoint doesn't have it
    if (!normalizedEndpoint.startsWith('/api/v1')) {
      normalizedEndpoint = `/api/v1${normalizedEndpoint}`;
    }
    fullUrl = `${API_BASE_URL}${normalizedEndpoint}`;
  }

  try {
    const response = await fetch(fullUrl, {
      ...options,
      credentials: 'include', // Send session cookies
      headers: {
        'Content-Type': 'application/json',
        'X-Correlation-ID': getCorrelationId(),
        ...(csrfToken && isMutation ? { 'X-CSRFToken': csrfToken } : {}),
        ...options.headers,
      },
    });

    // Handle retryable errors
    if (!response.ok && isRetryable(response.status) && retryCount < RETRY_CONFIG.maxRetries) {
      const delay = RETRY_CONFIG.retryDelay * Math.pow(2, retryCount); // Exponential backoff
      await sleep(delay);
      return apiRequest<T>(endpoint, options, retryCount + 1);
    }

    // Handle non-retryable errors
    if (!response.ok) {
      let errorMessage = `Request failed: HTTP ${response.status}`;
      let errorDetail: string | null = null;

      try {
        const errorData = await response.json();
        errorDetail = errorData.detail || errorData.error || null;
        errorMessage = errorDetail || errorMessage;
      } catch {
        // If response is not JSON, use status text
        errorMessage = response.statusText || errorMessage;
      }

      // Handle authentication errors properly
      if (response.status === 401) {
        // Unauthorized - session expired or invalid
        // Clear auth state and redirect to login
        try {
          const { useAuthStore } = await import('@/lib/stores/authStore');
          const store = useAuthStore.getState();
          if (store.isAuthenticated) {
            await store.logout();
            // Redirect to login
            if (typeof window !== 'undefined' && window.location.pathname !== '/login') {
              window.location.href = '/login';
            }
          }
        } catch (error) {
          console.error('Failed to handle 401 error:', error);
        }
        // Don't show toast for 401 - handled by redirect
        throw new Error('Session expired. Please log in again.');
      }

      // Don't show toast for 404 (handled by components)
      if (response.status !== 404) {
        toast.error(errorMessage, {
          description: errorDetail && errorDetail !== errorMessage ? errorDetail : undefined,
        });
      }

      throw new Error(errorMessage);
    }

    // Handle empty responses (204 No Content)
    if (response.status === 204) {
      return {} as T;
    }

    return response.json();
  } catch (error) {
    // Handle network errors
    if (error instanceof TypeError && error.message.includes('fetch')) {
      const networkError = 'Network error. Please check your connection.';
      if (retryCount === 0) {
        toast.error(networkError);
      }
      throw new Error(networkError);
    }

    // Re-throw other errors
    throw error;
  }
}

export const api = {
  get: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, data: unknown) =>
    apiRequest<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data: unknown) =>
    apiRequest<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  patch: <T>(endpoint: string, data: unknown) =>
    apiRequest<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: 'DELETE' }),
  // File upload support
  postFormData: <T>(endpoint: string, formData: FormData) =>
    apiRequest<T>(endpoint, {
      method: 'POST',
      body: formData,
      headers: {
        // Don't set Content-Type for FormData (browser will set it with boundary)
      },
    }),
};
