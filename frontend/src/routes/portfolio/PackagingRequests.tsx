// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { usePackagingRequests, useMyPackagingRequests, useAssignedPackagingRequests } from '../../lib/api/hooks/usePortfolioManagement';
import { Card, CardContent, CardHeader, CardTitle } from '../../components/ui/card';
import { Badge } from '../../components/ui/badge';
import { Alert, AlertDescription } from '../../components/ui/alert';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../../components/ui/tabs';
import { Loader2, Package, Clock, CheckCircle2, AlertTriangle, User } from 'lucide-react';
import type { PackagingRequest } from '../../types/portfolio';

export function PackagingRequests() {
  const { data: allRequests, isLoading: allLoading, error } = usePackagingRequests({ ordering: '-created_at' });
  const { data: myRequests, isLoading: myLoading } = useMyPackagingRequests();
  const { data: assignedRequests, isLoading: assignedLoading } = useAssignedPackagingRequests();

  const getPriorityColor = (priority: string) => {
    switch (priority) {
      case 'URGENT': return 'destructive';
      case 'HIGH': return 'default';
      case 'NORMAL': return 'secondary';
      case 'LOW': return 'outline';
      default: return 'secondary';
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'COMPLETED': return 'text-green-600';
      case 'IN_PROGRESS': return 'text-blue-600';
      case 'PENDING': return 'text-amber-600';
      case 'CANCELLED': return 'text-gray-600';
      default: return 'text-gray-600';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'COMPLETED': return <CheckCircle2 className="h-4 w-4" />;
      case 'IN_PROGRESS': return <Clock className="h-4 w-4 animate-pulse" />;
      case 'PENDING': return <AlertTriangle className="h-4 w-4" />;
      default: return <Package className="h-4 w-4" />;
    }
  };

  const renderRequest = (request: PackagingRequest) => (
    <Card key={request.id} className="hover:shadow-md transition-shadow">
      <CardHeader>
        <div className="flex items-start justify-between">
          <div className="space-y-1 flex-1">
            <div className="flex items-center gap-2">
              <CardTitle className="text-base">{request.application_name || 'Application'}</CardTitle>
              <Badge variant={getPriorityColor(request.priority) as 'destructive' | 'default' | 'secondary' | 'outline'}>{request.priority}</Badge>
            </div>
            <p className="text-sm text-muted-foreground">
              Requested by {request.requested_by_name} on{' '}
              {new Date(request.created_at).toLocaleDateString()}
            </p>
          </div>
          <div className={`flex items-center gap-1 ${getStatusColor(request.status)}`}>
            {getStatusIcon(request.status)}
            <span className="text-sm font-medium">{request.status.replace('_', ' ')}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {/* Business Justification */}
        <div>
          <p className="text-sm font-medium mb-1">Business Justification</p>
          <p className="text-sm text-muted-foreground">{request.business_justification}</p>
        </div>

        {/* Target Platforms */}
        <div>
          <p className="text-sm font-medium mb-2">Target Platforms</p>
          <div className="flex flex-wrap gap-2">
            {request.target_platforms.map((platform: string, idx: number) => (
              <Badge key={idx} variant="outline">{platform}</Badge>
            ))}
          </div>
        </div>

        {/* Special Requirements */}
        {request.special_requirements && (
          <div>
            <p className="text-sm font-medium mb-1">Special Requirements</p>
            <p className="text-sm text-muted-foreground">{request.special_requirements}</p>
          </div>
        )}

        {/* Assignment */}
        {request.assigned_to_name && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-muted/50">
            <User className="h-4 w-4 text-muted-foreground" />
            <span className="text-sm">
              Assigned to <strong>{request.assigned_to_name}</strong>
            </span>
            {request.assigned_at && (
              <span className="text-xs text-muted-foreground">
                ({new Date(request.assigned_at).toLocaleDateString()})
              </span>
            )}
          </div>
        )}

        {/* Turnaround Time */}
        {request.turnaround_time_hours !== null && (
          <div className="flex items-center gap-2 p-3 rounded-lg bg-green-50 dark:bg-green-950 border border-green-200">
            <Clock className="h-4 w-4 text-green-600" />
            <span className="text-sm text-green-900 dark:text-green-100">
              Completed in <strong>{request.turnaround_time_hours.toFixed(1)}</strong> hours
            </span>
          </div>
        )}
      </CardContent>
    </Card>
  );

  if (error) {
    return (
      <Alert variant="destructive">
        <AlertTriangle className="h-4 w-4" />
        <AlertDescription>Failed to load packaging requests. Please try again.</AlertDescription>
      </Alert>
    );
  }

  return (
    <div className="space-y-6 p-6">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Packaging Requests</h1>
        <p className="text-muted-foreground">Workflow tracking from Application Manager to Packaging Engineer</p>
      </div>

      <Tabs defaultValue="all" className="space-y-4">
        <TabsList>
          <TabsTrigger value="all">
            All Requests
            {!allLoading && allRequests && (
              <Badge variant="secondary" className="ml-2">{allRequests.results.length}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="my-requests">
            My Requests
            {!myLoading && myRequests && (
              <Badge variant="secondary" className="ml-2">{myRequests.length}</Badge>
            )}
          </TabsTrigger>
          <TabsTrigger value="assigned">
            Assigned to Me
            {!assignedLoading && assignedRequests && (
              <Badge variant="secondary" className="ml-2">{assignedRequests.length}</Badge>
            )}
          </TabsTrigger>
        </TabsList>

        {/* All Requests */}
        <TabsContent value="all" className="space-y-4">
          {allLoading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : allRequests && allRequests.results.length > 0 ? (
            <div className="grid gap-4">
              {allRequests.results.map(renderRequest)}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Package className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Requests Found</h3>
                <p className="text-muted-foreground text-center">
                  No packaging requests available.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* My Requests */}
        <TabsContent value="my-requests" className="space-y-4">
          {myLoading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : myRequests && myRequests.length > 0 ? (
            <div className="grid gap-4">
              {myRequests.map(renderRequest)}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Package className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Requests</h3>
                <p className="text-muted-foreground text-center">
                  You haven't created any packaging requests yet.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>

        {/* Assigned to Me */}
        <TabsContent value="assigned" className="space-y-4">
          {assignedLoading ? (
            <div className="flex items-center justify-center h-48">
              <Loader2 className="h-8 w-8 animate-spin text-primary" />
            </div>
          ) : assignedRequests && assignedRequests.length > 0 ? (
            <div className="grid gap-4">
              {assignedRequests.map(renderRequest)}
            </div>
          ) : (
            <Card>
              <CardContent className="flex flex-col items-center justify-center py-12">
                <Package className="h-16 w-16 text-muted-foreground mb-4" />
                <h3 className="text-lg font-semibold mb-2">No Assigned Requests</h3>
                <p className="text-muted-foreground text-center">
                  You don't have any packaging requests assigned to you.
                </p>
              </CardContent>
            </Card>
          )}
        </TabsContent>
      </Tabs>
    </div>
  );
}
