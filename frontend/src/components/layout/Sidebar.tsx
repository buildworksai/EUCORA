// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState, useEffect, useMemo, useRef } from 'react';
import { useUIStore } from '@/lib/stores/uiStore';
import { useAuthStore } from '@/lib/stores/authStore';
import { isAdmin, isDemo } from '@/types/auth';
import { usePermissions } from '@/lib/auth/usePermissions';
import { ResourceType } from '@/routes/settings/rbac/contracts';
import { cn } from '@/lib/utils';
import {
    LayoutDashboard, Box, ShieldCheck, Settings, Database, Activity,
    HeartPulse, Sparkles, Shield, Users, Bell, Package, FileKey,
    Briefcase, TrendingUp, DollarSign, PackageCheck, FileText,
    Server, MessageSquare, Search, ClipboardList, BookOpen, Target, CalendarClock,
    ChevronDown, Rocket, Building2, Wrench, Lock, Brain, Cog
} from 'lucide-react';
import { NavLink, useLocation } from 'react-router-dom';
import { LicenseSummaryWidget } from '@/components/licenses';

interface NavItem {
    href: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    adminOnly?: boolean;
    resource?: ResourceType;
    action?: 'read' | 'create' | 'update' | 'delete';
}

interface NavGroup {
    id: string;
    label: string;
    icon: React.ComponentType<{ className?: string }>;
    items: NavItem[];
    adminOnly?: boolean;
}

// Intelligently grouped navigation
const navGroups: NavGroup[] = [
    {
        id: 'overview',
        label: 'Overview',
        icon: LayoutDashboard,
        items: [
            { href: '/dashboard', label: 'Dashboard', icon: LayoutDashboard },
        ]
    },
    {
        id: 'deployment',
        label: 'Deployment',
        icon: Rocket,
        items: [
            { href: '/deployments/stack', label: 'Application Stack', icon: Package, resource: 'applications', action: 'read' },
            { href: '/deploy', label: 'Deployments', icon: Box, resource: 'deployment_intents', action: 'read' },
            { href: '/packaging-requests', label: 'Packaging', icon: PackageCheck, resource: 'packaging_requests', action: 'read' },
            { href: '/planning', label: 'Planning', icon: CalendarClock, resource: 'deployment_plans', action: 'read' },
            { href: '/cab', label: 'CAB Portal', icon: Activity, resource: 'cab_requests', action: 'read' },
        ]
    },
    {
        id: 'assets',
        label: 'Assets',
        icon: Building2,
        items: [
            { href: '/assets', label: 'Inventory', icon: Database, resource: 'assets', action: 'read' },
            { href: '/licenses', label: 'Licenses', icon: FileKey, resource: 'license_inventory', action: 'read' },
            { href: '/portfolios', label: 'Portfolios', icon: Briefcase, resource: 'portfolios', action: 'read' },
            { href: '/discovery', label: 'Discovery', icon: Search, resource: 'discovery_sources', action: 'read' },
        ]
    },
    {
        id: 'operations',
        label: 'Operations',
        icon: Wrench,
        items: [
            { href: '/cmdb', label: 'CMDB', icon: Server, resource: 'cmdb_connections', action: 'read' },
            { href: '/communications', label: 'Communications', icon: MessageSquare, resource: 'change_records', action: 'read' },
            { href: '/sre', label: 'SRE', icon: HeartPulse, resource: 'health_endpoints', action: 'read' },
            { href: '/request-coordination', label: 'Requests', icon: ClipboardList, resource: 'tracked_requests', action: 'read' },
        ]
    },
    {
        id: 'security',
        label: 'Security',
        icon: Lock,
        items: [
            { href: '/compliance', label: 'Compliance', icon: ShieldCheck, resource: 'compliance_data', action: 'read' },
            { href: '/secops', label: 'SecOps', icon: ShieldCheck, resource: 'vulnerabilities', action: 'read' },
            { href: '/audit', label: 'Audit Trail', icon: Database, resource: 'audit_trail', action: 'read' },
            { href: '/sla-governance', label: 'SLA Governance', icon: Target, resource: 'sla_definitions', action: 'read' },
        ]
    },
    {
        id: 'intelligence',
        label: 'Intelligence',
        icon: Brain,
        items: [
            { href: '/ai-agents', label: 'AI Agents', icon: Sparkles, resource: 'ai_agents', action: 'read' },
            { href: '/dex', label: 'DEX & Green IT', icon: HeartPulse, resource: 'dex_data', action: 'read' },
            { href: '/performance', label: 'Performance', icon: TrendingUp, resource: 'portfolio_metrics', action: 'read' },
            { href: '/forecasts', label: 'Forecasts', icon: DollarSign, resource: 'license_forecasts', action: 'read' },
            { href: '/kb-triage', label: 'KB & Triage', icon: BookOpen, resource: 'knowledge_articles', action: 'read' },
        ]
    },
    {
        id: 'system',
        label: 'System',
        icon: Cog,
        items: [
            { href: '/settings', label: 'Settings', icon: Settings, resource: 'platform_settings', action: 'read' },
            { href: '/notifications', label: 'Notifications', icon: Bell },
        ]
    },
    {
        id: 'admin',
        label: 'Admin',
        icon: Shield,
        adminOnly: true,
        items: [
            { href: '/admin/policy-documents', label: 'Policy Documents', icon: FileText, resource: 'policy_documents', action: 'read', adminOnly: true },
            { href: '/admin/demo-data', label: 'Demo Data', icon: Shield, resource: 'platform_settings', action: 'read', adminOnly: true },
        ]
    },
];

