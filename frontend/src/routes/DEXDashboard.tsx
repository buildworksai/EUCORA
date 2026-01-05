import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import {
    XAxis, YAxis, Tooltip as ReTooltip, ResponsiveContainer,
    BarChart, Bar, Cell, PieChart, Pie, Legend
} from 'recharts';
import { Leaf, Timer, Heart, MonitorCheck } from 'lucide-react';
import { mockDb } from '@/lib/mocks/seeder';
import { useQuery } from '@tanstack/react-query';

export default function DEXDashboard() {
    // Fetch a subset for stats
    const { data: assets = [] } = useQuery({
        queryKey: ['dexAssets'],
        queryFn: async () => {
            await new Promise(r => setTimeout(r, 600));
            return mockDb.assets.slice(0, 1000); // Sample 1000 for charts
        }
    });

    const avgDexScore = (assets.reduce((acc, curr) => acc + curr.dexScore, 0) / assets.length).toFixed(2);
    const avgBootTime = Math.round(assets.reduce((acc, curr) => acc + curr.bootTime, 0) / assets.length);
    const totalCarbon = Math.round(assets.reduce((acc, curr) => acc + curr.carbonFootprint, 0) / 1000); // Tons

    // Sentiment Data
    const sentimentCounts = assets.reduce((acc, curr) => {
        acc[curr.userSentiment] = (acc[curr.userSentiment] || 0) + 1;
        return acc;
    }, {} as Record<string, number>);

    const sentimentData = [
        { name: 'Positive', value: sentimentCounts['Positive'] || 0, color: '#388E3C' },
        { name: 'Neutral', value: sentimentCounts['Neutral'] || 0, color: '#F1C40F' },
        { name: 'Negative', value: sentimentCounts['Negative'] || 0, color: '#E74C3C' },
    ];

    // Boot Time Distribution (Histogram-ish)
    const bootTimeDist = [
        { range: '< 20s', value: assets.filter(a => a.bootTime < 20).length },
        { range: '20-45s', value: assets.filter(a => a.bootTime >= 20 && a.bootTime < 45).length },
        { range: '45-90s', value: assets.filter(a => a.bootTime >= 45 && a.bootTime < 90).length },
        { range: '> 90s', value: assets.filter(a => a.bootTime >= 90).length },
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
                        <div className="text-2xl font-bold">{avgDexScore} / 10</div>
                        <p className="text-xs text-muted-foreground">Top 10% of industry peer group</p>
                    </CardContent>
                </Card>

                <Card className="glass border-l-4 border-l-eucora-green">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Green IT Impact</CardTitle>
                        <Leaf className="h-4 w-4 text-eucora-green" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{totalCarbon} Tons</div>
                        <p className="text-xs text-muted-foreground">Est. Annual CO2 Emissions</p>
                    </CardContent>
                </Card>

                <Card className="glass border-l-4 border-l-eucora-teal">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Avg Boot Time</CardTitle>
                        <Timer className="h-4 w-4 text-muted-foreground" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{avgBootTime} s</div>
                        <p className="text-xs text-muted-foreground">-12% vs last month</p>
                    </CardContent>
                </Card>

                <Card className="glass border-l-4 border-l-pink-500">
                    <CardHeader className="flex flex-row items-center justify-between space-y-0 pb-2">
                        <CardTitle className="text-sm font-medium">Sentiment</CardTitle>
                        <Heart className="h-4 w-4 text-pink-500" />
                    </CardHeader>
                    <CardContent>
                        <div className="text-2xl font-bold">{(sentimentCounts['Positive'] / assets.length * 100).toFixed(0)}%</div>
                        <p className="text-xs text-muted-foreground">Positive Feedback</p>
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
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
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
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
                                <BarChart data={bootTimeDist}>
                                    <XAxis dataKey="range" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                    <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                    <ReTooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', borderRadius: '8px', border: '1px solid hsl(var(--border))' }} cursor={{ fill: 'transparent' }} />
                                    <Bar dataKey="value" fill="#00A3BF" radius={[4, 4, 0, 0]} />
                                </BarChart>
                            </ResponsiveContainer>
                        </div>
                    </CardContent>
                </Card>
            </div>
        </div>
    );
}
