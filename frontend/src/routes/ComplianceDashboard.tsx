import { Card, CardContent, CardHeader, CardTitle, CardDescription } from '@/components/ui/card';
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, PieChart, Pie, Cell, Legend } from 'recharts';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { useState } from 'react';

// Mock Data
const complianceTrend = [
    { date: 'Jan 01', score: 82 }, { date: 'Jan 08', score: 85 }, { date: 'Jan 15', score: 84 },
    { date: 'Jan 22', score: 88 }, { date: 'Jan 29', score: 92 }, { date: 'Feb 05', score: 91 },
    { date: 'Feb 12', score: 94 }, { date: 'Feb 19', score: 96 }, { date: 'Feb 26', score: 98 },
];

const vulnerabilityData = [
    { name: 'Critical', value: 12, color: '#E74C3C' },
    { name: 'High', value: 45, color: '#F39C12' },
    { name: 'Medium', value: 120, color: '#F1C40F' },
    { name: 'Low', value: 350, color: '#3498DB' },
];

const osDistribution = [
    { name: 'Windows 11', value: 15400, color: '#0078D7' },
    { name: 'Windows 10', value: 8500, color: '#00BCF2' },
    { name: 'macOS Sonoma', value: 4300, color: '#FF3B30' },
    { name: 'Ubuntu', value: 1200, color: '#E95420' },
];

export default function ComplianceDashboard() {
    const [timeRange, setTimeRange] = useState('90d');

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
                        <div className="text-2xl font-bold">98.2%</div>
                    </CardHeader>
                </Card>
                <Card className="glass border-l-4 border-l-eucora-red">
                    <CardHeader className="py-4">
                        <CardTitle className="text-xs font-medium uppercase text-muted-foreground">Critical Vulnerabilities</CardTitle>
                        <div className="text-2xl font-bold">12</div>
                    </CardHeader>
                </Card>
                <Card className="glass border-l-4 border-l-eucora-gold">
                    <CardHeader className="py-4">
                        <CardTitle className="text-xs font-medium uppercase text-muted-foreground">Policy Conflicts</CardTitle>
                        <div className="text-2xl font-bold">145</div>
                    </CardHeader>
                </Card>
                <Card className="glass border-l-4 border-l-eucora-teal">
                    <CardHeader className="py-4">
                        <CardTitle className="text-xs font-medium uppercase text-muted-foreground">Pending Updates</CardTitle>
                        <div className="text-2xl font-bold">1,203</div>
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
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
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
                        <div className="h-[300px] w-full">
                            <ResponsiveContainer width="100%" height="100%">
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
                        {osDistribution.map((os) => {
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
                        })}
                    </div>
                </CardContent>
            </Card>
        </div>
    );
}
