# Test Generation Guide

## Remaining Components to Test

### UI Components (23 total, 6 tested, 17 remaining)
- [x] button.tsx
- [x] badge.tsx
- [x] card.tsx
- [x] input.tsx
- [x] select.tsx
- [x] empty-state.tsx
- [ ] alert-dialog.tsx
- [ ] avatar.tsx
- [ ] collapsible.tsx
- [ ] dialog.tsx
- [ ] dropdown-menu.tsx
- [ ] error-boundary.tsx
- [ ] form.tsx
- [ ] label.tsx
- [ ] loading-button.tsx
- [ ] scroll-area.tsx
- [ ] separator.tsx
- [ ] sheet.tsx
- [ ] skeleton.tsx
- [ ] switch.tsx
- [ ] table.tsx
- [ ] tabs.tsx
- [ ] textarea.tsx
- [ ] tooltip.tsx

### Layout Components (5 total, 0 tested)
- [ ] AppLayout.tsx
- [ ] MeshBackground.tsx
- [ ] Sidebar.tsx
- [ ] ThemeProvider.tsx
- [ ] Topbar.tsx

### Deployment Components (2 total, 2 tested)
- [x] RiskScoreBadge.tsx
- [x] RingProgressIndicator.tsx

### Asset Components (2 total, 0 tested)
- [ ] AssetActionRunner.tsx
- [ ] AssetDetailDialog.tsx

### AI Components (3 total, 0 tested)
- [ ] AIApprovalDialog.tsx
- [ ] AmaniChatBubble.tsx
- [ ] PendingApprovals.tsx

## Test Pattern Template

```typescript
// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { ComponentName } from './ComponentName';

describe('ComponentName', () => {
  it('renders correctly', () => {
    render(<ComponentName />);
    expect(screen.getByRole('...')).toBeInTheDocument();
  });

  it('handles props correctly', () => {
    render(<ComponentName prop="value" />);
    // assertions
  });
});
```

## Coverage Target

- Lines: ≥90%
- Functions: ≥90%
- Branches: ≥90%
- Statements: ≥90%

