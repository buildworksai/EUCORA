import { useState } from 'react';
import { Button } from '@/components/ui/button';
import { Card } from '@/components/ui/card';
import { Play, CheckCircle2, Loader2, Terminal } from 'lucide-react';
import { Badge } from '@/components/ui/badge';
import { ScrollArea } from '@/components/ui/scroll-area';

interface Action {
    id: string;
    name: string;
    description: string;
    risk: 'Low' | 'Medium' | 'High';
    estimatedTime: string;
}

const AVAILABLE_ACTIONS: Action[] = [
    { id: 'clean_teams', name: 'Clear Teams Cache', description: 'Removes local cache files to resolve login/display issues.', risk: 'Low', estimatedTime: '15s' },
    { id: 'restart_print', name: 'Restart Print Spooler', description: 'Restarts the local print service to clear stuck jobs.', risk: 'Low', estimatedTime: '10s' },
    { id: 'flush_dns', name: 'Flush DNS Cache', description: 'Clears local DNS resolver cache to fix connectivity.', risk: 'Low', estimatedTime: '5s' },
    { id: 'gpupdate', name: 'Force Group Policy', description: 'Runs gpupdate /force to apply latest policies.', risk: 'Medium', estimatedTime: '45s' },
    { id: 'reset_outlook', name: 'Reset Outlook Profile', description: 'Recreates the default Outlook mail profile.', risk: 'High', estimatedTime: '2m' },
    { id: 'restart_agent', name: 'Restart DEX Agent', description: 'Restarts the monitoring agent service.', risk: 'Low', estimatedTime: '30s' },
];

// Action-specific console output commands
const ACTION_COMMANDS: Record<string, string[]> = {
    'clean_teams': [
        'Remove-Item -Path "$env:APPDATA\\Microsoft\\Teams\\Cache\\*" -Recurse -Force',
        'Remove-Item -Path "$env:LOCALAPPDATA\\Microsoft\\Teams\\Cache\\*" -Recurse -Force',
        'Get-Process -Name "Teams" -ErrorAction SilentlyContinue | Stop-Process -Force',
    ],
    'restart_print': [
        'Stop-Service -Name "Spooler" -Force',
        'Start-Sleep -Seconds 2',
        'Start-Service -Name "Spooler"',
    ],
    'flush_dns': [
        'ipconfig /flushdns',
        'Clear-DnsClientCache',
    ],
    'gpupdate': [
        'gpupdate /force',
        'gpupdate /target:computer /force',
        'gpupdate /target:user /force',
    ],
    'reset_outlook': [
        'Get-Process -Name "OUTLOOK" -ErrorAction SilentlyContinue | Stop-Process -Force',
        'Remove-Item -Path "$env:APPDATA\\Microsoft\\Outlook\\*.ost" -Force',
        'Remove-Item -Path "$env:APPDATA\\Microsoft\\Outlook\\*.pst" -Force -ErrorAction SilentlyContinue',
        'New-Item -Path "$env:APPDATA\\Microsoft\\Outlook" -ItemType Directory -Force',
    ],
    'restart_agent': [
        'Stop-Service -Name "EUCORADEXAgent" -Force',
        'Start-Sleep -Seconds 3',
        'Start-Service -Name "EUCORADEXAgent"',
        'Get-Service -Name "EUCORADEXAgent" | Select-Object Status',
    ],
};

