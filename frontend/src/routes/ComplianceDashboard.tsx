import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useState } from 'react';
import { useComplianceStats } from '@/lib/api/hooks/useCompliance';
import { Loader2 } from 'lucide-react';

export default function ComplianceDashboard() {
    const [timeRange, setTimeRange] = useState('90d');
    const { data: stats, isLoading } = useComplianceStats();
    
    // Use API data if available, otherwise show loading or fallback
    const complianceTrend = stats?.compliance_trend || [];
    const vulnerabilityData = stats?.vulnerability_data || [];
    const osDistribution = stats?.os_distribution || [];
    const overallCompliance = stats?.overall_compliance || 0;
    const criticalVulns = stats?.critical_vulnerabilities || 0;
    const policyConflicts = stats?.policy_conflicts || 0;
    const pendingUpdates = stats?.pending_updates || 0;

    return (
        <div className="space-y-6">
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight">Compliance & Security</h2>
                    <p className="text-muted-foreground">Detailed insights into fleet version drift and vulnerability status.</p>
                </div>
                <Select value={timeRange} onValueChange={setTimeRange}>
                    <SelectTrigger className="w-[180px]">
                        <SelectValue placeholder="Select range" />
                    </SelectTrigger>
                    <SelectContent>
                        <SelectItem value="30d">Last 30 Days</SelectItem>
                        <SelectItem value="90d">Last 90 Days</SelectItem>
                        <SelectItem value="1y">Last Year</SelectItem>
                    </SelectContent>
                </Select>
            </div>

            {/* Top KPIs */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card className="glass border-l-4 border-l-eucora-green">
                    <CardHeader className="py-4">
                        <CardTitle className="text-xs font-medium uppercase text-muted-foreground">Overall Compliance</CardTitle>
                        {isLoading ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        ) : (
                            <div className="text-2xl font-bold">{overallCompliance.toFixed(1)}%</div>
                        )}
                    </CardHeader>
                </Card>
                <Card className="glass border-l-4 border-l-eucora-red">
                    <CardHeader className="py-4">
                        <CardTitle className="text-xs font-medium uppercase text-muted-foreground">Critical Vulnerabilities</CardTitle>
                        {isLoading ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        ) : (
                            <div className="text-2xl font-bold">{criticalVulns.toLocaleString()}</div>
                        )}
                    </CardHeader>
                </Card>
                <Card className="glass border-l-4 border-l-eucora-gold">
                    <CardHeader className="py-4">
                        <CardTitle className="text-xs font-medium uppercase text-muted-foreground">Policy Conflicts</CardTitle>
                        {isLoading ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        ) : (
                            <div className="text-2xl font-bold">{policyConflicts.toLocaleString()}</div>
                        )}
                    </CardHeader>
                </Card>
                <Card className="glass border-l-4 border-l-eucora-teal">
                    <CardHeader className="py-4">
                        <CardTitle className="text-xs font-medium uppercase text-muted-foreground">Pending Updates</CardTitle>
                        {isLoading ? (
                            <Loader2 className="h-6 w-6 animate-spin text-muted-foreground" />
                        ) : (
                            <div className="text-2xl font-bold">{pendingUpdates.toLocaleString()}</div>
                        )}
                    </CardHeader>
                </Card>
            </div>

            <div className="grid gap-6 md:grid-cols-2">
                {/* Compliance Trend Area Chart */}
                <Card className="glass col-span-2 lg:col-span-1">
                    <CardHeader>
                        <CardTitle>Compliance Score Trend</CardTitle>
                        <CardDescription>Historical compliance over time.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] w-full min-w-0">
                            {isLoading ? (
                                <div className="flex items-center justify-center h-full">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : complianceTrend.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                                    <AreaChart data={complianceTrend}>
                                        <defs>
                                            <linearGradient id="colorScore" x1="0" y1="0" x2="0" y2="1">
                                                <stop offset="5%" stopColor="#388E3C" stopOpacity={0.8} />
                                                <stop offset="95%" stopColor="#388E3C" stopOpacity={0} />
                                            </linearGradient>
                                        </defs>
                                        <XAxis dataKey="date" stroke="#888888" fontSize={12} tickLine={false} axisLine={false} />
                                        <YAxis stroke="#888888" fontSize={12} tickLine={false} axisLine={false} domain={[60, 100]} />
                                        <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', borderRadius: '8px', border: '1px solid hsl(var(--border))' }} />
                                        <Area type="monotone" dataKey="score" stroke="#388E3C" fillOpacity={1} fill="url(#colorScore)" />
                                    </AreaChart>
                                </ResponsiveContainer>
                            ) : (
                                <div className="flex items-center justify-center h-full text-muted-foreground">
                                    No data available
                                </div>
                            )}
                        </div>
                    </CardContent>
                </Card>

                {/* Vulnerabilities Pie Chart */}
                <Card className="glass col-span-2 lg:col-span-1">
                    <CardHeader>
                        <CardTitle>Vulnerability Distribution</CardTitle>
                        <CardDescription>Active vulnerabilities by severity.</CardDescription>
                    </CardHeader>
                    <CardContent>
                        <div className="h-[300px] w-full min-w-0">
                            {isLoading ? (
                                <div className="flex items-center justify-center h-full">
                                    <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                                </div>
                            ) : vulnerabilityData.length > 0 ? (
                                <ResponsiveContainer width="100%" height="100%" minWidth={0} minHeight={0}>
                                    <PieChart>
                                        <Pie
                                            data={vulnerabilityData}
                                            cx="50%"
                                            cy="50%"
                                            innerRadius={60}
                                            outerRadius={100}
                                            paddingAngle={5}
                                            dataKey="value"
                                        >
                                            {vulnerabilityData.map((entry, index) => (
                                                <Cell key={`cell-${index}`} fill={entry.color} />
                                            ))}
                                        </Pie>
                                        <Tooltip contentStyle={{ backgroundColor: 'hsl(var(--card))', borderRadius: '8px', border: '1px solid hsl(var(--border))' }} />
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
            </div>

            {/* OS Distribution Bar Chart (Drift Analysis) */}
            <Card className="glass">
                <CardHeader>
                    <CardTitle>Asset OS Distribution</CardTitle>
                    <CardDescription>Spread of Operating Systems across the fleet.</CardDescription>
                </CardHeader>
                <CardContent>
                    <div className="h-[250px] w-full flex items-end gap-2 justify-center">
                        {isLoading ? (
                            <div className="flex items-center justify-center h-full w-full">
                                <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
                            </div>
                        ) : osDistribution.length > 0 ? (
                            osDistribution.map((os) => {
                                const total = osDistribution.reduce((a, b) => a + b.value, 0);
                                const percentage = (os.value / total) * 100;
                                return (
                                    <div key={os.name} className="flex flex-col items-center gap-2 group w-24">
                                        <div className="relative w-full bg-muted rounded-t-lg overflow-hidden transition-all group-hover:opacity-80" style={{ height: '200px' }}>
                                            <div
                                                className="absolute bottom-0 w-full rounded-t-lg transition-all duration-500"
                                                style={{ height: `${percentage}%`, backgroundColor: os.color }}
                                            />
                                        </div>
                                        <div className="text-center">
                                            <div className="font-bold text-sm">{os.value.toLocaleString()}</div>
                                            <div className="text-xs text-muted-foreground">{os.name}</div>
                                        </div>
                                    </div>
                                )
                            })
                        ) : (
                            <div className="flex items-center justify-center h-full w-full text-muted-foreground">
                                No data available
                            </div>
                        )}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
