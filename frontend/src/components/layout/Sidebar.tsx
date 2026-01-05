// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useUIStore } from '@/lib/stores/uiStore';
import { useAuthStore } from '@/lib/stores/authStore';
import { isAdmin, isDemo, hasPermission } from '@/types/auth';
import { cn } from '@/lib/utils';
import { 
    LayoutDashboard, Box, ShieldCheck, Settings, Database, Activity, 
    HeartPulse, Sparkles, Shield, Users, Link2 
} from 'lucide-react';
import { NavLink } from 'react-router-dom';

interface NavItem {
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    adminOnly?: boolean;
    resource?: string;
}

const navItems: NavItem[] = [
    { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard, resource: 'dashboard' },
    { href: '/dex', label: 'DEX & Green IT', icon: HeartPulse, resource: 'deployments' },
    { href: '/assets', label: 'Asset Inventory', icon: Database, resource: 'assets' },
    { href: '/compliance', label: 'Compliance', icon: ShieldCheck, resource: 'compliance' },
    { href: '/deploy', label: 'Deployments', icon: Box, resource: 'deployments' },
    { href: '/cab', label: 'CAB Portal', icon: Activity, resource: 'cab' },
    { href: '/ai-agents', label: 'AI Agents', icon: Sparkles, resource: 'ai' },
    { href: '/audit', label: 'Audit Trail', icon: Database, resource: 'audit' },
    { href: '/settings', label: 'Settings', icon: Settings, resource: 'settings' },
];

export function Sidebar() {
    const { sidebarOpen: isSidebarOpen } = useUIStore();
    const { user } = useAuthStore();
    const userIsAdmin = isAdmin(user);
    const userIsDemo = isDemo(user);

    // Filter nav items based on user permissions
    const visibleNavItems = navItems.filter(item => {
        // Admin users see everything
        if (userIsAdmin) return true;
        
        // Demo users see all read-only pages
        if (userIsDemo) return true;
        
        // Check permission for resource
        if (item.resource) {
            return hasPermission(user, item.resource, 'read');
        }
        
        return true;
    });

    return (
        <div className="h-full flex flex-col items-center py-6 bg-gradient-to-b from-white/5 to-transparent">
            {/* Brand */}
            <div className="w-full px-6 mb-8 flex items-center gap-3">
                <div className="p-2 rounded-xl bg-eucora-deepBlue shadow-lg shadow-eucora-deepBlue/40">
                    <img src="/logo.png" alt="EUCORA Logo" className="w-8 h-8 object-contain" />
                </div>
                <div className={`font-bold text-xl tracking-tight transition-all duration-300 ${!isSidebarOpen && "scale-0 w-0 opacity-0"}`}>
                    EUCORA
                </div>
            </div>

            {/* Navigation */}
            <nav className="w-full flex-1 px-3 space-y-1">
                {visibleNavItems.map((item) => (
                    <NavLink
                        key={item.href}
                        to={item.href}
                        className={({ isActive }) =>
                            cn(
                                "flex items-center gap-3 px-3 py-3 rounded-xl transition-all duration-200 group relative overflow-hidden",
                                isActive
                                    ? "bg-eucora-deepBlue text-white shadow-md shadow-eucora-deepBlue/25 font-medium translate-x-1"
                                    : "text-muted-foreground hover:bg-white/10 hover:text-foreground hover:translate-x-1"
                            )
                        }
                    >
                        <item.icon className={cn("w-5 h-5 transition-transform group-hover:scale-110")} />
                        <span className={cn("transition-opacity duration-300", !isSidebarOpen && "opacity-0 hidden")}>
                            {item.label}
                        </span>
                        {item.adminOnly && (
                            <Shield className={cn("w-3 h-3 text-eucora-gold ml-auto", !isSidebarOpen && "hidden")} />
                        )}
                        {/* Hover Glow Effect */}
                        <div className="absolute inset-0 rounded-xl bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                    </NavLink>
                ))}
            </nav>

            {/* Footer Status */}
            <div className={`mt-auto px-6 w-full ${!isSidebarOpen && "hidden"}`}>
                <div className="p-4 rounded-xl bg-white/5 border border-white/5">
                    <div className="flex items-center justify-between mb-2">
                        <span className="text-xs font-semibold text-muted-foreground uppercase">System Status</span>
                        <span className="h-2 w-2 rounded-full bg-eucora-green animate-pulse" />
                    </div>
                    <div className="text-xs text-muted-foreground">
                        <div className="flex justify-between">
                            <span>API</span>
                            <span className="text-eucora-green">Operational</span>
                        </div>
                        <div className="flex justify-between mt-1">
                            <span>Factory</span>
                            <span className="text-eucora-gold">Busy</span>
                        </div>
                    </div>
                </div>
                
                {/* User Role Indicator */}
                <div className="mt-3 p-3 rounded-lg bg-white/5">
                    <div className="flex items-center gap-2 text-xs">
                        {userIsAdmin ? (
                            <>
                                <Shield className="w-4 h-4 text-eucora-gold" />
                                <span className="text-eucora-gold">Admin Access</span>
                            </>
                        ) : userIsDemo ? (
                            <>
                                <Sparkles className="w-4 h-4 text-eucora-teal" />
                                <span className="text-eucora-teal">Demo Mode</span>
                            </>
                        ) : (
                            <>
                                <Users className="w-4 h-4 text-muted-foreground" />
                                <span className="text-muted-foreground">{user?.role || 'User'}</span>
                            </>
                        )}
                    </div>
                </div>
                
                <div className="mt-4 text-[10px] text-center text-muted-foreground/50">
                    Built by BuildWorks.AI
                </div>
            </div>
        </div>
    );
}
