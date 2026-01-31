// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { usePortfolios, useHighRiskForecasts } from '../../lib/api/hooks/usePortfolioManagement';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Loader2, TrendingUp, TrendingDown, AlertTriangle, Building2, DollarSign } from 'lucide-react';

export function PortfolioManagerDashboard() {
  const { data: portfoliosData, isLoading, error } = usePortfolios();
  const { data: highRiskForecasts } = useHighRiskForecasts();

  if (isLoading) {
    return (
      <div className="flex items-center justify-center h-96">
        <Loader2 className="h-8 w-8 animate-spin text-primary" />
      </div>
    );
  }

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Failed to load portfolios. Please try again.</AlertDescription>
      </Alert>
    );
  }

  const portfolios = portfoliosData?.results || [];

  return (
    <div className="space-y-6 p-6">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Portfolio Management</h1>
          <p className="text-muted-foreground">Manage your application portfolios and track key metrics</p>
        </div>
      </div>

      {/* High-Risk Forecasts Alert */}
      {highRiskForecasts && highRiskForecasts.length > 0 && (
        <Alert className="border-amber-500 bg-amber-50 dark:bg-amber-950">
          <AlertTriangle className="h-4 w-4 text-amber-600" />
          <AlertDescription className="text-amber-900 dark:text-amber-100">
            <strong>{highRiskForecasts.length} high-risk license forecast(s)</strong> require attention.
            Review true-up forecasts for upcoming renewals.
          </AlertDescription>
        </Alert>
      )}

      {/* Portfolio Cards Grid */}
      <div className="grid gap-6 md:grid-cols-2">
        {portfolios.map((portfolio) => (
          <Card key={portfolio.id} className="hover:shadow-lg transition-shadow">
            <CardHeader>
              <div className="flex items-start justify-between">
                <div className="space-y-1">
                  <CardTitle className="text-xl">{portfolio.name}</CardTitle>
                  <p className="text-sm text-muted-foreground">{portfolio.manager_name}</p>
                </div>
                <Building2 className="h-8 w-8 text-muted-foreground" />
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Budget */}
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2">
                  <DollarSign className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Annual Budget</span>
                </div>
                <span className="text-lg font-bold">
                  ${parseFloat(portfolio.budget_annual).toLocaleString()}
                </span>
              </div>

              {/* Applications */}
              <div className="flex items-center justify-between p-3 rounded-lg bg-muted/50">
                <span className="text-sm font-medium">Applications</span>
                <Badge variant="secondary" className="text-base">
                  {portfolio.total_applications}
                </Badge>
              </div>

              {/* License Utilization */}
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <span className="text-sm font-medium">License Utilization</span>
                  <span className="text-sm font-bold">
                    {portfolio.license_utilization_percent.toFixed(1)}%
                  </span>
                </div>
                <div className="h-2 bg-muted rounded-full overflow-hidden">
                  <div
                    className={`h-full transition-all ${
                      portfolio.license_utilization_percent > 90
                        ? 'bg-red-500'
                        : portfolio.license_utilization_percent > 70
                        ? 'bg-green-500'
                        : 'bg-blue-500'
                    }`}
                    style={{ width: `${Math.min(portfolio.license_utilization_percent, 100)}%` }}
                  />
                </div>
                <div className="flex items-center justify-between text-xs text-muted-foreground">
                  <span>{portfolio.total_licenses_consumed.toLocaleString()} consumed</span>
                  <span>{portfolio.total_licenses_entitled.toLocaleString()} entitled</span>
                </div>
              </div>

              {/* Health & Compliance Scores */}
              <div className="grid grid-cols-2 gap-4 pt-2">
                <div className="space-y-1">
                  <div className="flex items-center gap-1">
                    {portfolio.health_score >= 80 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-amber-500" />
                    )}
                    <span className="text-sm font-medium">Health</span>
                  </div>
                  <p className="text-2xl font-bold">{portfolio.health_score.toFixed(1)}</p>
                </div>
                <div className="space-y-1">
                  <div className="flex items-center gap-1">
                    {portfolio.compliance_score >= 90 ? (
                      <TrendingUp className="h-4 w-4 text-green-500" />
                    ) : (
                      <TrendingDown className="h-4 w-4 text-amber-500" />
                    )}
                    <span className="text-sm font-medium">Compliance</span>
                  </div>
                  <p className="text-2xl font-bold">{portfolio.compliance_score.toFixed(1)}</p>
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      {portfolios.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <Building2 className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Portfolios Found</h3>
            <p className="text-muted-foreground text-center">
              You don't have any portfolios assigned yet.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
