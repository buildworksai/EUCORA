// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useTrueUpForecasts } from '../../lib/api/hooks/usePortfolioManagement';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Loader2, TrendingUp, DollarSign, AlertTriangle, CheckCircle2, Lightbulb } from 'lucide-react';

export function TrueUpForecasts() {
  const { data: forecastsData, isLoading, error } = useTrueUpForecasts({ ordering: '-forecast_generated_at' });

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
        <AlertDescription>Failed to load forecasts. Please try again.</AlertDescription>
      </Alert>
    );
  }

  const forecasts = forecastsData?.results || [];

  const getRiskColor = (additional: number, entitled: number) => {
    const percent = (additional / entitled) * 100;
    if (percent >= 50) return { badge: 'destructive', bg: 'bg-red-50 dark:bg-red-950 border-red-200', icon: 'text-red-600' };
    if (percent >= 25) return { badge: 'destructive', bg: 'bg-orange-50 dark:bg-orange-950 border-orange-200', icon: 'text-orange-600' };
    if (percent >= 10) return { badge: 'default', bg: 'bg-amber-50 dark:bg-amber-950 border-amber-200', icon: 'text-amber-600' };
    return { badge: 'secondary', bg: 'bg-green-50 dark:bg-green-950 border-green-200', icon: 'text-green-600' };
  };

  const getRiskLabel = (additional: number, entitled: number) => {
    const percent = (additional / entitled) * 100;
    if (percent >= 50) return 'CRITICAL';
    if (percent >= 25) return 'HIGH';
    if (percent >= 10) return 'MEDIUM';
    return 'LOW';
  };

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">License True-Up Forecasts</h1>
        <p className="text-muted-foreground">Vendor ELA renewal forecasts and budget planning</p>
      </div>

      {/* Forecasts Grid */}
      <div className="grid gap-6 md:grid-cols-1 lg:grid-cols-2">
        {forecasts.map((forecast) => {
          const riskStyle = getRiskColor(forecast.additional_licenses_needed, forecast.entitled_quantity_current);
          const riskLabel = getRiskLabel(forecast.additional_licenses_needed, forecast.entitled_quantity_current);
          const needsAdditional = forecast.additional_licenses_needed > 0;

          return (
            <Card key={forecast.id} className={`${riskStyle.bg} border-2`}>
              <CardHeader>
                <div className="flex items-start justify-between">
                  <div className="space-y-1">
                    <CardTitle className="text-xl">{forecast.vendor_name}</CardTitle>
                    <p className="text-sm text-muted-foreground">Forecast Period: {forecast.forecast_period}</p>
                  </div>
                  <Badge variant={riskStyle.badge as 'destructive' | 'default' | 'secondary' | 'outline'}>{riskLabel}</Badge>
                </div>
              </CardHeader>
              <CardContent className="space-y-4">
                {/* Current State */}
                <div className="space-y-2">
                  <div className="flex items-center justify-between">
                    <span className="text-sm font-medium">Current Utilization</span>
                    <span className="text-lg font-bold">{forecast.utilization_current_percent.toFixed(1)}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all"
                      style={{ width: `${Math.min(forecast.utilization_current_percent, 100)}%` }}
                    />
                  </div>
                  <div className="flex items-center justify-between text-xs text-muted-foreground">
                    <span>{forecast.consumed_quantity_current.toLocaleString()} consumed</span>
                    <span>{forecast.entitled_quantity_current.toLocaleString()} entitled</span>
                  </div>
                </div>

                {/* Forecast */}
                <div className="p-4 rounded-lg bg-background/50 space-y-3">
                  <div className="flex items-center gap-2">
                    <TrendingUp className={`h-5 w-5 ${riskStyle.icon}`} />
                    <span className="font-semibold">Forecast</span>
                  </div>
                  <div className="space-y-2 text-sm">
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Projected Consumption</span>
                      <span className="font-medium">{forecast.consumed_quantity_forecast.toLocaleString()}</span>
                    </div>
                    <div className="flex justify-between">
                      <span className="text-muted-foreground">Growth Rate</span>
                      <span className="font-medium text-amber-600">
                        +{forecast.consumption_growth_percent.toFixed(1)}%
                      </span>
                    </div>
                    {needsAdditional ? (
                      <>
                        <div className="flex justify-between font-semibold text-red-600 dark:text-red-400">
                          <span>Additional Needed</span>
                          <span>{forecast.additional_licenses_needed.toLocaleString()}</span>
                        </div>
                        <div className="flex justify-between items-center">
                          <div className="flex items-center gap-1">
                            <DollarSign className="h-4 w-4" />
                            <span className="text-muted-foreground">Estimated Cost</span>
                          </div>
                          <span className="text-lg font-bold text-red-600 dark:text-red-400">
                            ${parseFloat(forecast.estimated_cost_impact).toLocaleString()}
                          </span>
                        </div>
                      </>
                    ) : (
                      <div className="flex items-center gap-2 text-green-600 dark:text-green-400 font-medium">
                        <CheckCircle2 className="h-4 w-4" />
                        <span>Within current entitlement</span>
                      </div>
                    )}
                  </div>
                </div>

                {/* Mitigation Recommendations */}
                {forecast.mitigation_recommendations && forecast.mitigation_recommendations.length > 0 && (
                  <div className="space-y-2">
                    <div className="flex items-center gap-2 text-sm font-medium">
                      <Lightbulb className="h-4 w-4 text-amber-500" />
                      <span>Mitigation Strategies</span>
                    </div>
                    <div className="space-y-2">
                      {forecast.mitigation_recommendations.slice(0, 3).map((rec, idx) => (
                        <div key={idx} className="p-3 rounded-lg bg-background/50 text-sm">
                          <div className="font-medium capitalize">{rec.strategy.replace('_', ' ')}</div>
                          <div className="text-xs text-muted-foreground mt-1">{rec.description}</div>
                          {rec.licenses_saved > 0 && (
                            <div className="text-xs text-green-600 dark:text-green-400 mt-1 font-medium">
                              Potential savings: {rec.licenses_saved} licenses (${rec.cost_savings.toLocaleString()})
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                    {parseFloat(forecast.potential_savings) > 0 && (
                      <div className="p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200">
                        <div className="flex items-center justify-between">
                          <span className="text-sm font-medium text-green-900 dark:text-green-100">
                            Total Potential Savings
                          </span>
                          <span className="text-lg font-bold text-green-600">
                            ${parseFloat(forecast.potential_savings).toLocaleString()}
                          </span>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {/* Confidence */}
                <div className="flex items-center justify-between text-sm pt-2 border-t">
                  <span className="text-muted-foreground">Forecast Confidence</span>
                  <Badge variant="outline">{forecast.confidence_percent.toFixed(0)}%</Badge>
                </div>
              </CardContent>
            </Card>
          );
        })}
      </div>

      {forecasts.length === 0 && (
        <Card>
          <CardContent className="flex flex-col items-center justify-center py-12">
            <TrendingUp className="h-16 w-16 text-muted-foreground mb-4" />
            <h3 className="text-lg font-semibold mb-2">No Forecasts Available</h3>
            <p className="text-muted-foreground text-center">
              License true-up forecasts will appear here when generated.
            </p>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
