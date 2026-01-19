// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * AI Agent Hub - Dashboard for AI-assisted workflows.
 */
import { useState } from 'react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { 
    Package, FileCheck, AlertTriangle, Rocket, Shield, 
    Activity, Clock, CheckCircle, XCircle, Play,
    Sparkles, Brain, Loader2
} from 'lucide-react';
import { useAIAgentTasks, useAIAgentStats } from '@/lib/api/hooks/useAI';

const AGENT_TYPES = [
    {
        id: 'packaging',
        name: 'Packaging Assistant',
        description: 'Automates package creation, SBOM generation, and vulnerability analysis',
        icon: Package,
        color: 'text-blue-500',
        capabilities: [
            'Generate Win32/MSIX/PKG packages',
            'Create SBOMs (SPDX/CycloneDX)',
            'Analyze vulnerabilities',
            'Write detection rules'
        ]
    },
    {
        id: 'cab_evidence',
        name: 'CAB Evidence Generator',
        description: 'Compiles complete evidence packs for CAB submissions',
        icon: FileCheck,
        color: 'text-green-500',
        capabilities: [
            'Generate evidence packs',
            'Compile test results',
            'Create rollout plans',
            'Document rollback strategies'
        ]
    },
    {
        id: 'risk_explainer',
        name: 'Risk Score Explainer',
        description: 'Explains risk scores and provides mitigation recommendations',
        icon: AlertTriangle,
        color: 'text-yellow-500',
        capabilities: [
            'Explain risk factors',
            'Suggest mitigations',
            'Compare similar packages',
            'Predict risk changes'
        ]
    },
    {
        id: 'deployment',
        name: 'Deployment Advisor',
        description: 'Recommends deployment strategies and monitors rollouts',
        icon: Rocket,
        color: 'text-purple-500',
        capabilities: [
            'Recommend ring strategies',
            'Analyze deployment health',
            'Predict success rates',
            'Suggest rollback triggers'
        ]
    },
    {
        id: 'compliance',
        name: 'Compliance Analyzer',
        description: 'Monitors compliance posture and suggests remediation',
        icon: Shield,
        color: 'text-eucora-teal',
        capabilities: [
            'Audit compliance gaps',
            'Generate remediation plans',
            'Track policy violations',
            'Forecast compliance trends'
        ]
    }
];

