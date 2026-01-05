// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * "Ask Amani" - Enhanced Floating AI chat bubble component.
 * Available on every page with context-aware assistance.
 * Features:
 * - Reduced transparency for better UX
 * - Page context awareness with dynamic suggestions
 * - Customizable system prompt
 * - Keyboard shortcuts (Ctrl+K to open)
 */
import { useState, useEffect, useRef, useCallback } from 'react';
import { useLocation } from 'react-router-dom';
import { 
    X, Send, Sparkles, Minimize2, Maximize2, Settings2, 
    MessageSquare, RotateCcw, ChevronDown, Info, Keyboard,
    Package, Shield, Rocket, Database, Activity, BarChart3,
    FileCheck, AlertTriangle, Zap
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import { Textarea } from '@/components/ui/textarea';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import {
    Sheet,
    SheetContent,
    SheetDescription,
    SheetHeader,
    SheetTitle,
    SheetTrigger,
    SheetFooter,
} from '@/components/ui/sheet';
import {
    Tooltip,
    TooltipContent,
    TooltipProvider,
    TooltipTrigger,
} from '@/components/ui/tooltip';
import {
    Collapsible,
    CollapsibleContent,
    CollapsibleTrigger,
} from '@/components/ui/collapsible';
import { useAmaniChat, useConversation, useCreateTaskFromMessage, usePendingApprovals, type AIAgentTask } from '@/lib/api/hooks/useAI';
import { AIApprovalDialog } from './AIApprovalDialog';
import { cn } from '@/lib/utils';
import { toast } from 'sonner';

interface Message {
    id: string;
    role: 'user' | 'assistant';
    content: string;
    timestamp: Date;
    requiresAction?: boolean;
    taskId?: string; // Link to created task if approval was requested
}

// Page context configuration with icons, descriptions, and smart suggestions
const PAGE_CONTEXT: Record<string, {
    title: string;
    description: string;
    icon: React.ComponentType<{ className?: string }>;
    suggestions: string[];
    capabilities: string[];
    tips: string[];
}> = {
    '/dashboard': {
        title: 'Dashboard',
        description: 'Monitor your deployment pipeline and system health at a glance.',
        icon: BarChart3,
        suggestions: [
            'What deployments need my attention?',
            'Show me high-risk changes pending approval',
            'Summarize today\'s deployment activity',
            'Which rings have failing deployments?',
        ],
        capabilities: [
            'View active deployments and their status',
            'Monitor ring progression and success rates',
            'Identify pending CAB approvals',
        ],
        tips: [
            'Click on a deployment card to see detailed status',
            'Use filters to focus on specific rings or statuses',
        ],
    },
    '/assets': {
        title: 'Asset Inventory',
        description: 'Browse and manage your endpoint assets across all platforms.',
        icon: Database,
        suggestions: [
            'How many Windows devices need updates?',
            'Show me non-compliant assets',
            'Which assets are running outdated packages?',
            'Find assets in the pilot ring',
        ],
        capabilities: [
            'Search and filter assets by platform, status, ring',
            'View asset compliance posture',
            'Track package installation status',
        ],
        tips: [
            'Use the search bar to find specific assets',
            'Filter by compliance status to find issues',
        ],
    },
    '/compliance': {
        title: 'Compliance Dashboard',
        description: 'Track compliance posture and policy adherence across your fleet.',
        icon: Shield,
        suggestions: [
            'What\'s our overall compliance rate?',
            'Which policies have the most violations?',
            'Show me critical compliance gaps',
            'How can I improve compliance in APAC region?',
        ],
        capabilities: [
            'Monitor compliance metrics by region/department',
            'Track policy violation trends',
            'Generate compliance reports',
        ],
        tips: [
            'Set up alerts for compliance threshold breaches',
            'Review drift remediation status regularly',
        ],
    },
    '/deploy': {
        title: 'Deployments',
        description: 'Create and manage application deployments across rings.',
        icon: Rocket,
        suggestions: [
            'Help me create a new deployment',
            'What are the promotion gate requirements?',
            'Explain the ring progression model',
            'How do I rollback a failed deployment?',
        ],
        capabilities: [
            'Create new deployment intents',
            'Monitor ring progression',
            'Execute rollbacks when needed',
        ],
        tips: [
            'Always validate rollback strategy before Ring 2+',
            'Monitor success rates in Canary before promoting',
        ],
    },
    '/cab': {
        title: 'CAB Portal',
        description: 'Review and approve Change Advisory Board submissions.',
        icon: FileCheck,
        suggestions: [
            'What changes are pending CAB approval?',
            'Explain this risk score to me',
            'Generate evidence pack summary',
            'What are the approval criteria for high-risk changes?',
        ],
        capabilities: [
            'Review pending CAB submissions',
            'Approve or reject changes with comments',
            'Generate and review evidence packs',
        ],
        tips: [
            'Always review the complete evidence pack before approval',
            'Check for compensating controls on exceptions',
        ],
    },
    '/ai-agents': {
        title: 'AI Agent Hub',
        description: 'Manage AI-assisted workflows with human approval gates.',
        icon: Sparkles,
        suggestions: [
            'What AI agents are available?',
            'Show me pending AI task approvals',
            'How do AI agents help with packaging?',
            'What tasks require human approval?',
        ],
        capabilities: [
            'View available AI agent capabilities',
            'Monitor AI-generated tasks',
            'Approve or reject AI recommendations',
        ],
        tips: [
            'All AI recommendations require human approval',
            'Review AI-generated evidence before submission',
        ],
    },
    '/audit': {
        title: 'Audit Trail',
        description: 'View immutable audit logs for all system activities.',
        icon: Activity,
        suggestions: [
            'Show me recent deployment events',
            'Who approved this change?',
            'Find all actions by a specific user',
            'Show me CAB decisions from last week',
        ],
        capabilities: [
            'Search and filter audit events',
            'Export audit reports',
            'Track correlation IDs across systems',
        ],
        tips: [
            'Use correlation IDs to trace complete workflows',
            'Export reports for compliance audits',
        ],
    },
    '/settings': {
        title: 'Settings',
        description: 'Configure AI providers, preferences, and system settings.',
        icon: Settings2,
        suggestions: [
            'How do I configure OpenAI?',
            'What AI providers are supported?',
            'Help me set up Anthropic Claude',
            'Explain API key security',
        ],
        capabilities: [
            'Configure AI model providers',
            'Set default provider for Amani',
            'Manage notification preferences',
        ],
        tips: [
            'API keys are stored securely in vault',
            'Set a default provider for consistent responses',
        ],
    },
    '/dex': {
        title: 'DEX & Green IT',
        description: 'Monitor Digital Employee Experience and sustainability metrics.',
        icon: Zap,
        suggestions: [
            'What\'s our current DEX score?',
            'How can we improve device performance?',
            'Show me energy consumption trends',
            'Which devices have poor user experience?',
        ],
        capabilities: [
            'Track DEX metrics across fleet',
            'Monitor sustainability indicators',
            'Identify performance bottlenecks',
        ],
        tips: [
            'Focus on devices with DEX scores below 70',
            'Track power consumption trends monthly',
        ],
    },
};

// Default context for unknown pages
const DEFAULT_CONTEXT = {
    title: 'EUCORA',
    description: 'Enterprise Endpoint Application Packaging & Deployment Factory',
    icon: Package,
    suggestions: [
        'How does EUCORA work?',
        'Explain the deployment ring model',
        'What is CAB approval?',
        'Help me get started',
    ],
    capabilities: [
        'Packaging and deployment management',
        'Compliance monitoring',
        'CAB workflow automation',
    ],
    tips: [
        'Use the sidebar to navigate between modules',
        'Press Ctrl+K to quickly open Amani',
    ],
};

// Default system prompt template
const DEFAULT_SYSTEM_PROMPT = `You are Amani, an AI assistant for EUCORA (End-User Computing Orchestration & Reliability Architecture).

IMPORTANT RULES:
1. You are an ASSISTANT - all recommendations require human approval
2. Never bypass CAB approval gates or risk thresholds
3. Risk scores are deterministic - explain them, don't override them
4. Always mention when actions require approval

Be concise, actionable, and reference EUCORA concepts (rings, evidence packs, risk factors).`;

export function AmaniChatBubble() {
    const location = useLocation();
    const [isOpen, setIsOpen] = useState(false);
    const [isExpanded, setIsExpanded] = useState(false);
    const [messages, setMessages] = useState<Message[]>([]);
    const [input, setInput] = useState('');
    const [conversationId, setConversationId] = useState<string | null>(null);
    const [showSettings, setShowSettings] = useState(false);
    const [systemPrompt, setSystemPrompt] = useState(() => {
        // Load from localStorage or use default
        return localStorage.getItem('amani_system_prompt') || DEFAULT_SYSTEM_PROMPT;
    });
    const [tempSystemPrompt, setTempSystemPrompt] = useState(systemPrompt);
    const [showContextHelp, setShowContextHelp] = useState(true);
    const [selectedTask, setSelectedTask] = useState<AIAgentTask | null>(null);
    const [approvalDialogOpen, setApprovalDialogOpen] = useState(false);
    const messagesEndRef = useRef<HTMLDivElement>(null);
    const inputRef = useRef<HTMLInputElement>(null);
    
    const { mutateAsync: sendMessage, isPending: isLoading } = useAmaniChat();
    const { data: conversationData } = useConversation(conversationId);
    const { mutateAsync: createTask } = useCreateTaskFromMessage();
    const { data: pendingApprovalsData } = usePendingApprovals();
    
    // Get current page context
    const currentPath = location.pathname;
    const pageContext = PAGE_CONTEXT[currentPath] || DEFAULT_CONTEXT;
    const PageIcon = pageContext.icon;
    
    // Keyboard shortcut to open chat (Ctrl+K or Cmd+K)
    useEffect(() => {
        const handleKeyDown = (e: KeyboardEvent) => {
            if ((e.ctrlKey || e.metaKey) && e.key === 'k') {
                e.preventDefault();
                setIsOpen(prev => !prev);
            }
            // Escape to close
            if (e.key === 'Escape' && isOpen) {
                setIsOpen(false);
            }
        };
        
        window.addEventListener('keydown', handleKeyDown);
        return () => window.removeEventListener('keydown', handleKeyDown);
    }, [isOpen]);
    
    // Focus input when chat opens
    useEffect(() => {
        if (isOpen && inputRef.current) {
            setTimeout(() => inputRef.current?.focus(), 100);
        }
    }, [isOpen]);
    
    // Load conversation history when conversationId changes
    useEffect(() => {
        if (conversationData?.messages) {
            const loadedMessages: Message[] = conversationData.messages.map((msg: any) => ({
                id: msg.id,
                role: msg.role as 'user' | 'assistant',
                content: msg.content,
                timestamp: new Date(msg.timestamp),
                requiresAction: msg.requires_action,
            }));
            setMessages(loadedMessages);
        }
    }, [conversationData]);
    
    const scrollToBottom = useCallback(() => {
        messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
    }, []);
    
    useEffect(() => {
        scrollToBottom();
    }, [messages, scrollToBottom]);
    
    const handleSend = async () => {
        if (!input.trim() || isLoading) return;
        
        const userMessage: Message = {
            id: crypto.randomUUID(),
            role: 'user',
            content: input,
            timestamp: new Date()
        };
        
        setMessages(prev => [...prev, userMessage]);
        const currentInput = input;
        setInput('');
        setShowContextHelp(false);
        
        try {
            const response = await sendMessage({
                message: currentInput,
                conversation_id: conversationId || undefined,
                context: {
                    page: currentPath,
                    page_title: pageContext.title,
                    custom_system_prompt: systemPrompt !== DEFAULT_SYSTEM_PROMPT ? systemPrompt : undefined,
                },
            });
            
            if (response.error) {
                toast.error(response.error);
                return;
            }
            
            // Update conversation ID if this is a new conversation
            if (!conversationId && response.conversation_id) {
                setConversationId(response.conversation_id);
            }
            
            const assistantMessage: Message = {
                id: response.message_id,
                role: 'assistant',
                content: response.response,
                timestamp: new Date(),
                requiresAction: response.requires_action
            };
            
            setMessages(prev => [...prev, assistantMessage]);
        } catch (error: any) {
            toast.error(error?.response?.data?.error || 'Failed to send message');
            // Remove the user message on error
            setMessages(prev => prev.filter(m => m.id !== userMessage.id));
        }
    };
    
    const handleNewConversation = () => {
        setMessages([]);
        setConversationId(null);
        setShowContextHelp(true);
    };
    
    const handleSaveSystemPrompt = () => {
        setSystemPrompt(tempSystemPrompt);
        localStorage.setItem('amani_system_prompt', tempSystemPrompt);
        setShowSettings(false);
        toast.success('System prompt updated');
    };
    
    const handleResetSystemPrompt = () => {
        setTempSystemPrompt(DEFAULT_SYSTEM_PROMPT);
    };
    
    const handleSuggestionClick = (suggestion: string) => {
        setInput(suggestion);
        inputRef.current?.focus();
    };
    
    // Handle clicking on "Requires Human Approval" badge
    const handleApprovalClick = async (message: Message) => {
        try {
            // If message already has a task ID, find and open that task
            if (message.taskId) {
                const existingTask = pendingApprovalsData?.pending_approvals?.find(
                    t => t.id === message.taskId
                );
                if (existingTask) {
                    setSelectedTask(existingTask);
                    setApprovalDialogOpen(true);
                    return;
                }
            }
            
            // Create a new task for this AI recommendation
            const result = await createTask({
                title: `AI Recommendation: ${message.content.substring(0, 50)}...`,
                description: message.content,
                agent_type: 'amani',
                task_type: 'ai_recommendation',
                input_data: {
                    page: currentPath,
                    page_title: pageContext.title,
                },
                output_data: {
                    recommendation: message.content,
                    timestamp: message.timestamp.toISOString(),
                },
                conversation_id: conversationId || undefined,
            });
            
            if (result.task) {
                // Update the message with the task ID
                setMessages(prev => prev.map(m => 
                    m.id === message.id 
                        ? { ...m, taskId: result.task.id }
                        : m
                ));
                
                // Open the approval dialog with the new task
                setSelectedTask(result.task);
                setApprovalDialogOpen(true);
                
                toast.success('Task created for approval', {
                    description: 'This recommendation has been submitted for human approval.',
                });
            }
        } catch (error: any) {
            toast.error('Failed to create approval task', {
                description: error?.response?.data?.error || 'An error occurred',
            });
        }
    };
    
    const pendingCount = pendingApprovalsData?.total_count || 0;
    
    return (
        <TooltipProvider>
            {/* Floating Bubble */}
            <div className="fixed bottom-6 right-6 z-50 animate-in fade-in zoom-in duration-300">
                {!isOpen && (
                    <Tooltip>
                        <TooltipTrigger asChild>
                            <button
                                onClick={() => setIsOpen(true)}
                                className="relative group hover:scale-105 active:scale-95 transition-all duration-200"
                                aria-label="Open Amani chat (Ctrl+K)"
                            >
                                <div className="w-16 h-16 rounded-2xl bg-gradient-to-br from-eucora-teal via-eucora-teal to-eucora-coral flex items-center justify-center shadow-xl shadow-eucora-teal/30 border-2 border-white/30 transition-all group-hover:shadow-2xl group-hover:shadow-eucora-teal/40">
                                    <Sparkles className="h-7 w-7 text-white drop-shadow-lg" />
                                </div>
                                <span className="absolute -top-1 -right-1 w-5 h-5 bg-eucora-coral rounded-full animate-pulse flex items-center justify-center">
                                    <span className="text-[10px] text-white font-bold">AI</span>
                                </span>
                                <div className="absolute -bottom-2 left-1/2 -translate-x-1/2 bg-background/95 backdrop-blur-sm px-3 py-1.5 rounded-lg text-xs font-medium whitespace-nowrap opacity-0 group-hover:opacity-100 transition-all duration-200 border border-border shadow-lg">
                                    <span className="flex items-center gap-1.5">
                                        <Keyboard className="h-3 w-3 text-muted-foreground" />
                                        <span>⌘K</span>
                                    </span>
                                </div>
                            </button>
                        </TooltipTrigger>
                        <TooltipContent side="left" className="max-w-[200px]">
                            <p className="font-medium">Ask Amani</p>
                            <p className="text-xs text-muted-foreground">Your AI assistant for {pageContext.title}</p>
                        </TooltipContent>
                    </Tooltip>
                )}
            </div>
            
            {/* Chat Window - Reduced Transparency */}
            {isOpen && (
                <div
                    className={cn(
                        "fixed z-50 rounded-2xl shadow-2xl flex flex-col overflow-hidden animate-in fade-in slide-in-from-bottom-4 duration-300",
                        // REDUCED TRANSPARENCY: More solid background with subtle blur
                        "bg-[hsl(var(--card))]/95 backdrop-blur-xl border-2 border-border/50",
                        isExpanded 
                            ? "bottom-6 right-6 w-[700px] h-[85vh] max-h-[900px]" 
                            : "bottom-6 right-6 w-[440px] h-[600px]"
                    )}
                    style={{
                        boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.5), 0 0 0 1px rgba(255, 255, 255, 0.1)',
                    }}
                >
                    {/* Header - More Opaque */}
                    <div className="flex items-center justify-between px-4 py-3 border-b border-border bg-gradient-to-r from-eucora-teal/30 via-eucora-teal/20 to-eucora-coral/20">
                        <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-eucora-teal to-eucora-coral flex items-center justify-center shadow-lg">
                                <Sparkles className="h-5 w-5 text-white" />
                            </div>
                            <div>
                                <h3 className="font-semibold text-sm flex items-center gap-2">
                                    Ask Amani
                                    <Badge variant="outline" className="text-[10px] px-1.5 py-0 h-4 bg-eucora-teal/20 text-eucora-teal border-eucora-teal/30">
                                        AI
                                    </Badge>
                                    {pendingCount > 0 && (
                                        <Badge className="text-[10px] px-1.5 py-0 h-4 bg-eucora-gold text-white animate-pulse">
                                            {pendingCount} pending
                                        </Badge>
                                    )}
                                </h3>
                                <p className="text-xs text-muted-foreground flex items-center gap-1.5">
                                    <PageIcon className="h-3 w-3" />
                                    Helping with {pageContext.title}
                                </p>
                            </div>
                        </div>
                        <div className="flex items-center gap-1">
                            {/* New Conversation */}
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8"
                                        onClick={handleNewConversation}
                                        aria-label="New conversation"
                                    >
                                        <RotateCcw className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>New conversation</TooltipContent>
                            </Tooltip>
                            
                            {/* Settings Sheet */}
                            <Sheet open={showSettings} onOpenChange={setShowSettings}>
                                <SheetTrigger asChild>
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8"
                                        aria-label="Settings"
                                    >
                                        <Settings2 className="h-4 w-4" />
                                    </Button>
                                </SheetTrigger>
                                <SheetContent className="w-[400px] sm:w-[540px] bg-card/98 backdrop-blur-xl">
                                    <SheetHeader>
                                        <SheetTitle className="flex items-center gap-2">
                                            <Settings2 className="h-5 w-5 text-eucora-teal" />
                                            Amani Settings
                                        </SheetTitle>
                                        <SheetDescription>
                                            Customize how Amani assists you. Your preferences are saved locally.
                                        </SheetDescription>
                                    </SheetHeader>
                                    
                                    <div className="mt-6 space-y-6">
                                        {/* System Prompt Section */}
                                        <div className="space-y-3">
                                            <div className="flex items-center justify-between">
                                                <Label htmlFor="system-prompt" className="text-sm font-medium">
                                                    System Prompt
                                                </Label>
                                                <Button 
                                                    variant="ghost" 
                                                    size="sm" 
                                                    className="h-7 text-xs"
                                                    onClick={handleResetSystemPrompt}
                                                >
                                                    <RotateCcw className="h-3 w-3 mr-1" />
                                                    Reset to Default
                                                </Button>
                                            </div>
                                            <Textarea
                                                id="system-prompt"
                                                value={tempSystemPrompt}
                                                onChange={(e) => setTempSystemPrompt(e.target.value)}
                                                className="min-h-[200px] font-mono text-xs bg-background/50"
                                                placeholder="Enter custom system prompt..."
                                            />
                                            <p className="text-xs text-muted-foreground">
                                                This prompt guides how Amani responds. The default includes EUCORA governance rules.
                                            </p>
                                        </div>
                                        
                                        <Separator />
                                        
                                        {/* Tips Section */}
                                        <div className="space-y-3">
                                            <Label className="text-sm font-medium">Prompt Tips</Label>
                                            <div className="grid gap-2 text-xs text-muted-foreground">
                                                <div className="flex items-start gap-2 p-2 rounded-lg bg-background/50">
                                                    <Info className="h-4 w-4 mt-0.5 text-eucora-teal shrink-0" />
                                                    <span>Keep governance rules to ensure CAB compliance</span>
                                                </div>
                                                <div className="flex items-start gap-2 p-2 rounded-lg bg-background/50">
                                                    <Info className="h-4 w-4 mt-0.5 text-eucora-teal shrink-0" />
                                                    <span>Add domain-specific context for better answers</span>
                                                </div>
                                                <div className="flex items-start gap-2 p-2 rounded-lg bg-background/50">
                                                    <Info className="h-4 w-4 mt-0.5 text-eucora-teal shrink-0" />
                                                    <span>Include your role/team for personalized assistance</span>
                                                </div>
                                            </div>
                                        </div>
                                    </div>
                                    
                                    <SheetFooter className="mt-6">
                                        <Button variant="outline" onClick={() => setShowSettings(false)}>
                                            Cancel
                                        </Button>
                                        <Button 
                                            className="bg-eucora-teal hover:bg-eucora-teal/90"
                                            onClick={handleSaveSystemPrompt}
                                        >
                                            Save Changes
                                        </Button>
                                    </SheetFooter>
                                </SheetContent>
                            </Sheet>
                            
                            {/* Expand/Minimize */}
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8"
                                        onClick={() => setIsExpanded(!isExpanded)}
                                        aria-label={isExpanded ? "Minimize" : "Maximize"}
                                    >
                                        {isExpanded ? <Minimize2 className="h-4 w-4" /> : <Maximize2 className="h-4 w-4" />}
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>{isExpanded ? 'Minimize' : 'Expand'}</TooltipContent>
                            </Tooltip>
                            
                            {/* Close */}
                            <Tooltip>
                                <TooltipTrigger asChild>
                                    <Button 
                                        variant="ghost" 
                                        size="icon" 
                                        className="h-8 w-8"
                                        onClick={() => setIsOpen(false)}
                                        aria-label="Close chat"
                                    >
                                        <X className="h-4 w-4" />
                                    </Button>
                                </TooltipTrigger>
                                <TooltipContent>Close (Esc)</TooltipContent>
                            </Tooltip>
                        </div>
                    </div>
                    
                    {/* Messages Area */}
                    <ScrollArea className="flex-1 p-4">
                        {/* Context-Aware Welcome */}
                        {messages.length === 0 && showContextHelp && (
                            <div className="space-y-4">
                                {/* Page Context Header */}
                                <div className="text-center py-4">
                                    <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-gradient-to-br from-eucora-teal/20 to-eucora-coral/10 flex items-center justify-center border border-eucora-teal/30">
                                        <PageIcon className="h-8 w-8 text-eucora-teal" />
                                    </div>
                                    <h4 className="font-semibold text-lg mb-1">
                                        {pageContext.title}
                                    </h4>
                                    <p className="text-sm text-muted-foreground max-w-[300px] mx-auto">
                                        {pageContext.description}
                                    </p>
                                </div>
                                
                                {/* Suggestions */}
                                <div className="space-y-2">
                                    <p className="text-xs font-medium text-muted-foreground uppercase tracking-wider px-1">
                                        Suggested Questions
                                    </p>
                                    <div className="grid gap-2">
                                        {pageContext.suggestions.map((suggestion, i) => (
                                            <button
                                                key={i}
                                                onClick={() => handleSuggestionClick(suggestion)}
                                                className="flex items-center gap-3 p-3 rounded-xl text-left text-sm bg-background/50 hover:bg-background/80 border border-border/50 hover:border-eucora-teal/30 transition-all group"
                                            >
                                                <MessageSquare className="h-4 w-4 text-muted-foreground group-hover:text-eucora-teal transition-colors shrink-0" />
                                                <span className="group-hover:text-foreground transition-colors">{suggestion}</span>
                                            </button>
                                        ))}
                                    </div>
                                </div>
                                
                                {/* Collapsible Page Info */}
                                <Collapsible className="mt-4">
                                    <CollapsibleTrigger className="flex items-center gap-2 text-xs text-muted-foreground hover:text-foreground transition-colors w-full justify-center">
                                        <Info className="h-3 w-3" />
                                        <span>What can I do on this page?</span>
                                        <ChevronDown className="h-3 w-3" />
                                    </CollapsibleTrigger>
                                    <CollapsibleContent className="mt-3 space-y-3">
                                        {/* Capabilities */}
                                        <div className="p-3 rounded-xl bg-background/50 border border-border/50">
                                            <p className="text-xs font-medium text-muted-foreground mb-2">Capabilities</p>
                                            <ul className="space-y-1.5">
                                                {pageContext.capabilities.map((cap, i) => (
                                                    <li key={i} className="flex items-start gap-2 text-xs">
                                                        <span className="w-1.5 h-1.5 rounded-full bg-eucora-teal mt-1.5 shrink-0" />
                                                        <span>{cap}</span>
                                                    </li>
                                                ))}
                                            </ul>
                                        </div>
                                        
                                        {/* Tips */}
                                        <div className="p-3 rounded-xl bg-eucora-teal/5 border border-eucora-teal/20">
                                            <p className="text-xs font-medium text-eucora-teal mb-2">💡 Tips</p>
                                            <ul className="space-y-1.5">
                                                {pageContext.tips.map((tip, i) => (
                                                    <li key={i} className="text-xs text-muted-foreground">{tip}</li>
                                                ))}
                                            </ul>
                                        </div>
                                    </CollapsibleContent>
                                </Collapsible>
                            </div>
                        )}
                        
                        {/* Message History */}
                        {messages.map((message) => (
                            <div
                                key={message.id}
                                className={cn(
                                    "mb-4 flex",
                                    message.role === 'user' ? 'justify-end' : 'justify-start'
                                )}
                            >
                                <div
                                    className={cn(
                                        "max-w-[85%] rounded-2xl px-4 py-3",
                                        message.role === 'user'
                                            ? 'bg-eucora-teal text-white rounded-br-md shadow-lg'
                                            : 'bg-background border border-border rounded-bl-md shadow-sm'
                                    )}
                                >
                                    <p className="text-sm whitespace-pre-wrap leading-relaxed">{message.content}</p>
                                    {message.requiresAction && (
                                        <button
                                            onClick={() => handleApprovalClick(message)}
                                            className="mt-2 inline-flex items-center gap-1 px-2 py-1 text-xs rounded-md border border-eucora-coral text-eucora-coral bg-eucora-coral/10 hover:bg-eucora-coral/20 transition-colors cursor-pointer"
                                        >
                                            <AlertTriangle className="h-3 w-3" />
                                            {message.taskId ? 'View Approval Status' : 'Requires Human Approval'}
                                        </button>
                                    )}
                                </div>
                            </div>
                        ))}
                        
                        {/* Typing Indicator */}
                        {isLoading && (
                            <div className="flex justify-start mb-4">
                                <div className="bg-background border border-border rounded-2xl rounded-bl-md px-4 py-3 shadow-sm">
                                    <div className="flex items-center gap-2">
                                        <div className="flex gap-1">
                                            <span className="w-2 h-2 rounded-full bg-eucora-teal animate-bounce" style={{ animationDelay: '0ms' }} />
                                            <span className="w-2 h-2 rounded-full bg-eucora-teal animate-bounce" style={{ animationDelay: '150ms' }} />
                                            <span className="w-2 h-2 rounded-full bg-eucora-teal animate-bounce" style={{ animationDelay: '300ms' }} />
                                        </div>
                                        <span className="text-xs text-muted-foreground">Amani is thinking...</span>
                                    </div>
                                </div>
                            </div>
                        )}
                        
                        <div ref={messagesEndRef} />
                    </ScrollArea>
                    
                    {/* Input Area - More Opaque */}
                    <div className="p-4 border-t border-border bg-background/80">
                        <form 
                            onSubmit={(e) => { e.preventDefault(); handleSend(); }}
                            className="flex gap-2"
                        >
                            <Input
                                ref={inputRef}
                                value={input}
                                onChange={(e) => setInput(e.target.value)}
                                placeholder={`Ask about ${pageContext.title.toLowerCase()}...`}
                                className="flex-1 bg-background border-border/80 focus:border-eucora-teal"
                                disabled={isLoading}
                            />
                            <Button 
                                type="submit" 
                                size="icon"
                                disabled={!input.trim() || isLoading}
                                className="bg-eucora-teal hover:bg-eucora-teal/90 shadow-lg shadow-eucora-teal/25"
                            >
                                <Send className="h-4 w-4" />
                            </Button>
                        </form>
                        <p className="text-[10px] text-muted-foreground text-center mt-2">
                            AI recommendations require human approval • Press ⌘K to toggle
                        </p>
                    </div>
                </div>
            )}
            
            {/* Approval Dialog */}
            <AIApprovalDialog
                task={selectedTask}
                open={approvalDialogOpen}
                onOpenChange={setApprovalDialogOpen}
                onApproved={() => {
                    // Refresh messages to update status
                    toast.success('Task approved!');
                }}
                onRejected={() => {
                    toast.info('Task rejected');
                }}
            />
        </TooltipProvider>
    );
}
