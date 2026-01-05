// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Settings page with Profile, AI Providers, User Management, and Integrations.
 */
import { useState, useEffect, useCallback, useMemo } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardFooter, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Badge } from '@/components/ui/badge';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { Switch } from '@/components/ui/switch';
import { 
    Eye, EyeOff, Save, Check, X, Bot, Sparkles, Zap, Brain, 
    Settings as SettingsIcon, Trash2, AlertTriangle, Users, Link2, 
    Shield, Database, Bell, Server, Globe, Cloud, Key, RefreshCw,
    Plus, Edit, UserPlus, UserMinus, Activity
} from 'lucide-react';
import { useModelProviders, useConfigureProvider, useDeleteProviderByType } from '@/lib/api/hooks/useAI';
import { useAuthStore } from '@/lib/stores/authStore';
import { isAdmin, isDemo, MOCK_USERS, type User, type UserRole } from '@/types/auth';
import { toast } from 'sonner';
import {
    AlertDialog,
    AlertDialogAction,
    AlertDialogCancel,
    AlertDialogContent,
    AlertDialogDescription,
    AlertDialogFooter,
    AlertDialogHeader,
    AlertDialogTitle,
    AlertDialogTrigger,
} from "@/components/ui/alert-dialog";
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogFooter,
    DialogHeader,
    DialogTitle,
    DialogTrigger,
} from "@/components/ui/dialog";
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';

const PROVIDERS = [
    { 
        id: 'openai', 
        name: 'OpenAI', 
        icon: Sparkles,
        models: [
            'gpt-4o',
            'gpt-4o-mini',
            'gpt-4-turbo',
            'gpt-4',
            'gpt-3.5-turbo',
            'o1-preview',
            'o1-mini',
        ],
        placeholder: 'sk-...'
    },
    { 
        id: 'anthropic', 
        name: 'Anthropic', 
        icon: Brain,
        models: [
            'claude-3-5-sonnet-20241022',
            'claude-3-opus-20240229',
            'claude-3-sonnet-20240229',
            'claude-3-haiku-20240307',
        ],
        placeholder: 'sk-ant-...'
    },
    { 
        id: 'groq', 
        name: 'Groq', 
        icon: Zap,
        models: [
            'llama-3.1-70b-versatile',
            'llama-3.1-8b-instant',
            'mixtral-8x7b-32768',
            'gemma2-9b-it',
        ],
        placeholder: 'gsk_...'
    },
    { 
        id: 'azure_openai', 
        name: 'Azure OpenAI', 
        icon: Bot,
        models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-35-turbo'],
        placeholder: 'your-azure-key',
        hasEndpoint: true
    },
    { 
        id: 'google_gemini', 
        name: 'Google Gemini', 
        icon: Sparkles,
        models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
        placeholder: 'AIza...'
    },
];

// Mock users for demo
const mockUsersList: User[] = [
    {
        id: '1',
        email: 'admin@eucora.com',
        firstName: 'System',
        lastName: 'Administrator',
        role: 'admin',
        department: 'IT Operations',
        isActive: true,
        permissions: [],
        createdAt: new Date('2024-01-01'),
        lastLogin: new Date(),
    },
    {
        id: '2',
        email: 'demo@eucora.com',
        firstName: 'Demo',
        lastName: 'User',
        role: 'demo',
        department: 'Engineering',
        isActive: true,
        permissions: [],
        createdAt: new Date('2024-06-01'),
        lastLogin: new Date(),
    },
    {
        id: '3',
        email: 'operator@eucora.com',
        firstName: 'John',
        lastName: 'Operator',
        role: 'operator',
        department: 'DevOps',
        isActive: true,
        permissions: [],
        createdAt: new Date('2024-03-15'),
        lastLogin: new Date(Date.now() - 86400000),
    },
    {
        id: '4',
        email: 'viewer@eucora.com',
        firstName: 'Jane',
        lastName: 'Viewer',
        role: 'viewer',
        department: 'Compliance',
        isActive: false,
        permissions: [],
        createdAt: new Date('2024-04-20'),
        lastLogin: new Date(Date.now() - 604800000),
    },
];

