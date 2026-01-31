// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Policy Context Panel Component.
 *
 * Displays policy chunks that are guiding the workflow execution.
 */
import { FileText } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { ScrollArea } from '@/components/ui/scroll-area';
import type { PolicyChunk } from '@/routes/ai/contracts';

interface PolicyContextPanelProps {
  policies: PolicyChunk[];
}

export function PolicyContextPanel({ policies }: PolicyContextPanelProps) {
  return (
    <ScrollArea className="h-full">
      <div className="space-y-4">
        <p className="text-sm text-muted-foreground">
          The following policies are guiding this workflow:
        </p>

        {policies.length === 0 ? (
          <p className="text-sm text-muted-foreground">No policies retrieved for this workflow.</p>
        ) : (
          policies.map((policy, i) => (
            <Card key={i} className="p-3">
              <div className="flex items-start gap-2">
                <FileText className="w-4 h-4 text-eucora-teal mt-0.5 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm">{policy.document_title}</p>
                  <Badge variant="outline" className="mt-1 text-xs">
                    {policy.category}
                  </Badge>
                  <p className="text-xs text-muted-foreground mt-2 line-clamp-4">{policy.content}</p>
                  <Button variant="ghost" size="sm" className="mt-2 text-xs">
                    View Full Document
                  </Button>
                </div>
              </div>
            </Card>
          ))
        )}
      </div>
    </ScrollArea>
  );
}
