// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Badge } from '@/components/ui/badge';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Separator } from '@/components/ui/separator';
import { Switch } from '@/components/ui/switch';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { Bell, Shield, Users } from 'lucide-react';
import { useAuthStore } from '@/lib/stores/authStore';
import type { UserRole } from '@/types/auth';

const getRoleBadgeColor = (role: UserRole) => {
  switch (role) {
    case 'admin':
      return 'bg-eucora-gold/10 text-eucora-gold border-eucora-gold/30';
    case 'operator':
      return 'bg-eucora-deepBlue/10 text-eucora-deepBlue border-eucora-deepBlue/30';
    case 'demo':
      return 'bg-eucora-teal/10 text-eucora-teal border-eucora-teal/30';
    default:
      return 'bg-gray-500/10 text-gray-500 border-gray-500/30';
  }
};

export default function ProfileTab() {
  const { user: currentUser } = useAuthStore();

  return (
    <>
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
                {currentUser?.firstName?.charAt(0)}
                {currentUser?.lastName?.charAt(0)}
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
    </>
  );
}