// Mock integrations state
const mockIntegrations = {
    entraId: {
        tenantId: '',
        clientId: '',
        redirectUri: 'https://eucora.example.com/auth/callback',
        scopes: ['User.Read', 'Directory.Read.All'],
        isConfigured: false,
    },
    cmdb: {
        type: 'servicenow' as const,
        apiUrl: '',
        syncInterval: 60,
        isConfigured: false,
    },
    ticketing: {
        type: 'jira' as const,
        apiUrl: '',
        projectKey: 'EUCORA',
        defaultPriority: 'Medium',
        isConfigured: false,
    },
    monitoring: {
        type: 'datadog' as const,
        apiUrl: '',
        dashboardUrl: '',
        alertWebhook: '',
        isConfigured: false,
    },
};

export default function Settings() {
    const [searchParams, setSearchParams] = useSearchParams();
    const tabFromUrl = searchParams.get('tab') || 'profile';
    
    // Use local state to track the active tab, initialized from URL
    const [activeTab, setActiveTab] = useState(tabFromUrl);
    
    // Sync URL to local state only on actual URL changes
    // Note: We DON'T include activeTab in deps to avoid the loop
    useEffect(() => {
        setActiveTab(tabFromUrl);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [tabFromUrl]);
    
    // Memoized handler to prevent re-renders
    const handleTabChange = useCallback((value: string) => {
        setActiveTab(value);
        // Update URL in the background without causing re-render loop
        setSearchParams({ tab: value }, { replace: true });
    }, [setSearchParams]);
    
    const [showKey, setShowKey] = useState<Record<string, boolean>>({});
    const [providerConfigs, setProviderConfigs] = useState<Record<string, any>>({});
    const [users, setUsers] = useState<User[]>(mockUsersList);
    const [integrations, setIntegrations] = useState(mockIntegrations);
    const [isEditingUser, setIsEditingUser] = useState<string | null>(null);
    const [isAddingUser, setIsAddingUser] = useState(false);
    const [newUser, setNewUser] = useState({ email: '', firstName: '', lastName: '', role: 'viewer' as UserRole, department: '' });
    
    const { data: providersData, isLoading } = useModelProviders();
    const { mutate: configureProvider, isPending: isSaving } = useConfigureProvider();
    const { mutate: deleteProviderByType, isPending: isDeleting } = useDeleteProviderByType();
    const { user: currentUser } = useAuthStore();

    const providers = providersData?.providers || [];
    const userIsAdmin = isAdmin(currentUser);
    const userIsDemo = isDemo(currentUser);

    const handleDeleteProvider = (providerType: string, providerName: string) => {
        deleteProviderByType(providerType, {
            onSuccess: () => {
                toast.success(`${providerName} configuration deleted successfully`);
                setProviderConfigs(prev => {
                    const { [providerType]: _, ...rest } = prev;
                    return rest;
                });
            },
            onError: (error: any) => {
                toast.error(error?.response?.data?.error || 'Failed to delete provider');
            }
        });
    };

    const toggleKey = (provider: string) => {
        setShowKey(prev => ({ ...prev, [provider]: !prev[provider] }));
    };

    const handleSaveProvider = (providerId: string) => {
        if (userIsDemo) {
            toast.info('Configuration changes are disabled in demo mode');
            return;
        }
        
        const config = providerConfigs[providerId];
        if (!config?.api_key) {
            toast.error('API key is required');
            return;
        }
        
        if (!config?.model_name) {
            toast.error('Model selection is required');
            return;
        }
        
        configureProvider({
            provider_type: providerId,
            api_key: config.api_key,
            model_name: config.model_name,
            endpoint_url: config.endpoint_url,
            display_name: PROVIDERS.find(p => p.id === providerId)?.name,
            max_tokens: config.max_tokens || 4096,
            temperature: config.temperature || 0.7,
            is_default: config.is_default || false,
        }, {
            onSuccess: () => {
                toast.success(`${PROVIDERS.find(p => p.id === providerId)?.name} configured successfully`);
                setProviderConfigs(prev => ({
                    ...prev,
                    [providerId]: { ...prev[providerId], api_key: '' }
                }));
            },
            onError: (error: any) => {
                toast.error(error?.response?.data?.error || 'Failed to configure provider');
            }
        });
    };

    const handleAddUser = () => {
        if (userIsDemo) {
            toast.info('User management is disabled in demo mode');
            return;
        }
        
        if (!newUser.email || !newUser.firstName) {
            toast.error('Email and first name are required');
            return;
        }
        
        const user: User = {
            id: String(Date.now()),
            email: newUser.email,
            firstName: newUser.firstName,
            lastName: newUser.lastName,
            role: newUser.role,
            department: newUser.department,
            isActive: true,
            permissions: [],
            createdAt: new Date(),
        };
        
        setUsers(prev => [...prev, user]);
        setNewUser({ email: '', firstName: '', lastName: '', role: 'viewer', department: '' });
        setIsAddingUser(false);
        toast.success('User added successfully');
    };

    const handleToggleUserStatus = (userId: string) => {
        if (userIsDemo) {
            toast.info('User management is disabled in demo mode');
            return;
        }
        
        setUsers(prev => prev.map(u => 
            u.id === userId ? { ...u, isActive: !u.isActive } : u
        ));
        toast.success('User status updated');
    };

    const handleSaveIntegration = (type: string) => {
        if (userIsDemo) {
            toast.info('Integration configuration is disabled in demo mode');
            return;
        }
        
        setIntegrations(prev => ({
            ...prev,
            [type]: { ...prev[type as keyof typeof prev], isConfigured: true }
        }));
        toast.success(`${type} integration configured successfully`);
    };

    // Initialize provider configs from existing providers only when providers data changes
    // We use JSON.stringify to compare arrays/objects properly
    const providersKey = JSON.stringify(providers.map((p: any) => p.id));
    useEffect(() => {
        if (providers.length === 0) return;
        
        const configs: Record<string, any> = {};
        providers.forEach((provider: any) => {
            configs[provider.provider_type] = {
                model_name: provider.model_name,
                endpoint_url: provider.endpoint_url,
                max_tokens: provider.max_tokens,
                temperature: provider.temperature,
                is_default: provider.is_default,
            };
        });
        setProviderConfigs(configs);
        // eslint-disable-next-line react-hooks/exhaustive-deps
    }, [providersKey]);

    const getRoleBadgeColor = (role: UserRole) => {
        switch (role) {
            case 'admin': return 'bg-eucora-gold/10 text-eucora-gold border-eucora-gold/30';
            case 'operator': return 'bg-eucora-deepBlue/10 text-eucora-deepBlue border-eucora-deepBlue/30';
            case 'demo': return 'bg-eucora-teal/10 text-eucora-teal border-eucora-teal/30';
            default: return 'bg-gray-500/10 text-gray-500 border-gray-500/30';
        }
    };

    return (
        <div className="max-w-6xl mx-auto space-y-8">
            <div>
                <h2 className="text-3xl font-bold tracking-tight flex items-center gap-3">
                    <SettingsIcon className="h-8 w-8 text-eucora-teal" />
                    Settings
                </h2>
                <p className="text-muted-foreground mt-1">
                    Manage your preferences, integrations, and system configurations.
                </p>
            </div>

            {userIsDemo && (
                <div className="flex items-center gap-3 p-4 bg-eucora-teal/10 border border-eucora-teal/20 rounded-lg">
                    <Sparkles className="h-5 w-5 text-eucora-teal" />
                    <div>
                        <p className="text-sm font-medium text-eucora-teal">Demo Mode Active</p>
                        <p className="text-xs text-muted-foreground">Configuration changes are view-only in demo mode.</p>
                    </div>
                </div>
            )}

            <Tabs value={activeTab} className="space-y-6" onValueChange={handleTabChange}>
                <TabsList className={`glass grid w-full ${userIsAdmin ? 'grid-cols-4' : 'grid-cols-2'}`}>
                    <TabsTrigger value="profile">Profile</TabsTrigger>
                    <TabsTrigger value="ai">AI Providers</TabsTrigger>
                    {userIsAdmin && <TabsTrigger value="users">Users</TabsTrigger>}
                    {userIsAdmin && <TabsTrigger value="integrations">Integrations</TabsTrigger>}
                </TabsList>

                {/* Profile Tab */}
                <TabsContent value="profile" className="space-y-6">
                    <Card className="glass">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Users className="h-5 w-5 text-eucora-teal" />
                                User Profile
                            </CardTitle>
                            <CardDescription>Your account information and preferences</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-6">
                            <div className="flex items-center gap-6">
                                <Avatar className="h-20 w-20 border-4 border-eucora-deepBlue/30">
                                    <AvatarImage src={currentUser?.avatar} />
                                    <AvatarFallback className="bg-eucora-deepBlue text-white text-2xl">
                                        {currentUser?.firstName?.charAt(0)}{currentUser?.lastName?.charAt(0)}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="space-y-1">
                                    <h3 className="text-xl font-semibold">
                                        {currentUser?.firstName} {currentUser?.lastName}
                                    </h3>
                                    <p className="text-muted-foreground">{currentUser?.email}</p>
                                    <div className="flex gap-2 mt-2">
                                        <Badge variant="outline" className={getRoleBadgeColor(currentUser?.role || 'viewer')}>
                                            {currentUser?.role?.toUpperCase()}
                                        </Badge>
                                        {currentUser?.department && (
                                            <Badge variant="secondary">{currentUser.department}</Badge>
                                        )}
                                    </div>
                                </div>
                            </div>
                            
                            <Separator />
                            
                            <div className="grid grid-cols-2 gap-4">
                                <div className="space-y-2">
                                    <Label>First Name</Label>
                                    <Input value={currentUser?.firstName || ''} disabled />
                                </div>
                                <div className="space-y-2">
                                    <Label>Last Name</Label>
                                    <Input value={currentUser?.lastName || ''} disabled />
                                </div>
                                <div className="space-y-2">
                                    <Label>Email</Label>
                                    <Input value={currentUser?.email || ''} disabled />
                                </div>
                                <div className="space-y-2">
                                    <Label>Department</Label>
                                    <Input value={currentUser?.department || ''} disabled />
                                </div>
                            </div>
                            
                            <div className="p-4 bg-muted/50 rounded-lg">
                                <p className="text-sm text-muted-foreground">
                                    <Shield className="inline h-4 w-4 mr-1" />
                                    Profile information is managed via Microsoft Entra ID. Contact your administrator to update.
                                </p>
                            </div>
                        </CardContent>
                    </Card>

                    <Card className="glass">
                        <CardHeader>
                            <CardTitle className="flex items-center gap-2">
                                <Bell className="h-5 w-5 text-eucora-teal" />
                                Notification Preferences
                            </CardTitle>
                            <CardDescription>Configure how you receive notifications</CardDescription>
                        </CardHeader>
                        <CardContent className="space-y-4">
                            <div className="flex items-center justify-between">
                                <div>
                                    <Label>Email Notifications</Label>
                                    <p className="text-xs text-muted-foreground">Receive deployment alerts via email</p>
                                </div>
                                <Switch defaultChecked />
                            </div>
                            <Separator />
                            <div className="flex items-center justify-between">
                                <div>
                                    <Label>CAB Approval Alerts</Label>
                                    <p className="text-xs text-muted-foreground">Notify when approvals are needed</p>
                                </div>
                                <Switch defaultChecked />
                            </div>
                            <Separator />
                            <div className="flex items-center justify-between">
                                <div>
                                    <Label>Critical System Alerts</Label>
                                    <p className="text-xs text-muted-foreground">High-priority system notifications</p>
                                </div>
                                <Switch defaultChecked />
                            </div>
                        </CardContent>
                    </Card>
                </TabsContent>

                {/* AI Providers Tab */}
                <TabsContent value="ai" className="space-y-6">
                    <Card className="glass border-eucora-teal/30">
                        <CardHeader>
                            <div className="flex items-center gap-2">
                                <Sparkles className="h-5 w-5 text-eucora-teal" />
                                <CardTitle>Default AI Provider</CardTitle>
                            </div>
                            <CardDescription>
                                Select the default provider for "Ask Amani" and agent workflows.
                            </CardDescription>
                        </CardHeader>
                        <CardContent>
                            <div className="flex items-center gap-4">
                                <Select 
                                    value={providers.find((p: any) => p.is_default)?.provider_type || ''}
                                    onValueChange={(value) => {
                                        if (userIsDemo) {
                                            toast.info('Configuration changes are disabled in demo mode');
                                            return;
                                        }
                                        const provider = providers.find((p: any) => p.provider_type === value);
                                        if (provider) {
                                            configureProvider({
                                                provider_type: provider.provider_type,
                                                api_key: '',
                                                model_name: provider.model_name,
                                                display_name: provider.display_name,
                                                is_default: true,
                                            }, {
                                                onSuccess: () => toast.success('Default provider updated'),
                                            });
                                        }
                                    }}
                                >
                                    <SelectTrigger className="w-full max-w-xs">
                                        <SelectValue placeholder="Select default provider" />
                                    </SelectTrigger>
                                    <SelectContent>
                                        {providers.filter((p: any) => p.is_active && p.key_configured).map((provider: any) => {
                                            const providerConfig = PROVIDERS.find(p => p.id === provider.provider_type);
                                            const IconComponent = providerConfig?.icon;
                                            return (
                                                <SelectItem key={provider.id} value={provider.provider_type}>
                                                    <div className="flex items-center gap-2">
                                                        {IconComponent && <IconComponent className="h-4 w-4" />}
                                                        {provider.display_name} ({provider.model_name})
                                                    </div>
                                                </SelectItem>
                                            );
                                        })}
                                    </SelectContent>
                                </Select>
                                {providers.filter((p: any) => p.is_default && p.is_active).length === 0 && (
                                    <Badge variant="outline" className="text-yellow-500 border-yellow-500">
                                        No default provider set
                                    </Badge>
                                )}
                            </div>
                        </CardContent>
                    </Card>

                    <div className="grid gap-4 md:grid-cols-2">
                        {PROVIDERS.map(provider => {
                            const existingProvider = providers.find(
                                (p: any) => p.provider_type === provider.id
                            );
                            const isConfigured = existingProvider?.key_configured || false;
                            const config = providerConfigs[provider.id] || {};
                            
                            return (
                                <Card key={provider.id} className={`glass transition-all ${isConfigured ? 'border-green-500/30' : ''}`}>
                                    <CardHeader className="pb-3">
                                        <div className="flex items-center justify-between">
                                            <div className="flex items-center gap-2">
                                                <provider.icon className="h-5 w-5 text-eucora-teal" />
                                                <CardTitle className="text-base">{provider.name}</CardTitle>
                                            </div>
                                            {isConfigured && (
                                                <Badge variant="outline" className="text-green-500 border-green-500">
                                                    <Check className="h-3 w-3 mr-1" /> Configured
                                                </Badge>
                                            )}
                                        </div>
                                    </CardHeader>
                                    <CardContent className="space-y-4">
                                        <div className="space-y-2">
                                            <Label>Model</Label>
                                            <Select 
                                                value={config.model_name || provider.models[0]}
                                                onValueChange={(value) => setProviderConfigs(prev => ({
                                                    ...prev,
                                                    [provider.id]: { ...prev[provider.id], model_name: value }
                                                }))}
                                            >
                                                <SelectTrigger>
                                                    <SelectValue />
                                                </SelectTrigger>
                                                <SelectContent>
                                                    {provider.models.map(model => (
                                                        <SelectItem key={model} value={model}>{model}</SelectItem>
                                                    ))}
                                                </SelectContent>
                                            </Select>
                                        </div>

                                        <div className="space-y-2">
                                            <Label>API Key {isConfigured && <span className="text-muted-foreground text-xs">(leave blank to keep existing)</span>}</Label>
                                            <div className="flex gap-2">
                                                <Input
                                                    type={showKey[provider.id] ? 'text' : 'password'}
                                                    placeholder={provider.placeholder}
                                                    value={config.api_key || ''}
                                                    onChange={(e) => setProviderConfigs(prev => ({
                                                        ...prev,
                                                        [provider.id]: { ...prev[provider.id], api_key: e.target.value }
                                                    }))}
                                                />
                                                <Button 
                                                    variant="ghost" 
                                                    size="icon"
                                                    onClick={() => toggleKey(provider.id)}
                                                >
                                                    {showKey[provider.id] ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                                                </Button>
                                            </div>
                                        </div>

                                        {provider.hasEndpoint && (
                                            <div className="space-y-2">
                                                <Label>Endpoint URL</Label>
                                                <Input
                                                    placeholder="https://your-endpoint.openai.azure.com/"
                                                    value={config.endpoint_url || ''}
                                                    onChange={(e) => setProviderConfigs(prev => ({
                                                        ...prev,
                                                        [provider.id]: { ...prev[provider.id], endpoint_url: e.target.value }
                                                    }))}
                                                />
                                            </div>
                                        )}
                                    </CardContent>
                                    <CardFooter className="pt-0">
                                        <Button 
                                            className="w-full bg-eucora-teal hover:bg-eucora-teal-dark"
                                            onClick={() => handleSaveProvider(provider.id)}
                                            disabled={isSaving}
                                        >
                                            <Save className="mr-2 h-4 w-4" />
                                            {isConfigured ? 'Update' : 'Save'}
                                        </Button>
                                    </CardFooter>
                                </Card>
                            );
                        })}
                    </div>
                </TabsContent>

                {/* Users Tab (Admin Only) */}
                {userIsAdmin && (
                    <TabsContent value="users" className="space-y-6">
                        <Card className="glass">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div>
                                        <CardTitle className="flex items-center gap-2">
                                            <Users className="h-5 w-5 text-eucora-teal" />
                                            User Management
                                        </CardTitle>
                                        <CardDescription>Manage user accounts and permissions</CardDescription>
                                    </div>
                                    <Dialog open={isAddingUser} onOpenChange={setIsAddingUser}>
                                        <DialogTrigger asChild>
                                            <Button className="bg-eucora-deepBlue hover:bg-eucora-deepBlue-dark">
                                                <UserPlus className="mr-2 h-4 w-4" />
                                                Add User
                                            </Button>
                                        </DialogTrigger>
                                        <DialogContent className="glass">
                                            <DialogHeader>
                                                <DialogTitle>Add New User</DialogTitle>
                                                <DialogDescription>Create a new user account</DialogDescription>
                                            </DialogHeader>
                                            <div className="space-y-4 py-4">
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div className="space-y-2">
                                                        <Label>First Name *</Label>
                                                        <Input 
                                                            value={newUser.firstName}
                                                            onChange={(e) => setNewUser(prev => ({ ...prev, firstName: e.target.value }))}
                                                        />
                                                    </div>
                                                    <div className="space-y-2">
                                                        <Label>Last Name</Label>
                                                        <Input 
                                                            value={newUser.lastName}
                                                            onChange={(e) => setNewUser(prev => ({ ...prev, lastName: e.target.value }))}
                                                        />
                                                    </div>
                                                </div>
                                                <div className="space-y-2">
                                                    <Label>Email *</Label>
                                                    <Input 
                                                        type="email"
                                                        value={newUser.email}
                                                        onChange={(e) => setNewUser(prev => ({ ...prev, email: e.target.value }))}
                                                    />
                                                </div>
                                                <div className="grid grid-cols-2 gap-4">
                                                    <div className="space-y-2">
                                                        <Label>Role</Label>
                                                        <Select 
                                                            value={newUser.role}
                                                            onValueChange={(value: UserRole) => setNewUser(prev => ({ ...prev, role: value }))}
                                                        >
                                                            <SelectTrigger>
                                                                <SelectValue />
                                                            </SelectTrigger>
                                                            <SelectContent>
                                                                <SelectItem value="admin">Admin</SelectItem>
                                                                <SelectItem value="operator">Operator</SelectItem>
                                                                <SelectItem value="viewer">Viewer</SelectItem>
                                                            </SelectContent>
                                                        </Select>
                                                    </div>
                                                    <div className="space-y-2">
                                                        <Label>Department</Label>
                                                        <Input 
                                                            value={newUser.department}
                                                            onChange={(e) => setNewUser(prev => ({ ...prev, department: e.target.value }))}
                                                        />
                                                    </div>
                                                </div>
                                            </div>
                                            <DialogFooter>
                                                <Button variant="outline" onClick={() => setIsAddingUser(false)}>Cancel</Button>
                                                <Button onClick={handleAddUser} className="bg-eucora-teal hover:bg-eucora-teal-dark">
                                                    Add User
                                                </Button>
                                            </DialogFooter>
                                        </DialogContent>
                                    </Dialog>
                                </div>
                            </CardHeader>
                            <CardContent>
                                <div className="space-y-3">
                                    {users.map(user => (
                                        <div 
                                            key={user.id}
                                            className={`flex items-center justify-between p-4 rounded-lg border ${
                                                user.isActive ? 'bg-card' : 'bg-muted/30 opacity-60'
                                            }`}
                                        >
                                            <div className="flex items-center gap-4">
                                                <Avatar className="h-10 w-10">
                                                    <AvatarFallback className="bg-eucora-deepBlue text-white">
                                                        {user.firstName?.charAt(0)}{user.lastName?.charAt(0)}
                                                    </AvatarFallback>
                                                </Avatar>
                                                <div>
                                                    <p className="font-medium">{user.firstName} {user.lastName}</p>
                                                    <p className="text-sm text-muted-foreground">{user.email}</p>
                                                </div>
                                            </div>
                                            <div className="flex items-center gap-4">
                                                <Badge variant="outline" className={getRoleBadgeColor(user.role)}>
                                                    {user.role}
                                                </Badge>
                                                <Badge variant={user.isActive ? 'default' : 'secondary'}>
                                                    {user.isActive ? 'Active' : 'Inactive'}
                                                </Badge>
                                                <Button 
                                                    variant="ghost" 
                                                    size="sm"
                                                    onClick={() => handleToggleUserStatus(user.id)}
                                                >
                                                    {user.isActive ? <UserMinus className="h-4 w-4" /> : <UserPlus className="h-4 w-4" />}
                                                </Button>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            </CardContent>
                        </Card>
                    </TabsContent>
                )}

                {/* Integrations Tab (Admin Only) */}
                {userIsAdmin && (
                    <TabsContent value="integrations" className="space-y-6">
                        {/* Microsoft Entra ID */}
                        <Card className="glass">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-blue-500/10">
                                            <Cloud className="h-5 w-5 text-blue-500" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">Microsoft Entra ID</CardTitle>
                                            <CardDescription>Single sign-on and directory integration</CardDescription>
                                        </div>
                                    </div>
                                    <Badge variant={integrations.entraId.isConfigured ? 'default' : 'secondary'}>
                                        {integrations.entraId.isConfigured ? 'Connected' : 'Not Configured'}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Tenant ID</Label>
                                        <Input 
                                            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                                            value={integrations.entraId.tenantId}
                                            onChange={(e) => setIntegrations(prev => ({
                                                ...prev,
                                                entraId: { ...prev.entraId, tenantId: e.target.value }
                                            }))}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Client ID</Label>
                                        <Input 
                                            placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                                            value={integrations.entraId.clientId}
                                            onChange={(e) => setIntegrations(prev => ({
                                                ...prev,
                                                entraId: { ...prev.entraId, clientId: e.target.value }
                                            }))}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label>Redirect URI</Label>
                                    <Input 
                                        value={integrations.entraId.redirectUri}
                                        onChange={(e) => setIntegrations(prev => ({
                                            ...prev,
                                            entraId: { ...prev.entraId, redirectUri: e.target.value }
                                        }))}
                                    />
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button onClick={() => handleSaveIntegration('entraId')} className="bg-blue-500 hover:bg-blue-600">
                                    <Save className="mr-2 h-4 w-4" />
                                    Save Configuration
                                </Button>
                            </CardFooter>
                        </Card>

                        {/* CMDB */}
                        <Card className="glass">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-purple-500/10">
                                            <Database className="h-5 w-5 text-purple-500" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">CMDB Integration</CardTitle>
                                            <CardDescription>Configuration management database sync</CardDescription>
                                        </div>
                                    </div>
                                    <Badge variant={integrations.cmdb.isConfigured ? 'default' : 'secondary'}>
                                        {integrations.cmdb.isConfigured ? 'Connected' : 'Not Configured'}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>CMDB Type</Label>
                                        <Select 
                                            value={integrations.cmdb.type}
                                            onValueChange={(value: any) => setIntegrations(prev => ({
                                                ...prev,
                                                cmdb: { ...prev.cmdb, type: value }
                                            }))}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="servicenow">ServiceNow</SelectItem>
                                                <SelectItem value="jira">Jira Assets</SelectItem>
                                                <SelectItem value="freshservice">Freshservice</SelectItem>
                                                <SelectItem value="custom">Custom API</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Sync Interval (minutes)</Label>
                                        <Input 
                                            type="number"
                                            value={integrations.cmdb.syncInterval}
                                            onChange={(e) => setIntegrations(prev => ({
                                                ...prev,
                                                cmdb: { ...prev.cmdb, syncInterval: parseInt(e.target.value) || 60 }
                                            }))}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label>API URL</Label>
                                    <Input 
                                        placeholder="https://your-instance.service-now.com/api"
                                        value={integrations.cmdb.apiUrl}
                                        onChange={(e) => setIntegrations(prev => ({
                                            ...prev,
                                            cmdb: { ...prev.cmdb, apiUrl: e.target.value }
                                        }))}
                                    />
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button onClick={() => handleSaveIntegration('cmdb')} className="bg-purple-500 hover:bg-purple-600">
                                    <Save className="mr-2 h-4 w-4" />
                                    Save Configuration
                                </Button>
                            </CardFooter>
                        </Card>

                        {/* Ticketing Tool */}
                        <Card className="glass">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-green-500/10">
                                            <Activity className="h-5 w-5 text-green-500" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">Ticketing System</CardTitle>
                                            <CardDescription>Change request and incident management</CardDescription>
                                        </div>
                                    </div>
                                    <Badge variant={integrations.ticketing.isConfigured ? 'default' : 'secondary'}>
                                        {integrations.ticketing.isConfigured ? 'Connected' : 'Not Configured'}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>System Type</Label>
                                        <Select 
                                            value={integrations.ticketing.type}
                                            onValueChange={(value: any) => setIntegrations(prev => ({
                                                ...prev,
                                                ticketing: { ...prev.ticketing, type: value }
                                            }))}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="servicenow">ServiceNow</SelectItem>
                                                <SelectItem value="jira">Jira Service Management</SelectItem>
                                                <SelectItem value="freshservice">Freshservice</SelectItem>
                                                <SelectItem value="zendesk">Zendesk</SelectItem>
                                                <SelectItem value="custom">Custom API</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Project Key</Label>
                                        <Input 
                                            placeholder="EUCORA"
                                            value={integrations.ticketing.projectKey}
                                            onChange={(e) => setIntegrations(prev => ({
                                                ...prev,
                                                ticketing: { ...prev.ticketing, projectKey: e.target.value }
                                            }))}
                                        />
                                    </div>
                                </div>
                                <div className="space-y-2">
                                    <Label>API URL</Label>
                                    <Input 
                                        placeholder="https://your-instance.atlassian.net"
                                        value={integrations.ticketing.apiUrl}
                                        onChange={(e) => setIntegrations(prev => ({
                                            ...prev,
                                            ticketing: { ...prev.ticketing, apiUrl: e.target.value }
                                        }))}
                                    />
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button onClick={() => handleSaveIntegration('ticketing')} className="bg-green-500 hover:bg-green-600">
                                    <Save className="mr-2 h-4 w-4" />
                                    Save Configuration
                                </Button>
                            </CardFooter>
                        </Card>

                        {/* Monitoring Tools */}
                        <Card className="glass">
                            <CardHeader>
                                <div className="flex items-center justify-between">
                                    <div className="flex items-center gap-3">
                                        <div className="p-2 rounded-lg bg-orange-500/10">
                                            <Server className="h-5 w-5 text-orange-500" />
                                        </div>
                                        <div>
                                            <CardTitle className="text-lg">Monitoring Integration</CardTitle>
                                            <CardDescription>Observability and alerting integration</CardDescription>
                                        </div>
                                    </div>
                                    <Badge variant={integrations.monitoring.isConfigured ? 'default' : 'secondary'}>
                                        {integrations.monitoring.isConfigured ? 'Connected' : 'Not Configured'}
                                    </Badge>
                                </div>
                            </CardHeader>
                            <CardContent className="space-y-4">
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Platform</Label>
                                        <Select 
                                            value={integrations.monitoring.type}
                                            onValueChange={(value: any) => setIntegrations(prev => ({
                                                ...prev,
                                                monitoring: { ...prev.monitoring, type: value }
                                            }))}
                                        >
                                            <SelectTrigger>
                                                <SelectValue />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem value="datadog">Datadog</SelectItem>
                                                <SelectItem value="splunk">Splunk</SelectItem>
                                                <SelectItem value="elastic">Elastic Stack</SelectItem>
                                                <SelectItem value="prometheus">Prometheus/Grafana</SelectItem>
                                                <SelectItem value="custom">Custom</SelectItem>
                                            </SelectContent>
                                        </Select>
                                    </div>
                                    <div className="space-y-2">
                                        <Label>API URL</Label>
                                        <Input 
                                            placeholder="https://api.datadoghq.com"
                                            value={integrations.monitoring.apiUrl}
                                            onChange={(e) => setIntegrations(prev => ({
                                                ...prev,
                                                monitoring: { ...prev.monitoring, apiUrl: e.target.value }
                                            }))}
                                        />
                                    </div>
                                </div>
                                <div className="grid grid-cols-2 gap-4">
                                    <div className="space-y-2">
                                        <Label>Dashboard URL</Label>
                                        <Input 
                                            placeholder="https://app.datadoghq.com/dashboard/..."
                                            value={integrations.monitoring.dashboardUrl}
                                            onChange={(e) => setIntegrations(prev => ({
                                                ...prev,
                                                monitoring: { ...prev.monitoring, dashboardUrl: e.target.value }
                                            }))}
                                        />
                                    </div>
                                    <div className="space-y-2">
                                        <Label>Alert Webhook</Label>
                                        <Input 
                                            placeholder="https://eucora.example.com/webhooks/alerts"
                                            value={integrations.monitoring.alertWebhook}
                                            onChange={(e) => setIntegrations(prev => ({
                                                ...prev,
                                                monitoring: { ...prev.monitoring, alertWebhook: e.target.value }
                                            }))}
                                        />
                                    </div>
                                </div>
                            </CardContent>
                            <CardFooter>
                                <Button onClick={() => handleSaveIntegration('monitoring')} className="bg-orange-500 hover:bg-orange-600">
                                    <Save className="mr-2 h-4 w-4" />
                                    Save Configuration
                                </Button>
                            </CardFooter>
                        </Card>
                    </TabsContent>
                )}
            </Tabs>
        </div>
    );
}
