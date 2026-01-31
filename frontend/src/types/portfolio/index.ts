// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * TypeScript types for Portfolio Management
 *
 * Corresponds to backend models in apps/portfolio_management/models.py
 */

/**
 * Portfolio - Portfolio Manager's portfolio of applications
 */
export interface Portfolio {
  id: string;
  name: string;
  manager: number;
  manager_name?: string;
  manager_email?: string;
  scope: {
    business_units?: string[];
    geographies?: string[];
    sites?: string[];
    [key: string]: string[] | undefined;
  };
  budget_annual: string; // Decimal as string

  // Cached metrics
  total_applications: number;
  total_licenses_entitled: number;
  total_licenses_consumed: number;
  license_utilization_percent: number;
  health_score: number;
  compliance_score: number;

  // Timestamps
  created_at: string;
  updated_at: string;
}

/**
 * Application Ownership - Maps Application Managers to applications
 */
export interface ApplicationOwnership {
  id: string;
  application: string;
  application_name?: string;
  application_identifier?: string;
  owner: number;
  owner_name?: string;
  owner_email?: string;
  portfolio: string;
  portfolio_name?: string;
  ownership_type: 'PRIMARY' | 'SECONDARY';
  assigned_by: number | null;
  assigned_by_name?: string;
  assigned_at: string;
  is_active: boolean;

  // Timestamps
  created_at: string;
  updated_at: string;
}

/**
 * Application Manager Performance - Time-series performance snapshots
 */
export interface ApplicationManagerPerformance {
  id: string;
  manager: number;
  manager_name?: string;
  portfolio: string | null;
  portfolio_name?: string;

  // Time period
  recorded_at: string;
  period_start: string;
  period_end: string;

  // Deployment metrics
  deployments_total: number;
  deployments_successful: number;
  deployments_failed: number;
  deployments_rolled_back: number;
  success_rate_percent: number;
  avg_deployment_duration_days: number;

  // Health metrics
  applications_total: number;
  applications_healthy: number;
  applications_degraded: number;
  applications_critical: number;
  avg_health_score: number;

  // License metrics
  licenses_entitled: number;
  licenses_consumed: number;
  licenses_wasted: number;
  utilization_percent: number;

  // Incident metrics
  incidents_total: number;
  incidents_resolved: number;
  avg_mttr_hours: number;

  // Composite score
  composite_score: number;

  // Metadata
  calculation_metadata?: Record<string, string | number | boolean | null>;

  // Timestamps
  created_at: string;
}

/**
 * License True-Up Forecast - Vendor ELA renewal forecasts
 */
export interface LicenseTrueUpForecast {
  id: string;
  vendor: string;
  vendor_name?: string;
  portfolio: string | null;
  portfolio_name?: string;

  // Forecast period
  forecast_period: string;
  forecast_generated_at: string;
  forecast_horizon_days: number;

  // Current state
  entitled_quantity_current: number;
  consumed_quantity_current: number;
  utilization_current_percent: number;

  // Forecast
  consumed_quantity_forecast: number;
  consumption_growth_percent: number;
  additional_licenses_needed: number;
  estimated_cost_impact: string; // Decimal as string
  confidence_percent: number;

  // Mitigation
  mitigation_recommendations: MitigationRecommendation[];
  potential_savings: string; // Decimal as string

  // Metadata
  model_version?: string;
  correlation_id?: string;
  input_data_summary?: Record<string, string | number | boolean | null>;
}

export interface MitigationRecommendation {
  strategy: string;
  description: string;
  licenses_saved: number;
  cost_savings: number;
}

/**
 * Packaging Request - Workflow tracking from Application Manager to Packaging Engineer
 */
export interface PackagingRequest {
  id: string;
  application: string;
  application_name?: string;
  requested_by: number;
  requested_by_name?: string;
  assigned_to: number | null;
  assigned_to_name?: string;

  priority: 'URGENT' | 'HIGH' | 'NORMAL' | 'LOW';
  business_justification: string;
  target_platforms: string[];
  special_requirements: string;

  status: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';

  // Timestamps
  created_at: string;
  assigned_at: string | null;
  completed_at: string | null;
  turnaround_time_hours: number | null;
  updated_at: string;
}

/**
 * API Response types
 */
export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface PortfolioMetrics {
  portfolio_id: string;
  total_applications: number;
  total_licenses_entitled: number;
  total_licenses_consumed: number;
  license_utilization_percent: number;
  health_score: number;
  compliance_score: number;
  budget_annual: string;
}

/**
 * Filter types for API queries
 */
export interface PortfolioFilters {
  search?: string;
  ordering?: string;
}

export interface ApplicationOwnershipFilters {
  is_active?: boolean;
  ownership_type?: 'PRIMARY' | 'SECONDARY';
  portfolio?: string;
  owner?: number;
  search?: string;
  ordering?: string;
}

export interface PerformanceFilters {
  manager?: number;
  portfolio?: string;
  period_start?: string;
  period_end?: string;
  ordering?: string;
}

export interface ForecastFilters {
  vendor?: string;
  portfolio?: string;
  forecast_period?: string;
  ordering?: string;
}

export interface PackagingRequestFilters {
  status?: 'PENDING' | 'IN_PROGRESS' | 'COMPLETED' | 'CANCELLED';
  priority?: 'URGENT' | 'HIGH' | 'NORMAL' | 'LOW';
  requested_by?: number;
  assigned_to?: number;
  search?: string;
  ordering?: string;
}