// Storage key for persisting collapsed state
const COLLAPSED_GROUPS_KEY = 'eucora-sidebar-collapsed-groups';

function getStoredCollapsedGroups(): string[] {
    try {
        const stored = localStorage.getItem(COLLAPSED_GROUPS_KEY);
        return stored ? JSON.parse(stored) : [];
    } catch {
        return [];
    }
}

function storeCollapsedGroups(groups: string[]): void {
    try {
        localStorage.setItem(COLLAPSED_GROUPS_KEY, JSON.stringify(groups));
    } catch {
        // Ignore storage errors
    }
}

export function Sidebar() {
    const { sidebarOpen: isSidebarOpen } = useUIStore();
    const { user } = useAuthStore();
    const { hasPermission, isAdmin: userIsAdminRBAC } = usePermissions();
    const userIsAdmin = isAdmin(user) || userIsAdminRBAC;
    const userIsDemo = isDemo(user);
    const location = useLocation();

    // Track which groups are collapsed
    const [collapsedGroups, setCollapsedGroups] = useState<Set<string>>(() => 
        new Set(getStoredCollapsedGroups())
    );

    // Persist collapsed state
    useEffect(() => {
        storeCollapsedGroups(Array.from(collapsedGroups));
    }, [collapsedGroups]);

    // Track previous pathname to detect route changes
    const prevPathnameRef = useRef(location.pathname);

    // Auto-expand group containing active route (using RAF to avoid sync setState warning)
    useEffect(() => {
        if (prevPathnameRef.current !== location.pathname) {
            prevPathnameRef.current = location.pathname;
            
            const activeGroup = navGroups.find(group => 
                group.items.some(item => location.pathname.startsWith(item.href))
            );
            
            if (activeGroup && collapsedGroups.has(activeGroup.id)) {
                // Use requestAnimationFrame to defer state update
                requestAnimationFrame(() => {
                    setCollapsedGroups(prev => {
                        const next = new Set(prev);
                        next.delete(activeGroup.id);
                        return next;
                    });
                });
            }
        }
    }, [location.pathname, collapsedGroups]);

    const toggleGroup = (groupId: string) => {
        setCollapsedGroups(prev => {
            const next = new Set(prev);
            if (next.has(groupId)) {
                next.delete(groupId);
            } else {
                next.add(groupId);
            }
            return next;
        });
    };

    // Filter groups and items based on permissions
    const visibleGroups = useMemo(() => {
        return navGroups
            .filter(group => {
                // Admin-only groups
                if (group.adminOnly && !userIsAdmin) return false;
                return true;
            })
            .map(group => ({
                ...group,
                items: group.items.filter(item => {
                    // Admin users see everything
                    if (userIsAdmin) return true;

                    if (item.adminOnly) return false;

                    // Demo users see all read-only pages
                    if (userIsDemo) return true;

                    // Check permission for resource
                    if (item.resource && item.action) {
                        return hasPermission(item.resource, item.action);
                    }

                    return true;
                })
            }))
            .filter(group => group.items.length > 0); // Only show groups with visible items
    }, [userIsAdmin, userIsDemo, hasPermission]);

    return (
        <div className="h-full flex flex-col items-center py-6 bg-gradient-to-b from-white/5 to-transparent">
            {/* Brand */}
            <div className="w-full px-6 mb-6 flex items-center gap-3">
                <div className="p-2 rounded-xl bg-eucora-deepBlue shadow-lg shadow-eucora-deepBlue/40">
                    <img src="/logo.png" alt="EUCORA Logo" className="w-8 h-8 object-contain" />
                </div>
                <div className={cn(
                    "font-bold text-xl tracking-tight transition-all duration-300",
                    !isSidebarOpen && "scale-0 w-0 opacity-0"
                )}>
                    EUCORA
                </div>
            </div>

            {/* Navigation - Scrollable */}
            <nav className="w-full flex-1 min-h-0 px-3 overflow-y-auto scrollbar-thin scrollbar-thumb-white/10 scrollbar-track-transparent">
                {visibleGroups.map((group, groupIndex) => {
                    const isCollapsed = collapsedGroups.has(group.id);
                    const hasActiveItem = group.items.some(item => 
                        location.pathname === item.href || location.pathname.startsWith(item.href + '/')
                    );
                    const GroupIcon = group.icon;

                    return (
                        <div key={group.id} className={cn(groupIndex > 0 && "mt-1")}>
                            {/* Group Header */}
                            <button
                                onClick={() => toggleGroup(group.id)}
                                className={cn(
                                    "w-full flex items-center gap-3 px-3 py-2 rounded-lg transition-all duration-200",
                                    "text-xs font-semibold uppercase tracking-wider",
                                    hasActiveItem 
                                        ? "text-eucora-teal" 
                                        : "text-muted-foreground/70 hover:text-muted-foreground",
                                    group.adminOnly && "text-eucora-gold/70 hover:text-eucora-gold"
                                )}
                            >
                                <GroupIcon className="w-4 h-4 flex-shrink-0" />
                                <span className={cn(
                                    "flex-1 text-left transition-opacity duration-300",
                                    !isSidebarOpen && "opacity-0 hidden"
                                )}>
                                    {group.label}
                                </span>
                                <ChevronDown className={cn(
                                    "w-3.5 h-3.5 transition-transform duration-200",
                                    isCollapsed && "-rotate-90",
                                    !isSidebarOpen && "hidden"
                                )} />
                                {group.adminOnly && (
                                    <Shield className={cn(
                                        "w-3 h-3 text-eucora-gold",
                                        !isSidebarOpen && "hidden"
                                    )} />
                                )}
                            </button>

                            {/* Group Items */}
                            <div className={cn(
                                "overflow-hidden transition-all duration-200",
                                isCollapsed && isSidebarOpen ? "max-h-0 opacity-0" : "max-h-[500px] opacity-100"
                            )}>
                                <div className="space-y-0.5 py-1">
                                    {group.items.map((item) => (
                                        <NavLink
                                            key={item.href}
                                            to={item.href}
                                            className={({ isActive }) =>
                                                cn(
                                                    "flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all duration-200 group relative overflow-hidden",
                                                    isSidebarOpen && "ml-2",
                                                    isActive
                                                        ? "bg-eucora-deepBlue text-white shadow-md shadow-eucora-deepBlue/25 font-medium"
                                                        : "text-muted-foreground hover:bg-white/10 hover:text-foreground hover:translate-x-0.5"
                                                )
                                            }
                                        >
                                            <item.icon className="w-4.5 h-4.5 flex-shrink-0 transition-transform group-hover:scale-110" />
                                            <span className={cn(
                                                "text-sm transition-opacity duration-300",
                                                !isSidebarOpen && "opacity-0 hidden"
                                            )}>
                                                {item.label}
                                            </span>
                                            {/* Hover Glow Effect */}
                                            <div className="absolute inset-0 rounded-xl bg-white/5 opacity-0 group-hover:opacity-100 transition-opacity" />
                                        </NavLink>
                                    ))}
                                </div>
                            </div>

                            {/* Divider between groups */}
                            {groupIndex < visibleGroups.length - 1 && (
                                <div className={cn(
                                    "mx-3 my-2 border-t border-white/5",
                                    !isSidebarOpen && "mx-1"
                                )} />
                            )}
                        </div>
                    );
                })}
            </nav>

            {/* Compact License Widget (collapsed sidebar) */}
            {!isSidebarOpen && (
                <div className="mt-auto px-3 w-full">
                    <LicenseSummaryWidget compact className="mb-2" />
                </div>
            )}

            {/* Footer Status */}
            <div className={cn("mt-auto px-6 w-full", !isSidebarOpen && "hidden")}>
                {/* License Summary Widget (D8.5 Implementation) */}
                <LicenseSummaryWidget className="mb-3" />

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