export function AssetActionRunner({ assetId }: { assetId: string | number }) {
    const [running, setRunning] = useState<string | null>(null);
    const [history, setHistory] = useState<Record<string, 'Success' | 'Fail'>>({});

    // Convert assetId to string for display
    const assetIdStr = String(assetId);

    const runAction = (actionId: string) => {
        setRunning(actionId);
        // Simulate remote execution latency
        setTimeout(() => {
            setRunning(null);
            setHistory(prev => ({ ...prev, [actionId]: 'Success' }));
        }, 2000);
    };

    return (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-6 h-full min-h-0" style={{ height: '100%' }}>
            {/* Action List */}
            <div className="md:col-span-2 flex flex-col min-h-0 overflow-hidden">
                <div className="flex items-center justify-between mb-4 flex-shrink-0">
                    <div>
                        <h3 className="text-lg font-semibold flex items-center gap-2">
                            <Terminal className="w-5 h-5 text-primary" />
                            Remote Actions
                        </h3>
                        <p className="text-sm text-muted-foreground">Execute self-healing scripts on the remote endpoint.</p>
                    </div>
                </div>

                <ScrollArea className="flex-1 min-h-0">
                    <div className="grid gap-3 pr-4">
                        {AVAILABLE_ACTIONS.map((action) => (
                            <Card key={action.id} className="p-4 flex items-center justify-between hover:bg-white/5 transition-colors border-white/10 glass">
                                <div className="space-y-1">
                                    <div className="flex items-center gap-2">
                                        <span className="font-medium">{action.name}</span>
                                        <Badge variant="outline" className={`text-[10px] h-5 ${action.risk === 'High' ? 'border-red-500/50 text-red-400' :
                                            action.risk === 'Medium' ? 'border-yellow-500/50 text-yellow-400' :
                                                'border-green-500/50 text-green-400'
                                            }`}>
                                            {action.risk} Risk
                                        </Badge>
                                    </div>
                                    <p className="text-xs text-muted-foreground">{action.description}</p>
                                </div>

                                <div className="flex items-center gap-4">
                                    <span className="text-xs text-muted-foreground font-mono hidden sm:inline-block">
                                        ~{action.estimatedTime}
                                    </span>

                                    {history[action.id] === 'Success' ? (
                                        <Button variant="ghost" size="sm" className="text-eucora-green cursor-default hover:text-eucora-green hover:bg-transparent" disabled>
                                            <CheckCircle2 className="w-5 h-5 mr-1" /> Done
                                        </Button>
                                    ) : (
                                        <Button
                                            size="sm"
                                            className="bg-primary/20 hover:bg-primary/30 text-primary border border-primary/20"
                                            disabled={!!running}
                                            onClick={() => runAction(action.id)}
                                        >
                                            {running === action.id ? (
                                                <Loader2 className="w-4 h-4 animate-spin" />
                                            ) : (
                                                <>
                                                    <Play className="w-3 h-3 mr-1.5" /> Run
                                                </>
                                            )}
                                        </Button>
                                    )}
                                </div>
                            </Card>
                        ))}
                    </div>
                </ScrollArea>
            </div>

            {/* Console Output / Log */}
            <div className="md:col-span-1 rounded-xl bg-black/80 border border-white/10 font-mono text-xs p-4 flex flex-col min-h-0 overflow-hidden">
                <div className="mb-2 text-muted-foreground border-b border-white/10 pb-2 flex justify-between flex-shrink-0">
                    <span>Console Output</span>
                    <span className="w-2 h-2 rounded-full bg-green-500 animate-pulse" />
                </div>
                <ScrollArea className="flex-1 min-h-0">
                    <div className="space-y-2 text-green-400/80 pr-4">
                        <div>&gt; Connecting to agent {assetIdStr.substring(0, 8)}... OK</div>
                        <div>&gt; Verifying permissions... OK</div>
                        {Object.keys(history).map(actionId => {
                            const action = AVAILABLE_ACTIONS.find(a => a.id === actionId);
                            const commands = ACTION_COMMANDS[actionId] || [];
                            return (
                                <div key={actionId} className="space-y-1 mt-4">
                                    <div className="text-yellow-400/80">&gt; Executing: {action?.name}</div>
                                    {commands.map((cmd, idx) => (
                                        <div key={idx} className="text-muted-foreground ml-2">... {cmd}</div>
                                    ))}
                                    <div className="text-white">&gt; Result: Success (Exit Code 0)</div>
                                </div>
                            )
                        })}
                        {running && (
                            <div className="mt-4 animate-pulse">
                                <span className="text-yellow-400">&gt; Executing request...</span>
                            </div>
                        )}
                        <div className="mt-2 text-primary animate-pulse w-2 h-4 bg-primary/50" />
                    </div>
                </ScrollArea>
            </div>
        </div>
    );
}