export default function AIAgentHub() {
    const { data: stats, isLoading: statsLoading } = useAIAgentStats();
    const { data: tasksData, isLoading: tasksLoading } = useAIAgentTasks();
    const [, setSelectedAgent] = useState<string | null>(null); // Reserved for future use
    
    const tasks = tasksData?.tasks || [];
    
    return (
        <div className="space-y-8">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                        <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-eucora-teal to-eucora-coral flex items-center justify-center">
                            <Sparkles className="h-5 w-5 text-white" />
                        </div>
                        AI Agent Hub
                    </h2>
                    <p className="text-muted-foreground mt-1">
                        AI-assisted workflows with mandatory human approval gates
                    </p>
                </div>
                <Badge variant="outline" className="text-eucora-teal border-eucora-teal">
                    All actions require human approval
                </Badge>
            </div>
            
            {/* Stats */}
            <div className="grid gap-4 md:grid-cols-4">
                <Card className="glass">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-eucora-teal/20">
                                <Activity className="h-6 w-6 text-eucora-teal" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">
                                    {statsLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : stats?.active_tasks || 0}
                                </p>
                                <p className="text-sm text-muted-foreground">Active Tasks</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="glass">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-yellow-500/20">
                                <Clock className="h-6 w-6 text-yellow-500" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">
                                    {statsLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : stats?.awaiting_approval || 0}
                                </p>
                                <p className="text-sm text-muted-foreground">Awaiting Approval</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="glass">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-green-500/20">
                                <CheckCircle className="h-6 w-6 text-green-500" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">
                                    {statsLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : stats?.completed_today || 0}
                                </p>
                                <p className="text-sm text-muted-foreground">Completed Today</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
                <Card className="glass">
                    <CardContent className="pt-6">
                        <div className="flex items-center gap-4">
                            <div className="p-3 rounded-xl bg-eucora-coral/20">
                                <Brain className="h-6 w-6 text-eucora-coral" />
                            </div>
                            <div>
                                <p className="text-2xl font-bold">
                                    {statsLoading ? <Loader2 className="h-6 w-6 animate-spin" /> : `${stats?.tokens_used || 0}k`}
                                </p>
                                <p className="text-sm text-muted-foreground">Tokens Used</p>
                            </div>
                        </div>
                    </CardContent>
                </Card>
            </div>
            
            <Tabs defaultValue="agents" className="space-y-6">
                <TabsList className="glass">
                    <TabsTrigger value="agents">Available Agents</TabsTrigger>
                    <TabsTrigger value="tasks">Recent Tasks</TabsTrigger>
                </TabsList>
                
                <TabsContent value="agents">
                    {/* Agent Cards */}
                    <div>
                        <h3 className="text-xl font-semibold mb-4">Available Agents</h3>
                        <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3">
                            {AGENT_TYPES.map(agent => (
                                <Card key={agent.id} className="glass hover:border-eucora-teal/50 transition-all group cursor-pointer">
                                    <CardHeader>
                                        <div className="flex items-center gap-3">
                                            <div className={`p-2 rounded-lg bg-white/5 ${agent.color}`}>
                                                <agent.icon className="h-5 w-5" />
                                            </div>
                                            <div>
                                                <CardTitle className="text-base">{agent.name}</CardTitle>
                                            </div>
                                        </div>
                                        <CardDescription>{agent.description}</CardDescription>
                                    </CardHeader>
                                    <CardContent>
                                        <ul className="text-sm space-y-1 text-muted-foreground">
                                            {agent.capabilities.map((cap, i) => (
                                                <li key={i} className="flex items-center gap-2">
                                                    <span className="w-1 h-1 rounded-full bg-eucora-teal" />
                                                    {cap}
                                                </li>
                                            ))}
                                        </ul>
                                        <Button 
                                            className="w-full mt-4 group-hover:bg-eucora-teal group-hover:text-white transition-colors" 
                                            variant="outline"
                                            onClick={() => setSelectedAgent(agent.id)}
                                        >
                                            <Play className="mr-2 h-4 w-4" />
                                            Start Workflow
                                        </Button>
                                    </CardContent>
                                </Card>
                            ))}
                        </div>
                    </div>
                </TabsContent>
                
                <TabsContent value="tasks">
                    {/* Recent Tasks */}
                    <div>
                        <h3 className="text-xl font-semibold mb-4">Recent Agent Tasks</h3>
                        <Card className="glass">
                            <CardContent className="pt-6">
                                {tasksLoading ? (
                                    <div className="text-center py-8">
                                        <Loader2 className="h-8 w-8 animate-spin mx-auto text-eucora-teal" />
                                    </div>
                                ) : tasks.length === 0 ? (
                                    <div className="text-center py-8 text-muted-foreground">
                                        No agent tasks yet. Start a workflow above.
                                    </div>
                                ) : (
                                    <div className="space-y-4">
                                        {tasks.map((task) => (
                                            <div key={task.id} className="flex items-center justify-between p-4 rounded-lg bg-white/5 hover:bg-white/10 transition-colors">
                                                <div className="flex items-center gap-3">
                                                    <Badge variant={
                                                        task.status === 'completed' ? 'default' :
                                                        task.status === 'awaiting_approval' ? 'secondary' :
                                                        task.status === 'failed' ? 'destructive' :
                                                        'outline'
                                                    }>
                                                        {task.status}
                                                    </Badge>
                                                    <div>
                                                        <p className="font-medium">{task.title}</p>
                                                        <p className="text-sm text-muted-foreground">{task.description}</p>
                                                        <p className="text-xs text-muted-foreground mt-1">
                                                            {new Date(task.created_at).toLocaleString()}
                                                        </p>
                                                    </div>
                                                </div>
                                                <div className="flex items-center gap-2">
                                                    {task.status === 'awaiting_approval' && (
                                                        <>
                                                            <Button size="sm" variant="outline" className="text-green-500">
                                                                <CheckCircle className="h-4 w-4 mr-1" /> Approve
                                                            </Button>
                                                            <Button size="sm" variant="outline" className="text-red-500">
                                                                <XCircle className="h-4 w-4 mr-1" /> Reject
                                                            </Button>
                                                        </>
                                                    )}
                                                </div>
                                            </div>
                                        ))}
                                    </div>
                                )}
                            </CardContent>
                        </Card>
                    </div>
                </TabsContent>
            </Tabs>
        </div>
    );
}

