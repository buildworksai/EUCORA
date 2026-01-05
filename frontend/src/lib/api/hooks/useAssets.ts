/**
 * TanStack Query hooks for asset inventory (CMDB).
 */
import { useQuery } from '@tanstack/react-query';
import { api } from '../client';

export interface Asset {
  id: string;
  name: string;
  type: 'Laptop' | 'Desktop' | 'Virtual Machine' | 'Mobile' | 'Server';
  os: string;
  location: string;
  status: 'Active' | 'Inactive' | 'Retired' | 'Maintenance';
  compliance_score: number;
  last_checkin: string;
  owner: string;
  serial_number?: string;
  ip_address?: string;
  disk_encryption?: boolean;
  firewall_enabled?: boolean;
  dex_score?: number;
  boot_time?: number;
  carbon_footprint?: number;
  user_sentiment?: 'Positive' | 'Neutral' | 'Negative';
  installed_apps?: Array<{
    id: string;
    name: string;
    version: string;
    vendor: string;
  }>;
}

export interface AssetListResponse {
  assets: Asset[];
  total: number;
  page: number;
  page_size: number;
}

export interface AssetFilters {
  type?: string;
  os?: string;
  status?: string;
  location?: string;
  owner?: string;
  page?: number;
  page_size?: number;
  search?: string;
}

/**
 * Fetch asset inventory with pagination and filters.
 */
export function useAssets(filters?: AssetFilters) {
  return useQuery({
    queryKey: ['assets', filters],
    queryFn: async () => {
      const params = new URLSearchParams();
      if (filters?.type) params.append('type', filters.type);
      if (filters?.os) params.append('os', filters.os);
      if (filters?.status) params.append('status', filters.status);
      if (filters?.location) params.append('location', filters.location);
      if (filters?.owner) params.append('owner', filters.owner);
      if (filters?.page) params.append('page', filters.page.toString());
      if (filters?.page_size) params.append('page_size', filters.page_size.toString());
      if (filters?.search) params.append('search', filters.search);

      const queryString = params.toString();
      const response = await api.get<AssetListResponse>(
        `/assets/${queryString ? `?${queryString}` : ''}`
      );
      return response;
    },
    staleTime: 60000, // 1 minute
    refetchInterval: 300000, // Poll every 5 minutes
  });
}

/**
 * Fetch single asset by ID.
 */
export function useAsset(assetId: string) {
  return useQuery({
    queryKey: ['asset', assetId],
    queryFn: async () => {
      return api.get<Asset>(`/assets/${assetId}/`);
    },
    enabled: !!assetId,
    staleTime: 60000,
  });
}

