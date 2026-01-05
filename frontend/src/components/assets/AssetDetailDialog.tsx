import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogTitle,
} from '@/components/ui/dialog';
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from "@/components/ui/scroll-area";
import { Separator } from '@/components/ui/separator';
import { AssetActionRunner } from '@/components/assets/AssetActionRunner';
import { Asset } from '@/lib/api/hooks/useAssets';
import { Laptop, Server, Smartphone, Monitor, ShieldCheck, AlertTriangle, Cpu, HardDrive, Wifi, Activity, Wrench } from 'lucide-react';

interface AssetDetailDialogProps {
    asset: Asset | null;
    open: boolean;
    onOpenChange: (open: boolean) => void;
}

export function AssetDetailDialog({ asset, open, onOpenChange }: AssetDetailDialogProps) {
    if (!asset) return null;

    return (
        <Dialog open={open} onOpenChange={onOpenChange}>
            <DialogContent className="max-w-4xl max-h-[90vh] overflow-hidden flex flex-col glass p-0 border-white/20">
                {/* Header */}
                <div className="p-6 bg-gradient-to-br from-white/10 to-transparent border-b border-border/50">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-2xl bg-primary/10 border border-primary/20">
                                {asset.type === 'Laptop' && <Laptop className="w-8 h-8 text-primary" />}
                                {asset.type === 'Desktop' && <Monitor className="w-8 h-8 text-primary" />}
                                {asset.type === 'Mobile' && <Smartphone className="w-8 h-8 text-primary" />}
                                {asset.type === 'Server' && <Server className="w-8 h-8 text-primary" />}
                            </div>
                            <div>
                                <DialogTitle className="text-2xl font-bold">{asset.name}</DialogTitle>
                                <DialogDescription className="flex items-center gap-2 mt-1">
                                    <span>{asset.type}</span>
                                    {asset.serial_number && (
                                        <>
                                            <span>•</span>
                                            <span>{asset.serial_number}</span>
                                        </>
                                    )}
                                </DialogDescription>
                            </div>
                        </div>
                        <div className="flex flex-col items-end gap-2">
                            <Badge variant={asset.status === 'Active' ? 'default' : 'secondary'} className={asset.status === 'Active' ? 'bg-eucora-green' : ''}>
                                {asset.status}
                            </Badge>
                            <div className="text-sm text-muted-foreground">
                                Last Seen: {asset.last_checkin ? new Date(asset.last_checkin).toLocaleDateString() : 'Unknown'}
                            </div>
                        </div>
                    </div>
                </div>

                <Tabs defaultValue="overview" className="flex-1 flex flex-col">
                    <div className="px-6 border-b border-border/50 bg-background/50">
                        <TabsList className="bg-transparent h-14 space-x-4">
                            <TabsTrigger value="overview" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary h-10">Overview</TabsTrigger>
                            <TabsTrigger value="compliance" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary h-10">Compliance</TabsTrigger>
                            <TabsTrigger value="software" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary h-10">Software</TabsTrigger>
                            <TabsTrigger value="activity" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary h-10">Activity Log</TabsTrigger>
                            <TabsTrigger value="troubleshoot" className="data-[state=active]:bg-primary/10 data-[state=active]:text-primary h-10">
                                <div className="flex items-center gap-2">
                                    <Wrench className="w-4 h-4" /> Troubleshoot
                                </div>
                            </TabsTrigger>
                        </TabsList>
                    </div>

                    <ScrollArea className="flex-1 p-6 bg-background/40">
                        <TabsContent value="overview" className="mt-0 space-y-6">
                            <div className="grid grid-cols-2 gap-6">
                                <div className="space-y-4">
                                    <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Hardware Specs</h3>
                                    <div className="grid gap-4 p-4 rounded-xl border border-white/10 bg-white/5">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-sm"><Cpu className="w-4 h-4 text-primary" /> Processor</div>
                                            <span className="font-medium">Intel Core i7-12700H</span>
                                        </div>
                                        <Separator />
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-sm"><Activity className="w-4 h-4 text-primary" /> RAM</div>
                                            <span className="font-medium">32 GB DDR5</span>
                                        </div>
                                        <Separator />
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-sm"><HardDrive className="w-4 h-4 text-primary" /> Storage</div>
                                            <span className="font-medium">1 TB NVMe SSD</span>
                                        </div>
                                    </div>
                                </div>

                                <div className="space-y-4">
                                    <h3 className="text-sm font-semibold text-muted-foreground uppercase tracking-wider">Network & Identity</h3>
                                    <div className="grid gap-4 p-4 rounded-xl border border-white/10 bg-white/5">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-sm"><Wifi className="w-4 h-4 text-primary" /> IP Address</div>
                                            <span className="font-medium">{asset.ip_address || 'N/A'}</span>
                                        </div>
                                        <Separator />
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-sm">Owner</div>
                                            <span className="font-medium">{asset.owner}</span>
                                        </div>
                                        <Separator />
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2 text-sm">Location</div>
                                            <span className="font-medium">{asset.location}</span>
                                        </div>
                                    </div>
                                </div>
                            </div>
                        </TabsContent>

                        <TabsContent value="compliance" className="mt-0 space-y-6">
                            <div className="flex items-center gap-6 p-6 rounded-xl bg-gradient-to-r from-eucora-green/10 to-transparent border border-eucora-green/20">
                                <div className="relative">
                                    <svg className="w-24 h-24 transform -rotate-90">
                                        <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" className="text-muted/20" />
                                        <circle cx="48" cy="48" r="40" stroke="currentColor" strokeWidth="8" fill="transparent" strokeDasharray={251.2} strokeDashoffset={251.2 * (1 - (asset.compliance_score || 0) / 100)} className="text-eucora-green" />
                                    </svg>
                                    <span className="absolute inset-0 flex items-center justify-center text-xl font-bold">{asset.compliance_score || 0}%</span>
                                </div>
                                <div>
                                    <h3 className="text-lg font-bold text-eucora-green">Compliant</h3>
                                    <p className="text-muted-foreground max-w-md">Device meets all core security policies. Next audit scheduled for tomorrow.</p>
                                </div>
                            </div>

                            <div className="grid gap-3">
                                    <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                                        <div className="flex items-center gap-3">
                                            <ShieldCheck className="w-5 h-5 text-eucora-green" />
                                            <span className="font-medium">Disk Encryption (BitLocker)</span>
                                        </div>
                                        <Badge variant="outline" className={asset.disk_encryption ? "border-eucora-green text-eucora-green" : "border-muted text-muted-foreground"}>
                                            {asset.disk_encryption ? 'Enabled' : 'Disabled'}
                                        </Badge>
                                    </div>
                                    <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                                        <div className="flex items-center gap-3">
                                            <ShieldCheck className="w-5 h-5 text-eucora-green" />
                                            <span className="font-medium">Firewall Status</span>
                                        </div>
                                        <Badge variant="outline" className={asset.firewall_enabled ? "border-eucora-green text-eucora-green" : "border-muted text-muted-foreground"}>
                                            {asset.firewall_enabled ? 'Active' : 'Inactive'}
                                        </Badge>
                                    </div>
                                <div className="flex items-center justify-between p-4 rounded-lg border bg-card">
                                    <div className="flex items-center gap-3">
                                        <AlertTriangle className="w-5 h-5 text-eucora-gold" />
                                        <span className="font-medium">OS Patch Level</span>
                                    </div>
                                    <div className="flex items-center gap-2">
                                        <span className="text-xs text-muted-foreground">KB5034441 Missing</span>
                                        <Badge variant="outline" className="border-eucora-gold text-eucora-gold">Warning</Badge>
                                    </div>
                                </div>
                            </div>
                        </TabsContent>

                        <TabsContent value="software" className="mt-0">
                            <div className="border rounded-xl overflow-hidden bg-card">
                                <table className="w-full text-sm text-left">
                                    <thead className="bg-muted/50 text-muted-foreground font-medium">
                                        <tr>
                                            <th className="px-4 py-3">Application Name</th>
                                            <th className="px-4 py-3">Version</th>
                                            <th className="px-4 py-3">Vendor</th>
                                            <th className="px-4 py-3">Status</th>
                                        </tr>
                                    </thead>
                                    <tbody className="divide-y divide-border/50">
                                        {asset.installed_apps && asset.installed_apps.length > 0 ? (
                                            asset.installed_apps.map((app: any) => (
                                                <tr key={app.id} className="hover:bg-muted/30">
                                                    <td className="px-4 py-3 font-medium">{app.name?.split(' 0')[0] || app.name}</td>
                                                    <td className="px-4 py-3 text-muted-foreground">{app.version || 'N/A'}</td>
                                                    <td className="px-4 py-3 text-muted-foreground">{app.vendor || 'N/A'}</td>
                                                    <td className="px-4 py-3">
                                                        <Badge variant="secondary" className="text-xs">Installed</Badge>
                                                    </td>
                                                </tr>
                                            ))
                                        ) : (
                                            <tr>
                                                <td colSpan={4} className="px-4 py-8 text-center text-muted-foreground">
                                                    No installed applications data available
                                                </td>
                                            </tr>
                                        )}
                                    </tbody>
                                </table>
                            </div>
                        </TabsContent>
                        <TabsContent value="troubleshoot" className="mt-0 h-full">
                            <AssetActionRunner assetId={asset.id} />
                        </TabsContent>
                    </ScrollArea>
                </Tabs>
            </DialogContent>
        </Dialog>
    );
}
