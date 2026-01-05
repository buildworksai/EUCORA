import { useState } from 'react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { SkeletonTable } from '@/components/ui/skeleton';
import { EmptyState } from '@/components/ui/empty-state';
import { Search, Filter, ShieldAlert, User, Terminal, Calendar, Download } from 'lucide-react';
import { useEvents, type DeploymentEvent } from '@/lib/api/hooks/useEvents';
import { format } from 'date-fns';

export default function AuditTrail() {
    const [filter, setFilter] = useState('');
    const [dateRange, setDateRange] = useState<{ start?: string; end?: string }>({});

    const { data: events = [], isLoading, error } = useEvents({
        ...(filter ? { actor: filter } : {}),
        ...(dateRange.start ? { start_date: dateRange.start } : {}),
        ...(dateRange.end ? { end_date: dateRange.end } : {}),
    });

    const filteredEvents = events.filter((event) =>
        filter === '' ||
        event.actor.toLowerCase().includes(filter.toLowerCase()) ||
        event.event_type.toLowerCase().includes(filter.toLowerCase()) ||
        event.correlation_id.toLowerCase().includes(filter.toLowerCase())
    );

    if (error) {
        return (
            <div className="space-y-6">
                <EmptyState
                    icon={ShieldAlert}
                    title="Failed to load audit trail"
                    description={error instanceof Error ? error.message : 'Unknown error occurred'}
                />
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                        <ShieldAlert className="w-8 h-8 text-eucora-deepBlue" />
                        Audit Trail
                    </h2>
                    <p className="text-muted-foreground">
                        Forensic logs of all administrative actions and system events.
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <div className="relative w-full md:w-64">
                        <Search className="absolute left-2 top-2.5 h-4 w-4 text-muted-foreground" />
                        <Input
                            placeholder="Search logs..."
                            className="pl-8 bg-background/50"
                            value={filter}
                            onChange={(e) => setFilter(e.target.value)}
                            aria-label="Search audit logs"
                        />
                    </div>
                    <Button variant="outline" aria-label="Filter">
                        <Filter className="w-4 h-4 mr-2" /> Filter
                    </Button>
                    <Button variant="outline" aria-label="Export">
                        <Download className="w-4 h-4 mr-2" /> Export
                    </Button>
                </div>
            </div>

            {/* Timeline / Volume Visualization */}
            <div className="h-32 rounded-xl bg-gradient-to-r from-blue-900/20 to-purple-900/20 border border-white/10 flex items-center justify-center relative overflow-hidden">
                <div className="absolute inset-0 flex items-end justify-between px-4 opacity-50 pb-2">
                    {Array.from({ length: Math.min(40, filteredEvents.length) }).map((_, i) => {
                        const eventCount = Math.floor(Math.random() * filteredEvents.length);
                        return (
                            <div
                                key={i}
                                className="w-2 bg-primary/40 rounded-t-sm transition-all hover:bg-primary/80"
                                style={{ height: `${Math.min(80, (eventCount / filteredEvents.length) * 100)}%` }}
                            />
                        );
                    })}
                </div>
                <div className="relative z-10 font-mono text-xs text-muted-foreground bg-background/80 px-2 py-1 rounded backdrop-blur">
                    Activity Volume (Last 7 Days)
                </div>
            </div>

            <Card className="glass">
                <div className="rounded-xl border border-white/10 overflow-hidden">
                    {isLoading ? (
                        <div className="p-6">
                            <SkeletonTable rows={10} />
                        </div>
                    ) : filteredEvents.length === 0 ? (
                        <div className="p-12">
                            <EmptyState
                                icon={ShieldAlert}
                                title="No audit events found"
                                description="No events match your search criteria"
                            />
                        </div>
                    ) : (
                        <div className="overflow-x-auto">
                            <table className="w-full text-sm text-left" role="table">
                                <thead className="bg-muted/50 text-muted-foreground font-medium uppercase text-xs tracking-wider">
                                    <tr>
                                        <th className="px-6 py-4">Timestamp</th>
                                        <th className="px-6 py-4">Actor</th>
                                        <th className="px-6 py-4">Action</th>
                                        <th className="px-6 py-4">Resource</th>
                                        <th className="px-6 py-4">Status</th>
                                        <th className="px-6 py-4 text-right">Correlation ID</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-border/50 bg-background/20 backdrop-blur-sm">
                                    {filteredEvents.slice(0, 100).map((event) => (
                                        <tr
                                            key={event.id}
                                            className="hover:bg-white/5 transition-colors group cursor-pointer font-mono"
                                        >
                                            <td className="px-6 py-3 text-muted-foreground whitespace-nowrap">
                                                {format(new Date(event.created_at), 'MMM dd, yyyy HH:mm:ss')}
                                            </td>
                                            <td className="px-6 py-3">
                                                <div className="flex items-center gap-2">
                                                    <div className="w-6 h-6 rounded-full bg-primary/20 flex items-center justify-center text-[10px] text-primary">
                                                        <User className="w-3 h-3" />
                                                    </div>
                                                    <span className="font-semibold text-foreground group-hover:text-primary transition-colors">
                                                        {event.actor}
                                                    </span>
                                                </div>
                                            </td>
                                            <td className="px-6 py-3">
                                                <Badge variant="outline" className="border-white/10 bg-white/5 font-normal">
                                                    {event.event_type}
                                                </Badge>
                                            </td>
                                            <td className="px-6 py-3 text-muted-foreground">
                                                <div className="flex items-center gap-2">
                                                    <Terminal className="w-3 h-3" />
                                                    {event.correlation_id.slice(0, 8)}
                                                </div>
                                            </td>
                                            <td className="px-6 py-3">
                                                <Badge variant="outline" className="border-green-500/50 text-green-500">
                                                    Success
                                                </Badge>
                                            </td>
                                            <td className="px-6 py-3 text-right text-muted-foreground text-xs">
                                                {event.correlation_id}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            </Card>
        </div>
    );
}
