// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { useUIStore } from '@/lib/stores/uiStore';
import { useAuthStore } from '@/lib/stores/authStore';
import { isAdmin, isDemo } from '@/types/auth';
import { Moon, Sun, Menu, Bell, LogOut, User, Shield, Sparkles, CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import {
    DropdownMenu,
    DropdownMenuContent,
    DropdownMenuItem,
    DropdownMenuSeparator,
    DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { useNavigate } from 'react-router-dom';
import { usePendingApprovals } from '@/lib/api/hooks/useCAB';
import { useDeployments } from '@/lib/api/hooks/useDeployments';
import { formatDistanceToNow } from 'date-fns';

export function Topbar() {
    const navigate = useNavigate();
    const { toggleSidebar, setTheme } = useUIStore();
    const { user, logout } = useAuthStore();
    const { data: pendingApprovals = [] } = usePendingApprovals();
    const { data: deployments = [] } = useDeployments();

    // Calculate notification count
    const notificationCount = pendingApprovals.length +
        deployments.filter(d => d.status === 'AWAITING_CAB' || d.status === 'DEPLOYING').length;

    const handleLogout = async () => {
        await logout();
        navigate('/login');
    };

    const getRoleBadge = () => {
        if (!user) return null;

        switch (user.role) {
            case 'admin':
                return (
                    <Badge variant="outline" className="text-eucora-gold border-eucora-gold/50 bg-eucora-gold/10">
                        <Shield className="w-3 h-3 mr-1" />
                        Admin
                    </Badge>
                );
            case 'demo':
                return (
                    <Badge variant="outline" className="text-eucora-teal border-eucora-teal/50 bg-eucora-teal/10">
                        <Sparkles className="w-3 h-3 mr-1" />
                        Demo
                    </Badge>
                );
            case 'operator':
                return (
                    <Badge variant="outline" className="text-eucora-deepBlue border-eucora-deepBlue/50 bg-eucora-deepBlue/10">
                        Operator
                    </Badge>
                );
            default:
                return (
                    <Badge variant="secondary">
                        Viewer
                    </Badge>
                );
        }
    };

    const getInitials = () => {
        if (!user) return 'U';
        return `${user.firstName?.charAt(0) || ''}${user.lastName?.charAt(0) || ''}`.toUpperCase() || 'U';
    };

    return (
        <header className="sticky top-0 z-30 flex h-16 items-center gap-4 border-b bg-background/50 px-6 backdrop-blur-md glass">
            <Button variant="ghost" size="icon" onClick={toggleSidebar} className="lg:hidden">
                <Menu className="h-5 w-5" />
                <span className="sr-only">Toggle Sidebar</span>
            </Button>

            <div className="flex flex-1 items-center gap-4">
                <h1 className="text-lg font-semibold tracking-tight text-foreground/80 hidden md:block">
                    EUCORA - Enterprise Endpoint Application Packaging & Deployment Factory
                </h1>
                {isDemo(user) && (
                    <Badge variant="outline" className="text-eucora-teal border-eucora-teal/30 bg-eucora-teal/5 text-xs">
                        Demo Environment
                    </Badge>
                )}
            </div>

            <div className="flex items-center gap-3">
                {/* Notifications */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon" className="relative">
                            <Bell className="h-5 w-5 text-muted-foreground" />
                            {notificationCount > 0 && (
                                <span className="absolute top-1 right-1 w-2 h-2 bg-eucora-red rounded-full animate-pulse" />
                            )}
                            <span className="sr-only">Notifications</span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-80">
                        <div className="px-3 py-2 border-b border-border">
                            <div className="flex items-center justify-between">
                                <h3 className="text-sm font-semibold">Notifications</h3>
                                {notificationCount > 0 && (
                                    <Badge variant="secondary" className="text-xs">
                                        {notificationCount} new
                                    </Badge>
                                )}
                            </div>
                        </div>
                        <ScrollArea className="h-[400px]">
                            {notificationCount === 0 ? (
                                <div className="px-3 py-8 text-center text-sm text-muted-foreground">
                                    No new notifications
                                </div>
                            ) : (
                                <div className="py-2">
                                    {/* Pending CAB Approvals */}
                                    {pendingApprovals.slice(0, 5).map((approval) => (
                                        <DropdownMenuItem
                                            key={approval.correlation_id}
                                            className="flex flex-col items-start gap-1 px-3 py-3 cursor-pointer hover:bg-muted/50"
                                            onClick={() => navigate('/cab')}
                                        >
                                            <div className="flex items-start gap-2 w-full">
                                                <Clock className="h-4 w-4 text-eucora-gold mt-0.5 flex-shrink-0" />
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-medium truncate">
                                                        CAB Review: {approval.app_name} {approval.version}
                                                    </p>
                                                    <p className="text-xs text-muted-foreground">
                                                        Risk: {approval.risk_score} • {formatDistanceToNow(new Date(approval.submitted_at), { addSuffix: true })}
                                                    </p>
                                                </div>
                                            </div>
                                        </DropdownMenuItem>
                                    ))}

                                    {/* Deployments in progress */}
                                    {deployments
                                        .filter(d => d.status === 'DEPLOYING' || d.status === 'AWAITING_CAB')
                                        .slice(0, 5)
                                        .map((deployment) => (
                                            <DropdownMenuItem
                                                key={deployment.correlation_id}
                                                className="flex flex-col items-start gap-1 px-3 py-3 cursor-pointer hover:bg-muted/50"
                                                onClick={() => navigate('/dashboard')}
                                            >
                                                <div className="flex items-start gap-2 w-full">
                                                    {deployment.status === 'DEPLOYING' ? (
                                                        <CheckCircle2 className="h-4 w-4 text-eucora-green mt-0.5 flex-shrink-0" />
                                                    ) : (
                                                        <AlertCircle className="h-4 w-4 text-eucora-gold mt-0.5 flex-shrink-0" />
                                                    )}
                                                    <div className="flex-1 min-w-0">
                                                        <p className="text-sm font-medium truncate">
                                                            {deployment.status === 'DEPLOYING' ? 'Deploying' : 'Awaiting CAB'}: {deployment.app_name} {deployment.version}
                                                        </p>
                                                        <p className="text-xs text-muted-foreground">
                                                            Ring: {deployment.target_ring} • {formatDistanceToNow(new Date(deployment.created_at), { addSuffix: true })}
                                                        </p>
                                                    </div>
                                                </div>
                                            </DropdownMenuItem>
                                        ))}
                                </div>
                            )}
                        </ScrollArea>
                        {notificationCount > 0 && (
                            <>
                                <DropdownMenuSeparator />
                                <DropdownMenuItem
                                    className="cursor-pointer justify-center"
                                    onClick={() => navigate('/notifications')}
                                >
                                    View all notifications
                                </DropdownMenuItem>
                            </>
                        )}
                    </DropdownMenuContent>
                </DropdownMenu>

                {/* Theme Toggle */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" size="icon">
                            <Sun className="h-5 w-5 rotate-0 scale-100 transition-all dark:-rotate-90 dark:scale-0" />
                            <Moon className="absolute h-5 w-5 rotate-90 scale-0 transition-all dark:rotate-0 dark:scale-100" />
                            <span className="sr-only">Toggle theme</span>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end">
                        <DropdownMenuItem onClick={() => setTheme('light')}>Light</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => setTheme('dark')}>Dark</DropdownMenuItem>
                        <DropdownMenuItem onClick={() => setTheme('system')}>System</DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>

                {/* User Menu */}
                <DropdownMenu>
                    <DropdownMenuTrigger asChild>
                        <Button variant="ghost" className="flex items-center gap-3 px-2 h-auto py-2">
                            <Avatar className="h-9 w-9 border-2 border-eucora-deepBlue/30">
                                <AvatarImage src={user?.avatar} />
                                <AvatarFallback className="bg-eucora-deepBlue text-white text-sm font-medium">
                                    {getInitials()}
                                </AvatarFallback>
                            </Avatar>
                            <div className="text-left hidden md:block">
                                <p className="text-sm font-medium leading-none">
                                    {user?.firstName} {user?.lastName}
                                </p>
                                <p className="text-xs text-muted-foreground mt-0.5">
                                    {user?.email}
                                </p>
                            </div>
                        </Button>
                    </DropdownMenuTrigger>
                    <DropdownMenuContent align="end" className="w-64">
                        <div className="px-3 py-3 border-b border-border">
                            <div className="flex items-center gap-3">
                                <Avatar className="h-10 w-10 border-2 border-eucora-deepBlue/30">
                                    <AvatarImage src={user?.avatar} />
                                    <AvatarFallback className="bg-eucora-deepBlue text-white">
                                        {getInitials()}
                                    </AvatarFallback>
                                </Avatar>
                                <div className="flex-1 min-w-0">
                                    <p className="text-sm font-medium truncate">
                                        {user?.firstName} {user?.lastName}
                                    </p>
                                    <p className="text-xs text-muted-foreground truncate">
                                        {user?.email}
                                    </p>
                                </div>
                            </div>
                            <div className="mt-2 flex items-center gap-2">
                                {getRoleBadge()}
                                {user?.department && (
                                    <span className="text-xs text-muted-foreground">
                                        {user.department}
                                    </span>
                                )}
                            </div>
                        </div>
                        <DropdownMenuItem onClick={() => navigate('/settings')} className="cursor-pointer">
                            <User className="mr-2 h-4 w-4" />
                            Profile & Settings
                        </DropdownMenuItem>
                        {isAdmin(user) && (
                            <DropdownMenuItem onClick={() => navigate('/settings?tab=users')} className="cursor-pointer">
                                <Shield className="mr-2 h-4 w-4" />
                                User Management
                            </DropdownMenuItem>
                        )}
                        <DropdownMenuSeparator />
                        <DropdownMenuItem onClick={handleLogout} className="text-red-500 focus:text-red-500 cursor-pointer">
                            <LogOut className="mr-2 h-4 w-4" />
                            Sign Out
                        </DropdownMenuItem>
                    </DropdownMenuContent>
                </DropdownMenu>
            </div>
        </header>
    );
}
