// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { useState } from 'react';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '@/components/ui/tabs';
import { useStackApplications, useDeploymentEvents } from '@/lib/api/hooks/useStack';
import { TreeView } from '@/components/stack/TreeView';
import { TimelineView } from '@/components/stack/TimelineView';
import { DetailPanel } from '@/components/stack/DetailPanel';
import type { StackItem } from './contracts';

export default function ApplicationStack() {
  const [viewMode, setViewMode] = useState<'tree' | 'timeline'>('tree');
  const [selectedItem, setSelectedItem] = useState<StackItem | null>(null);
  const [filters] = useState<{ app_name?: string; status?: string; ring?: string }>({});

  const { data: applications, isLoading } = useStackApplications(filters);
  const { data: events } = useDeploymentEvents(filters);

  return (
    <div className="flex h-full">
      {/* Left Panel: Navigation */}
      <div className="w-[400px] border-r flex flex-col">
        <Tabs value={viewMode} onValueChange={(v) => setViewMode(v as 'tree' | 'timeline')}>
          <TabsList className="w-full">
            <TabsTrigger value="tree" className="flex-1">Tree</TabsTrigger>
            <TabsTrigger value="timeline" className="flex-1">Timeline</TabsTrigger>
          </TabsList>

          <TabsContent value="tree" className="mt-0">
            <TreeView
              applications={applications || []}
              isLoading={isLoading}
              selectedItem={selectedItem}
              onSelectItem={setSelectedItem}
            />
          </TabsContent>

          <TabsContent value="timeline" className="mt-0">
            <TimelineView
              events={events || []}
              onSelectItem={setSelectedItem}
            />
          </TabsContent>
        </Tabs>
      </div>

      {/* Right Panel: Details */}
      <div className="flex-1">
        {selectedItem ? (
          <DetailPanel item={selectedItem} />
        ) : (
          <div className="flex items-center justify-center h-full text-muted-foreground">
            Select an item to view details
          </div>
        )}
      </div>
    </div>
  );
}
