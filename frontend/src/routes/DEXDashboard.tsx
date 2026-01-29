import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
    XAxis, YAxis, Tooltip as ReTooltip, ResponsiveContainer,
    BarChart, Bar, Cell, PieChart, Pie, Legend
} from 'recharts';
import { Leaf, Timer, Heart, MonitorCheck, Loader2 } from 'lucide-react';
import { useQuery } from '@tanstack/react-query';
import { api } from '@/lib/api/client';

interface Asset {
    id: string;
    dex_score: number;
    boot_time: number;
    carbon_footprint: number;
    user_sentiment: string;
}

interface AssetsResponse {
    assets: Asset[];
    total: number;
    page: number;
    page_size: number;
}

export default function DEXDashboard() {
    // Fetch assets from API for DEX stats
    const { data: assetsData, isLoading } = useQuery<AssetsResponse>({
        queryKey: ['dexAssets'],
        queryFn: async () => {
            // Fetch first 1000 assets for charts (enough for accurate stats)
            const response = await api.get<AssetsResponse>('/assets/?page_size=1000');
            return response;
        },
        staleTime: 180000, // 3 minutes
        refetchInterval: 300000, // Refetch every 5 minutes
    });

    const assets = assetsData?.assets || [];

    // CRITICAL FIX: Filter out null/undefined values when calculating averages to get accurate DEX metrics
    const assetsWithDex = assets.filter(a => a.dex_score != null && a.dex_score > 0);
    const assetsWithBootTime = assets.filter(a => a.boot_time != null && a.boot_time > 0);
    const assetsWithCarbon = assets.filter(a => a.carbon_footprint != null && a.carbon_footprint > 0);
    const assetsWithSentiment = assets.filter(a => a.user_sentiment != null);

    // Calculate stats from API data - only include assets with actual data
    const avgDexScore = assetsWithDex.length > 0
        ? (assetsWithDex.reduce((acc, curr) => acc + (curr.dex_score || 0), 0) / assetsWithDex.length).toFixed(2)
        : '0.00';
    const avgBootTime = assetsWithBootTime.length > 0
        ? Math.round(assetsWithBootTime.reduce((acc, curr) => acc + (curr.boot_time || 0), 0) / assetsWithBootTime.length)
        : 0;
    const totalCarbon = assetsWithCarbon.length > 0
        ? Math.round(assetsWithCarbon.reduce((acc, curr) => acc + (curr.carbon_footprint || 0), 0) / 1000) // Tons
        : 0;

    // Sentiment Data - only count assets with sentiment data
    const sentimentCounts = assetsWithSentiment.reduce((acc, curr) => {
        const sentiment = curr.user_sentiment || 'Neutral';
        acc[sentiment] = (acc[sentiment] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const sentimentData = [
        { name: 'Positive', value: sentimentCounts['Positive'] || 0, color: '#388E3C' },
        { name: 'Neutral', value: sentimentCounts['Neutral'] || 0, color: '#F1C40F' },
        { name: 'Negative', value: sentimentCounts['Negative'] || 0, color: '#E74C3C' },
    ];

    // Boot Time Distribution (Histogram-ish) - only include assets with boot_time data
    const bootTimeDist = [
        { range: '< 20s', value: assetsWithBootTime.filter(a => (a.boot_time || 0) < 20).length },
        { range: '20-45s', value: assetsWithBootTime.filter(a => (a.boot_time || 0) >= 20 && (a.boot_time || 0) < 45).length },
        { range: '45-90s', value: assetsWithBootTime.filter(a => (a.boot_time || 0) >= 45 && (a.boot_time || 0) < 90).length },
        { range: '> 90s', value: assetsWithBootTime.filter(a => (a.boot_time || 0) >= 90).length },
    ];

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
                                <div className="text-2xl font-bold">{avgDexScore} / 10</div>
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
                        {isLoading ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        ) : (
                            <>
                                <div className="text-2xl font-bold">{totalCarbon} Tons</div>
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
                                <div className="text-2xl font-bold">{avgBootTime} s</div>
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
                                    {assets.length > 0
                                        ? ((sentimentCounts['Positive'] || 0) / assets.length * 100).toFixed(0)
                                        : '0'
                                    }%
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
                            ) : sentimentData.length > 0 ? (
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
                            ) : bootTimeDist.length > 0 ? (
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
        </div>
    );
}
