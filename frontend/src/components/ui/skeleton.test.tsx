// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render } from '@/test/utils';
import { Skeleton, SkeletonCard, SkeletonTable, SkeletonList } from './skeleton';

describe('Skeleton Components', () => {
  it('renders basic skeleton', () => {
    const { container } = render(<Skeleton />);
    const skeleton = container.querySelector('[class*="animate-pulse"]');
    expect(skeleton).toBeInTheDocument();
  });

  it('renders skeleton card', () => {
    const { container } = render(<SkeletonCard />);
    const card = container.querySelector('[class*="glass"]');
    expect(card).toBeInTheDocument();
  });

  it('renders skeleton table with default rows', () => {
    const { container } = render(<SkeletonTable />);
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders skeleton table with custom row count', () => {
    const { container } = render(<SkeletonTable rows={10} />);
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(5);
  });

  it('renders skeleton list with default items', () => {
    const { container } = render(<SkeletonList />);
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(0);
  });

  it('renders skeleton list with custom item count', () => {
    const { container } = render(<SkeletonList items={5} />);
    const skeletons = container.querySelectorAll('[class*="animate-pulse"]');
    expect(skeletons.length).toBeGreaterThan(3);
  });
});

