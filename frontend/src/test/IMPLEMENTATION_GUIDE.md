# Frontend Test Implementation Guide

## Overview

This guide outlines the testing strategy for achieving ≥90% code coverage across all 36 frontend components.

## Test Structure

All test files follow the pattern: `ComponentName.test.tsx` alongside the component file.

## Test Categories

### 1. UI Components (`components/ui/`)
- **Priority**: High (foundation components)
- **Coverage Target**: 95%+
- **Test Focus**: Rendering, variants, interactions, accessibility

**Components to Test**:
- [x] button.tsx (example complete)
- [ ] badge.tsx
- [ ] card.tsx
- [ ] input.tsx
- [ ] select.tsx
- [ ] dialog.tsx
- [ ] table.tsx
- [ ] form.tsx
- [ ] ... (all 23 UI components)

### 2. Layout Components (`components/layout/`)
- **Priority**: High (core navigation)
- **Coverage Target**: 90%+
- **Test Focus**: Navigation, routing, state management

**Components to Test**:
- [ ] AppLayout.tsx
- [ ] Sidebar.tsx
- [ ] Topbar.tsx
- [ ] ThemeProvider.tsx
- [ ] MeshBackground.tsx

### 3. Deployment Components (`components/deployment/`)
- **Priority**: Medium
- **Coverage Target**: 90%+
- **Test Focus**: Business logic, data display

**Components to Test**:
- [x] RiskScoreBadge.tsx (example complete)
- [ ] RingProgressIndicator.tsx

### 4. Asset Components (`components/assets/`)
- **Priority**: Medium
- **Coverage Target**: 90%+
- **Test Focus**: Data fetching, user interactions

**Components to Test**:
- [ ] AssetDetailDialog.tsx
- [ ] AssetActionRunner.tsx

### 5. AI Components (`components/ai/`)
- **Priority**: Medium
- **Coverage Target**: 90%+
- **Test Focus**: Chat interactions, approval workflows

**Components to Test**:
- [ ] AmaniChatBubble.tsx
- [ ] AIApprovalDialog.tsx
- [ ] PendingApprovals.tsx

## Test Patterns

### Basic Component Test
```typescript
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Component } from './Component';

describe('Component', () => {
  it('renders correctly', () => {
    render(<Component />);
    expect(screen.getByRole('...')).toBeInTheDocument();
  });
});
```

### Interaction Test
```typescript
import userEvent from '@testing-library/user-event';

it('handles user interaction', async () => {
  const user = userEvent.setup();
  const handleClick = vi.fn();
  render(<Component onClick={handleClick} />);
  await user.click(screen.getByRole('button'));
  expect(handleClick).toHaveBeenCalled();
});
```

### Async Data Test
```typescript
import { waitFor } from '@testing-library/react';

it('loads and displays data', async () => {
  render(<Component />);
  await waitFor(() => {
    expect(screen.getByText('Loaded')).toBeInTheDocument();
  });
});
```

## Running Tests

```bash
# Run all tests
npm run test

# Run with UI
npm run test:ui

# Run with coverage
npm run test:coverage

# CI mode (no watch)
npm run test:ci
```

## Coverage Requirements

- **Lines**: ≥90%
- **Functions**: ≥90%
- **Branches**: ≥90%
- **Statements**: ≥90%

## Next Steps

1. Complete UI component tests (foundation)
2. Complete layout component tests (navigation)
3. Complete business logic component tests
4. Add integration tests for routes
5. Add E2E tests for critical workflows

