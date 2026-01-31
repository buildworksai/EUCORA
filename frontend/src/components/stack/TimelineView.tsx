// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { ScrollArea } from '@/components/ui/scroll-area';
import { Card, CardContent } from '@/components/ui/card';
import { CheckCircle2, Clock, AlertCircle } from 'lucide-react';
import type { DeploymentEvent, StackItem } from '@/routes/deployments/contracts';

interface TimelineViewProps {
  events: DeploymentEvent[];
  onSelectItem: (item: StackItem) => void;
}

const EVENT_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  COMPLETED: CheckCircle2,
  DEPLOYING: Clock,
  FAILED: AlertCircle,
};

export function TimelineView({ events, onSelectItem }: TimelineViewProps) {
  return (
    <ScrollArea className="flex-1">
      <div className="relative p-4">
        <div className="absolute left-8 top-0 bottom-0 w-0.5 bg-border" />
        <div className="space-y-4">
          {events.map((event) => {
            const Icon = EVENT_ICONS[event.status] || Clock;
            return (
              <div key={event.id} className="relative pl-12 cursor-pointer group" onClick={() => onSelectItem(event.item as StackItem)}>
                <div className="absolute left-6 w-4 h-4 rounded-full border-2 border-background bg-eucora-teal">
                  <Icon className="w-2 h-2 text-white" />
                </div>
                <Card className="group-hover:border-eucora-teal/50 transition-colors">
                  <CardContent className="p-3">
                    <div className="flex items-center justify-between">
                      <div>
                        <p className="font-medium">{event.title}</p>
                        <p className="text-sm text-muted-foreground">{event.description}</p>
                      </div>
                      <div className="text-right text-sm text-muted-foreground">
                        <p>{new Date(event.timestamp).toLocaleDateString()}</p>
                        <p>{event.user}</p>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            );
          })}
        </div>
      </div>
    </ScrollArea>
  );
}
