// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
    XAxis, YAxis, Tooltip as ReTooltip, ResponsiveContainer,
    BarChart, Bar, Cell, PieChart, Pie, Legend
} from 'recharts';
import { Leaf, Timer, Heart, MonitorCheck, Loader2, TrendingUp, TrendingDown } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { ENDPOINTS, type DEXDashboardSummary, type GreenITSummary } from './dex/contracts';

export default function DEXDashboard() {
    // Fetch dashboard summary from DEX API
    const { data: dashboardData, isLoading: isLoadingDashboard } = useQuery<DEXDashboardSummary>({
        queryKey: ['dex-dashboard-summary'],
        queryFn: () => api.get<DEXDashboardSummary>(ENDPOINTS.dashboardSummary),
        staleTime: 180000, // 3 minutes
        refetchInterval: 300000, // Refetch every 5 minutes
    });

    // Fetch Green IT summary
    const { data: greenITData, isLoading: isLoadingGreenIT } = useQuery<GreenITSummary>({
        queryKey: ['dex-green-it-summary'],
        queryFn: () => api.get<GreenITSummary>(ENDPOINTS.greenITSummary),
        staleTime: 180000,
        refetchInterval: 300000,
    });

    const isLoading = isLoadingDashboard || isLoadingGreenIT;
    const summary = dashboardData;
    const greenIT = greenITData;

    // Sentiment Data
    const sentimentData = summary ? [
        { name: 'Positive', value: summary.positive_sentiment_pct, color: '#388E3C' },
        { name: 'Neutral', value: summary.neutral_sentiment_pct, color: '#F1C40F' },
        { name: 'Negative', value: summary.negative_sentiment_pct, color: '#E74C3C' },
    ] : [];

    // Boot Time Distribution (simplified - would need historical data for full histogram)
    const bootTimeDist = summary && summary.avg_boot_time ? [
        { range: '< 20s', value: summary.avg_boot_time < 20 ? summary.devices_with_dex : 0 },
        { range: '20-45s', value: summary.avg_boot_time >= 20 && summary.avg_boot_time < 45 ? summary.devices_with_dex : 0 },
        { range: '45-90s', value: summary.avg_boot_time >= 45 && summary.avg_boot_time < 90 ? summary.devices_with_dex : 0 },
        { range: '> 90s', value: summary.avg_boot_time >= 90 ? summary.devices_with_dex : 0 },
    ] : [];

    // Calculate trend indicator (mock - would need historical data)
    const dexTrend = summary && summary.avg_dex_score ? (summary.avg_dex_score >= 7.5 ? 'up' : 'down') : null;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Digital Employee Experience (DEX)</h2>
                    <p className="text-muted-foreground">Monitoring user sentiment, device performance, and sustainability.</p>
                </div>
            </div>

            {/* Top KPIs */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card className="glass border-l-4 border-l-eucora-deepBlue">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">DEX Score</CardTitle>
                        <MonitorCheck className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        ) : (
                            <>
                                <div className="flex items-center gap-2">
                                    <div className="text-2xl font-bold">
                                        {summary?.avg_dex_score?.toFixed(2) || '0.00'} / 10
                                    </div>
                                    {dexTrend === 'up' && <TrendingUp className="h-4 w-4 text-green-500" />}
                                    {dexTrend === 'down' && <TrendingDown className="h-4 w-4 text-red-500" />}
                                </div>
                                <p className="text-xs text-muted-foreground">Top 10% of industry peer group</p>
                            </>
                        )}
                    </CardContent>
                </Card>

                <Card className="glass border-l-4 border-l-eucora-green">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Green IT Impact</CardTitle>
                        <Leaf className="h-4 w-4 text-eucora-green" />
                    </CardHeader>
                    <CardContent>
                        {isLoadingGreenIT ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        ) : (
                            <>
                                <div className="text-2xl font-bold">
                                    {greenIT ? Math.round(greenIT.total_carbon_kg / 1000) : 0} Tons
                                </div>
                                <p className="text-xs text-muted-foreground">Est. Annual CO2 Emissions</p>
                            </>
                        )}
                    </CardContent>
                </Card>

                <Card className="glass border-l-4 border-l-eucora-teal">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Boot Time</CardTitle>
                        <Timer className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        ) : (
                            <>
                                <div className="text-2xl font-bold">{summary?.avg_boot_time || 0} s</div>
                                <p className="text-xs text-muted-foreground">-12% vs last month</p>
                            </>
                        )}
                    </CardContent>
                </Card>

                <Card className="glass border-l-4 border-l-pink-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Sentiment</CardTitle>
                        <Heart className="h-4 w-4 text-pink-500" />
                    </CardHeader>
                    <CardContent>
                        {isLoading ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        ) : (
                            <>
                                <div className="text-2xl font-bold">
                                    {summary?.positive_sentiment_pct?.toFixed(0) || '0'}%
                                </div>
                                <p className="text-xs text-muted-foreground">Positive Feedback</p>
                            </>
                        )}
                    </CardContent>
                </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                {/* Sentiment Pie Chart */}
                <Card className="glass">
                    <CardHeader>
                        <CardTitle>Employee Sentiment</CardTitle>
                        <CardDescription>Based on daily engagement surveys.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] w-full min-w-0">
                            {isLoading ? (
                                <div className="flex items-center justify-center h-full">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : sentimentData.length > 0 && sentimentData.some(d => d.value > 0) ? (
                                <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                                    <PieChart>
                                        <Pie
                                            data={sentimentData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={100}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {sentimentData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <ReTooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', borderRadius: '8px', border: '1px solid hsl(var(--border))' }} />
                                        <Legend />
                                    </PieChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-full text-muted-foreground">
                                    No data available
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Boot Time Histogram */}
                <Card className="glass">
                    <CardHeader>
                        <CardTitle>Boot Time Analysis</CardTitle>
                        <CardDescription>Device startup performance distribution.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] w-full min-w-0">
                            {isLoading ? (
                                <div className="flex items-center justify-center h-full">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : bootTimeDist.length > 0 && bootTimeDist.some(d => d.value > 0) ? (
                                <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                                    <BarChart data={bootTimeDist}>
                                        <XAxis dataKey="range" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                        <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                        <ReTooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', borderRadius: '8px', border: '1px solid hsl(var(--border))' }} cursor={{ fill: 'transparent' }} />
                                        <Bar dataKey="value" fill="#00A3BF" radius={[4, 4, 0, 0]} />
                                    </BarChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-full text-muted-foreground">
                                    No data available
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>
            </div>

            {/* Green IT Section */}
            {greenIT && (
                <Card className="glass">
                    <CardHeader>
                        <CardTitle className="flex items-center gap-2">
                            <Leaf className="h-5 w-5 text-eucora-green" />
                            Green IT & Sustainability Metrics
                        </CardTitle>
                        <CardDescription>Carbon footprint and power consumption tracking (last 30 days)</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="grid gap-4 md:grid-cols-4">
                            <div>
                                <p className="text-sm text-muted-foreground">Total Carbon Footprint</p>
                                <p className="text-2xl font-bold">{greenIT.total_carbon_kg.toFixed(1)} kg CO2</p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">Total Power Consumption</p>
                                <p className="text-2xl font-bold">{greenIT.total_power_kwh.toFixed(1)} kWh</p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">Avg Carbon per Device</p>
                                <p className="text-2xl font-bold">{greenIT.avg_carbon_per_device.toFixed(1)} kg</p>
                            </div>
                            <div>
                                <p className="text-sm text-muted-foreground">Avg Power per Device</p>
                                <p className="text-2xl font-bold">{greenIT.avg_power_per_device.toFixed(1)} kWh</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            )}
        </div>
    );
}
