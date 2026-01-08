// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * Shared Settings data (providers + demo users).
 */
import type { LucideIcon } from 'lucide-react';
import { Bot, Brain, Sparkles, Zap } from 'lucide-react';
import type { User } from '@/types/auth';

export type ProviderDefinition = {
  id: string;
  name: string;
  icon: LucideIcon;
  models: string[];
  placeholder: string;
  hasEndpoint?: boolean;
};

export const PROVIDERS: ProviderDefinition[] = [
  {
    id: 'openai',
    name: 'OpenAI',
    icon: Sparkles,
    models: [
      'gpt-4o',
      'gpt-4o-mini',
      'gpt-4-turbo',
      'gpt-4',
      'gpt-3.5-turbo',
      'o1-preview',
      'o1-mini',
    ],
    placeholder: 'sk-...',
  },
  {
    id: 'anthropic',
    name: 'Anthropic',
    icon: Brain,
    models: [
      'claude-3-5-sonnet-20241022',
      'claude-3-opus-20240229',
      'claude-3-sonnet-20240229',
      'claude-3-haiku-20240307',
    ],
    placeholder: 'sk-ant-...',
  },
  {
    id: 'groq',
    name: 'Groq',
    icon: Zap,
    models: [
      'llama-3.1-70b-versatile',
      'llama-3.1-8b-instant',
      'mixtral-8x7b-32768',
      'gemma2-9b-it',
    ],
    placeholder: 'gsk_...',
  },
  {
    id: 'azure_openai',
    name: 'Azure OpenAI',
    icon: Bot,
    models: ['gpt-4o', 'gpt-4o-mini', 'gpt-4-turbo', 'gpt-4', 'gpt-35-turbo'],
    placeholder: 'your-azure-key',
    hasEndpoint: true,
  },
  {
    id: 'google_gemini',
    name: 'Google Gemini',
    icon: Sparkles,
    models: ['gemini-1.5-pro', 'gemini-1.5-flash', 'gemini-pro'],
    placeholder: 'AIza...',
  },
];

export const MOCK_USERS_LIST: User[] = [
  {
    id: '1',
    email: 'admin@eucora.com',
    firstName: 'System',
    lastName: 'Administrator',
    role: 'admin',
    department: 'IT Operations',
    isActive: true,
    permissions: [],
    createdAt: new Date('2024-01-01'),
    lastLogin: new Date(),
  },
  {
    id: '2',
    email: 'demo@eucora.com',
    firstName: 'Demo',
    lastName: 'User',
    role: 'demo',
    department: 'Engineering',
    isActive: true,
    permissions: [],
    createdAt: new Date('2024-06-01'),
    lastLogin: new Date(),
  },
  {
    id: '3',
    email: 'operator@eucora.com',
    firstName: 'John',
    lastName: 'Operator',
    role: 'operator',
    department: 'DevOps',
    isActive: true,
    permissions: [],
    createdAt: new Date('2024-03-15'),
    lastLogin: new Date(Date.now() - 86400000),
  },
  {
    id: '4',
    email: 'viewer@eucora.com',
    firstName: 'Jane',
    lastName: 'Viewer',
    role: 'viewer',
    department: 'Compliance',
    isActive: false,
    permissions: [],
    createdAt: new Date('2024-04-20'),
    lastLogin: new Date(Date.now() - 604800000),
  },
];
