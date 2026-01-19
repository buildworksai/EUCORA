/**
 * TanStack Query hooks for audit trail events.
 */
import { useQuery } from '@tanstack/react-query';
import { api } from '../client';

export interface DeploymentEvent {
  id: number;
  correlation_id: string;
  event_type: string;
  event_data: Record<string, unknown>;
  actor: string;
  created_at: string;
}

export interface EventListResponse {
  events: DeploymentEvent[];
}

export interface EventFilters {
  correlation_id?: string;
  event_type?: string;
  start_date?: string;
  end_date?: string;
  actor?: string;
}

/**
 * Fetch deployment events with optional filters.
 */
export function useEvents(filters?: EventFilters) {
  return useQuery({
    queryKey: ['events', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.correlation_id) params.append('correlation_id', filters.correlation_id);
      if (filters?.event_type) params.append('event_type', filters.event_type);
      if (filters?.start_date) params.append('start_date', filters.start_date);
      if (filters?.end_date) params.append('end_date', filters.end_date);
      if (filters?.actor) params.append('actor', filters.actor);

      const queryString = params.toString();
      const response = await api.get<EventListResponse>(
        `/events/list${queryString ? `?${queryString}` : ''}`
      );
      return response.events;
    },
    staleTime: 180000, // 3 minutes
    refetchInterval: 300000, // Poll every 5 minutes for new events
  });
}

