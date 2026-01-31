// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { usePerformanceSnapshots, usePerformanceLeaderboard } from '../../lib/api/hooks/usePortfolioManagement';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Loader2, TrendingUp, Trophy, Activity, AlertTriangle } from 'lucide-react';

export function ApplicationManagerPerformance() {
  const { data: performanceData, isLoading, error } = usePerformanceSnapshots({ ordering: '-recorded_at' });
  const { data: leaderboard } = usePerformanceLeaderboard(10);

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
        <AlertDescription>Failed to load performance data. Please try again.</AlertDescription>
      </Alert>
    );
  }

  const snapshots = performanceData?.results || [];
  const latestSnapshot = snapshots[0];

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Application Manager Performance</h1>
        <p className="text-muted-foreground">Track performance metrics and composite scores</p>
      </div>

      {/* Latest Performance Snapshot */}
      {latestSnapshot && (
        <Card className="border-2 border-primary/20">
          <CardHeader>
            <div className="flex items-center justify-between">
              <div>
                <CardTitle className="text-xl">Current Performance</CardTitle>
                <p className="text-sm text-muted-foreground">{latestSnapshot.manager_name}</p>
              </div>
              <div className="text-right">
                <div className="text-4xl font-bold text-primary">{latestSnapshot.composite_score.toFixed(1)}</div>
                <p className="text-sm text-muted-foreground">Composite Score</p>
              </div>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-4 md:grid-cols-4">
              {/* Deployment Success */}
              <div className="space-y-2 p-4 rounded-lg bg-muted/50">
                <p className="text-sm font-medium text-muted-foreground">Deployment Success</p>
                <p className="text-2xl font-bold">{latestSnapshot.success_rate_percent.toFixed(1)}%</p>
                <p className="text-xs text-muted-foreground">
                  {latestSnapshot.deployments_successful}/{latestSnapshot.deployments_total} successful
                </p>
              </div>

              {/* Health Score */}
              <div className="space-y-2 p-4 rounded-lg bg-muted/50">
                <p className="text-sm font-medium text-muted-foreground">Avg Health Score</p>
                <p className="text-2xl font-bold">{latestSnapshot.avg_health_score.toFixed(1)}</p>
                <p className="text-xs text-muted-foreground">
                  {latestSnapshot.applications_healthy} healthy apps
                </p>
              </div>

              {/* License Utilization */}
              <div className="space-y-2 p-4 rounded-lg bg-muted/50">
                <p className="text-sm font-medium text-muted-foreground">License Utilization</p>
                <p className="text-2xl font-bold">{latestSnapshot.utilization_percent.toFixed(1)}%</p>
                <p className="text-xs text-muted-foreground">
                  {latestSnapshot.licenses_consumed}/{latestSnapshot.licenses_entitled}
                </p>
              </div>

              {/* MTTR */}
              <div className="space-y-2 p-4 rounded-lg bg-muted/50">
                <p className="text-sm font-medium text-muted-foreground">Avg MTTR</p>
                <p className="text-2xl font-bold">{latestSnapshot.avg_mttr_hours.toFixed(1)}h</p>
                <p className="text-xs text-muted-foreground">
                  {latestSnapshot.incidents_resolved}/{latestSnapshot.incidents_total} resolved
                </p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Performance Trend */}
      {snapshots.length > 1 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Activity className="h-5 w-5" />
              Performance Trend
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {snapshots.slice(0, 5).map((snapshot, idx) => {
                const isLatest = idx === 0;
                const prevScore = snapshots[idx + 1]?.composite_score;
                const scoreChange = prevScore ? snapshot.composite_score - prevScore : 0;

                return (
                  <div
                    key={snapshot.id}
                    className={`flex items-center justify-between p-3 rounded-lg ${
                      isLatest ? 'bg-primary/10 border border-primary/20' : 'bg-muted/30'
                    }`}
                  >
                    <div className="flex-1">
                      <div className="flex items-center gap-2">
                        <p className="font-medium">{snapshot.manager_name}</p>
                        {isLatest && <Badge variant="default">Current</Badge>}
                      </div>
                      <p className="text-xs text-muted-foreground">
                        {new Date(snapshot.period_start).toLocaleDateString()} -{' '}
                        {new Date(snapshot.period_end).toLocaleDateString()}
                      </p>
                    </div>
                    <div className="flex items-center gap-4">
                      {scoreChange !== 0 && (
                        <div className={`flex items-center gap-1 ${scoreChange > 0 ? 'text-green-500' : 'text-red-500'}`}>
                          <TrendingUp className={`h-4 w-4 ${scoreChange < 0 ? 'rotate-180' : ''}`} />
                          <span className="text-sm font-medium">{Math.abs(scoreChange).toFixed(1)}</span>
                        </div>
                      )}
                      <div className="text-right">
                        <p className="text-2xl font-bold">{snapshot.composite_score.toFixed(1)}</p>
                      </div>
                    </div>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Leaderboard */}
      {leaderboard && leaderboard.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Trophy className="h-5 w-5 text-amber-500" />
              Top Performers
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-2">
              {leaderboard.map((performer, idx) => (
                <div key={performer.id} className="flex items-center gap-4 p-3 rounded-lg bg-muted/30">
                  <div className={`flex items-center justify-center w-8 h-8 rounded-full font-bold ${
                    idx === 0 ? 'bg-amber-500 text-white' :
                    idx === 1 ? 'bg-slate-400 text-white' :
                    idx === 2 ? 'bg-orange-600 text-white' :
                    'bg-muted text-muted-foreground'
                  }`}>
                    {idx + 1}
                  </div>
                  <div className="flex-1">
                    <p className="font-medium">{performer.manager_name}</p>
                    <p className="text-xs text-muted-foreground">
                      {performer.portfolio_name || 'Multiple Portfolios'}
                    </p>
                  </div>
                  <div className="text-right">
                    <p className="text-xl font-bold">{performer.composite_score.toFixed(1)}</p>
                    <p className="text-xs text-muted-foreground">Score</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
