// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Tooltip, TooltipContent, TooltipTrigger, TooltipProvider } from './tooltip';

describe('Tooltip', () => {
  it('renders tooltip content when open', () => {
    render(
      <TooltipProvider>
        <Tooltip open>
          <TooltipTrigger>Trigger</TooltipTrigger>
          <TooltipContent>Tooltip</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    );

    expect(screen.getAllByText('Tooltip').length).toBeGreaterThan(0);
  });
});
