// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { usePolicyTemplates } from '@/lib/api/hooks/usePolicies';
import { Building, Shield, ShoppingBag, FileText, Globe, Code } from 'lucide-react';
import { Loader2 } from 'lucide-react';
import type { PolicyTemplate } from '@/routes/policies/contracts';

const TEMPLATE_ICONS: Record<string, React.ComponentType<{ className?: string }>> = {
  enterprise: Building,
  security: Shield,
  optional: ShoppingBag,
  productivity: FileText,
  browser: Globe,
  development: Code,
};

interface TemplatePickerDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSelect: (template: PolicyTemplate) => void;
  platform?: string;
}

export function TemplatePickerDialog({ open, onOpenChange, onSelect, platform }: TemplatePickerDialogProps) {
  const { data: templates, isLoading } = usePolicyTemplates({ platform });

  const handleSelect = (template: PolicyTemplate) => {
    onSelect(template);
    onOpenChange(false);
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-w-4xl max-h-[80vh] overflow-y-auto">
        <DialogHeader>
          <DialogTitle>Select Policy Template</DialogTitle>
          <DialogDescription>Choose a pre-configured template to apply to this policy</DialogDescription>
        </DialogHeader>

        {isLoading ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-6 h-6 animate-spin text-muted-foreground" />
          </div>
        ) : (
          <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-3 mt-4">
            {templates?.map((template) => {
              const Icon = TEMPLATE_ICONS[template.template_type] || Building;
              return (
                <div
                  key={template.id}
                  className="border rounded-lg p-4 hover:border-eucora-teal/50 transition-colors cursor-pointer"
                  onClick={() => handleSelect(template)}
                >
                  <div className="flex items-start gap-3">
                    <Icon className="w-5 h-5 text-eucora-teal mt-0.5 flex-shrink-0" />
                    <div className="flex-1 min-w-0">
                      <h3 className="font-semibold text-sm">{template.name}</h3>
                      <p className="text-xs text-muted-foreground mt-1 line-clamp-2">{template.description}</p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </DialogContent>
    </Dialog>
  );
}
