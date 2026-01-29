// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
import { describe, it, expect } from 'vitest';
import { render, screen } from '@/test/utils';
import { Avatar, AvatarImage, AvatarFallback } from './avatar';

describe('Avatar', () => {
  it('renders avatar with image', () => {
    render(
      <Avatar>
        <AvatarImage src="/test-avatar.jpg" alt="Test Avatar" />
        <AvatarFallback>TA</AvatarFallback>
      </Avatar>
    );
    const image = screen.getByAltText('Test Avatar');
    expect(image).toBeInTheDocument();
  });

  it('renders fallback when image fails to load', () => {
    render(
      <Avatar>
        <AvatarImage src="/invalid.jpg" alt="Test" />
        <AvatarFallback>TA</AvatarFallback>
      </Avatar>
    );
    expect(screen.getByText('TA')).toBeInTheDocument();
  });

  it('applies custom className', () => {
    const { container } = render(
      <Avatar className="custom-avatar">
        <AvatarFallback>TA</AvatarFallback>
      </Avatar>
    );
    const avatar = container.querySelector('[class*="custom-avatar"]');
    expect(avatar).toBeInTheDocument();
  });
});
