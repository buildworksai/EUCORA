// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import type { StackItem } from '@/routes/deployments/contracts';

interface DetailPanelProps {
  item: StackItem;
}

export function DetailPanel({ item }: DetailPanelProps) {
  return (
    <div className="p-6 space-y-6">
      <Card>
        <CardHeader>
          <CardTitle>{item.type.charAt(0).toUpperCase() + item.type.slice(1)} Details</CardTitle>
        </CardHeader>
        <CardContent>
          <pre className="text-xs overflow-auto">{JSON.stringify(item, null, 2)}</pre>
        </CardContent>
      </Card>
    </div>
  );
}
