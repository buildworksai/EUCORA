// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { ScrollArea } from '@/components/ui/scroll-area';
import { Collapsible, CollapsibleContent, CollapsibleTrigger } from '@/components/ui/collapsible';
import { Badge } from '@/components/ui/badge';
import { ChevronRight, Package } from 'lucide-react';
import { cn } from '@/lib/utils';
import { useState } from 'react';
import type { StackApplication, StackItem } from '@/routes/deployments/contracts';

interface TreeViewProps {
  applications: StackApplication[];
  isLoading: boolean;
  selectedItem: StackItem | null;
  onSelectItem: (item: StackItem) => void;
}

export function TreeView({ applications, isLoading, selectedItem, onSelectItem }: TreeViewProps) {
  if (isLoading) {
    return <div className="p-4 text-muted-foreground">Loading...</div>;
  }

  return (
    <ScrollArea className="flex-1">
      <div className="p-4 space-y-1">
        {applications.map((app) => (
          <ApplicationNode
            key={app.id}
            application={app}
            isSelected={selectedItem?.id === app.id}
            onSelect={() => onSelectItem({ type: 'application' as const, ...app })}
          />
        ))}
      </div>
    </ScrollArea>
  );
}

function ApplicationNode({
  application,
  isSelected,
  onSelect,
}: {
  application: StackApplication;
  isSelected: boolean;
  onSelect: () => void;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="w-full" onClick={onSelect}>
        <div
          className={cn(
            'flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors font-semibold cursor-pointer',
            isSelected && 'bg-eucora-teal/10'
          )}
        >
          <ChevronRight className={cn('w-5 h-5 text-muted-foreground transition-transform', isOpen && 'rotate-90')} />
          <Package className="w-4 h-4 text-eucora-teal" />
          <span className="truncate flex-1">{application.name}</span>
          <Badge variant="outline" className="text-xs">
            {application.versions.length}
          </Badge>
        </div>
      </CollapsibleTrigger>
      {isOpen && (
        <CollapsibleContent className="pl-6 space-y-1 mt-1 border-l border-white/10">
          {application.versions.map((version) => (
            <VersionNode key={version.version} version={version} applicationId={application.id} />
          ))}
        </CollapsibleContent>
      )}
    </Collapsible>
  );
}

interface Deployment {
  id: string;
  target_ring: string;
  status: string;
}

function VersionNode({
  version,
}: {
  version: { version: string; deployments: Deployment[] };
  applicationId?: string;
}) {
  const [isOpen, setIsOpen] = useState(false);

  return (
    <Collapsible open={isOpen} onOpenChange={setIsOpen}>
      <CollapsibleTrigger className="w-full">
        <div className="flex items-center gap-2 px-3 py-2 rounded-lg hover:bg-white/5 transition-colors text-sm cursor-pointer">
          <ChevronRight className={cn('w-4 h-4 text-muted-foreground transition-transform', isOpen && 'rotate-90')} />
          <span className="font-mono text-xs">v{version.version}</span>
          <Badge variant="secondary" className="text-xs">
            {version.deployments.length}
          </Badge>
        </div>
      </CollapsibleTrigger>
      {isOpen && (
        <CollapsibleContent className="pl-6 space-y-1 mt-1 border-l border-white/10">
          {version.deployments.map((deployment) => (
            <div
              key={deployment.id}
              className="flex items-center justify-between py-2 px-3 rounded-lg hover:bg-white/5 transition-colors text-xs"
            >
              <span className="text-muted-foreground">{deployment.target_ring}</span>
              <Badge variant="outline" className="text-xs">
                {deployment.status}
              </Badge>
            </div>
          ))}
        </CollapsibleContent>
      )}
    </Collapsible>
  );
}
