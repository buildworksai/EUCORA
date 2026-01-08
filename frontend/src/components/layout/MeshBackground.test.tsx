// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render } from '@/test/utils';
import { MeshBackground } from './MeshBackground';

describe('MeshBackground', () => {
  it('renders background layers', () => {
    const { container } = render(<MeshBackground />);
    expect(container.querySelector('.fixed.inset-0')).toBeInTheDocument();
  });
});
