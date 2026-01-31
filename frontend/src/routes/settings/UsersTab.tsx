// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState } from 'react';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { UserMinus, UserPlus, Users, Shield } from 'lucide-react';
import { toast } from 'sonner';
import { useRoles, useUserRoles, useAssignRole, useRevokeRole } from '@/lib/auth/usePermissions';
import { Role } from '@/routes/settings/rbac/contracts';
import { PermissionGate } from '@/components/auth/PermissionGate';
import { Loader2 } from 'lucide-react';

// Mock user type - replace with real User type from API
interface User {
  id: string;
  email: string;
  first_name?: string;
  last_name?: string;
  username: string;
  is_active: boolean;
}

export default function UsersTab() {
  const [selectedUserId, setSelectedUserId] = useState<string | null>(null);
  const [isAssigningRole, setIsAssigningRole] = useState(false);
  const [selectedRoleId, setSelectedRoleId] = useState<string>('');
  const [selectedPortfolioScope, setSelectedPortfolioScope] = useState<string>('');
  const [selectedBusinessUnitScope, setSelectedBusinessUnitScope] = useState<string>('');

  // Fetch roles
  const { data: roles, isLoading: rolesLoading } = useRoles();
  const { data: userRoles, isLoading: userRolesLoading } = useUserRoles(selectedUserId || undefined);

  const assignRoleMutation = useAssignRole();
  const revokeRoleMutation = useRevokeRole();

  // Mock users list - replace with real API call
  const [users] = useState<User[]>([
    {
      id: '1',
      email: 'admin@eucora.com',
      username: 'admin',
      first_name: 'Admin',
      last_name: 'User',
      is_active: true,
    },
  ]);

  const handleAssignRole = async () => {
    if (!selectedUserId || !selectedRoleId) {
      toast.error('Please select a user and role');
      return;
    }

    try {
      await assignRoleMutation.mutateAsync({
        userId: selectedUserId,
        data: {
          role_id: selectedRoleId,
          portfolio_scope: selectedPortfolioScope || undefined,
          business_unit_scope: selectedBusinessUnitScope || undefined,
        },
      });
      toast.success('Role assigned successfully');
      setIsAssigningRole(false);
      setSelectedRoleId('');
      setSelectedPortfolioScope('');
      setSelectedBusinessUnitScope('');
    } catch {
      toast.error('Failed to assign role');
    }
  };

  const handleRevokeRole = async (userId: string, roleId: string) => {
    try {
      await revokeRoleMutation.mutateAsync({ userId, roleId });
      toast.success('Role revoked successfully');
    } catch {
      toast.error('Failed to revoke role');
    }
  };

  const getRoleBadgeColor = (roleType: string) => {
    switch (roleType) {
      case 'platform_admin':
        return 'bg-eucora-gold/10 text-eucora-gold border-eucora-gold/30';
      case 'application_manager':
        return 'bg-eucora-deepBlue/10 text-eucora-deepBlue border-eucora-deepBlue/30';
      case 'portfolio_manager':
        return 'bg-eucora-teal/10 text-eucora-teal border-eucora-teal/30';
      case 'packaging_engineer':
        return 'bg-purple-500/10 text-purple-500 border-purple-500/30';
      case 'license_manager':
        return 'bg-blue-500/10 text-blue-500 border-blue-500/30';
      case 'cab_approver':
        return 'bg-orange-500/10 text-orange-500 border-orange-500/30';
      case 'security_reviewer':
        return 'bg-red-500/10 text-red-500 border-red-500/30';
      case 'publisher':
        return 'bg-green-500/10 text-green-500 border-green-500/30';
      case 'auditor':
        return 'bg-gray-500/10 text-gray-500 border-gray-500/30';
      default:
        return 'bg-gray-500/10 text-gray-500 border-gray-500/30';
    }
  };

  return (
    <Card className="glass">
      <CardHeader>
        <div className="flex items-center justify-between">
          <div>
            <CardTitle className="flex items-center gap-2">
              <Users className="h-5 w-5 text-eucora-teal" />
              User Management
            </CardTitle>
            <CardDescription>Manage user accounts and RBAC role assignments</CardDescription>
          </div>
          <PermissionGate resource="users" action="create">
            <Button className="bg-eucora-deepBlue hover:bg-eucora-deepBlue-dark">
              <UserPlus className="mr-2 h-4 w-4" />
              Add User
            </Button>
          </PermissionGate>
        </div>
      </CardHeader>
      <CardContent>
        <div className="space-y-3">
          {users.map((user) => (
            <div
              key={user.id}
              className={`flex items-center justify-between p-4 rounded-lg border ${
                user.is_active ? 'bg-card' : 'bg-muted/30 opacity-60'
              }`}
            >
              <div className="flex items-center gap-4">
                <Avatar className="h-10 w-10">
                  <AvatarFallback className="bg-eucora-deepBlue text-white">
                    {user.first_name?.charAt(0) || user.username.charAt(0)}
                    {user.last_name?.charAt(0)}
                  </AvatarFallback>
                </Avatar>
                <div>
                  <p className="font-medium">
                    {user.first_name} {user.last_name}
                  </p>
                  <p className="text-sm text-muted-foreground">{user.email}</p>
                </div>
              </div>
              <div className="flex items-center gap-4">
                {/* Role badges - would fetch from useUserRoles */}
                <Badge variant={user.is_active ? 'default' : 'secondary'}>
                  {user.is_active ? 'Active' : 'Inactive'}
                </Badge>
                <PermissionGate resource="roles" action="update">
                  <Button
                    variant="ghost"
                    size="sm"
                    onClick={() => {
                      setSelectedUserId(user.id);
                      setIsAssigningRole(true);
                    }}
                  >
                    <Shield className="h-4 w-4 mr-1" />
                    Manage Roles
                  </Button>
                </PermissionGate>
              </div>
            </div>
          ))}
        </div>

        {/* Role Assignment Dialog */}
        <Dialog open={isAssigningRole} onOpenChange={setIsAssigningRole}>
          <DialogContent className="glass max-w-2xl">
            <DialogHeader>
              <DialogTitle>Manage User Roles</DialogTitle>
              <DialogDescription>Assign or revoke roles for this user</DialogDescription>
            </DialogHeader>
            <div className="space-y-6 py-4">
              {/* Current Roles */}
              <div>
                <Label className="mb-2 block">Current Roles</Label>
                {userRolesLoading ? (
                  <Loader2 className="h-4 w-4 animate-spin" />
                ) : userRoles && userRoles.length > 0 ? (
                  <div className="space-y-2">
                    {userRoles.map((userRole) => (
                      <div
                        key={userRole.id}
                        className="flex items-center justify-between p-3 rounded-lg border bg-card"
                      >
                        <div className="flex items-center gap-3">
                          <Badge variant="outline" className={getRoleBadgeColor(userRole.role.role_type)}>
                            {userRole.role.display_name}
                          </Badge>
                          {userRole.portfolio_name && (
                            <span className="text-sm text-muted-foreground">
                              Portfolio: {userRole.portfolio_name}
                            </span>
                          )}
                          {userRole.business_unit_scope && (
                            <span className="text-sm text-muted-foreground">
                              BU: {userRole.business_unit_scope}
                            </span>
                          )}
                        </div>
                        <Button
                          variant="ghost"
                          size="sm"
                          onClick={() => handleRevokeRole(selectedUserId!, userRole.role.id)}
                        >
                          <UserMinus className="h-4 w-4" />
                        </Button>
                      </div>
                    ))}
                  </div>
                ) : (
                  <p className="text-sm text-muted-foreground">No roles assigned</p>
                )}
              </div>

              {/* Assign New Role */}
              <div className="space-y-4 border-t pt-4">
                <Label className="text-base font-semibold">Assign New Role</Label>
                <div className="space-y-4">
                  <div className="space-y-2">
                    <Label>Role</Label>
                    <Select value={selectedRoleId} onValueChange={setSelectedRoleId}>
                      <SelectTrigger>
                        <SelectValue placeholder="Select a role" />
                      </SelectTrigger>
                      <SelectContent>
                        {rolesLoading ? (
                          <SelectItem value="loading" disabled>
                            Loading...
                          </SelectItem>
                        ) : (
                          roles?.map((role: Role) => (
                            <SelectItem key={role.id} value={role.id}>
                              {role.display_name}
                            </SelectItem>
                          ))
                        )}
                      </SelectContent>
                    </Select>
                  </div>

                  <div className="space-y-2">
                    <Label>Portfolio Scope (Optional)</Label>
                    <Input
                      value={selectedPortfolioScope}
                      onChange={(e) => setSelectedPortfolioScope(e.target.value)}
                      placeholder="Leave empty for global scope"
                    />
                  </div>

                  <div className="space-y-2">
                    <Label>Business Unit Scope (Optional)</Label>
                    <Input
                      value={selectedBusinessUnitScope}
                      onChange={(e) => setSelectedBusinessUnitScope(e.target.value)}
                      placeholder="Leave empty for global scope"
                    />
                  </div>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" onClick={() => setIsAssigningRole(false)}>
                Cancel
              </Button>
              <Button
                onClick={handleAssignRole}
                disabled={!selectedRoleId || assignRoleMutation.isPending}
                className="bg-eucora-teal hover:bg-eucora-teal-dark"
              >
                {assignRoleMutation.isPending ? (
                  <>
                    <Loader2 className="mr-2 h-4 w-4 animate-spin" />
                    Assigning...
                  </>
                ) : (
                  'Assign Role'
                )}
              </Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </CardContent>
    </Card>
  );
}
