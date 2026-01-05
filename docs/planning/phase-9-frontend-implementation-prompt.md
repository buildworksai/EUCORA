# Phase 9: Frontend Web Control Plane (React) - Implementation Prompt

**Version**: 1.0
**Date**: 2026-01-04
**Target Duration**: 4 weeks
**Dependencies**: Phase 8 (Backend Control Plane)

---

## Task Overview

Implement the **Vite + React + TypeScript** frontend for the Enterprise Endpoint Application Packaging & Deployment Factory. This web application provides an interactive UI for Platform Admins, CAB Approvers, Publishers, and Auditors to manage deployments, review evidence packs, and monitor system health.

**Success Criteria**:
- Premium glassmorphism UI with dark mode support
- Entra ID authentication via MSAL-React
- Real-time deployment dashboard with ring visualization
- Interactive CAB approval portal
- Evidence pack viewer with SBOM/vulnerability scan details
- Audit trail search and export
- ≥90% test coverage (Vitest + React Testing Library)
- E2E tests for critical flows (Playwright)

---

## Mandatory Guardrails

### Architecture Alignment
- ✅ **SPA Only**: No Server-Side Rendering (Next.js banned)
- ✅ **Session-Based Auth**: Django backend handles sessions; no JWTs in localStorage
- ✅ **Zustand for State**: Redux/Redux Toolkit/MobX banned
- ✅ **TanStack Query for Server State**: Handles caching, polling, optimistic updates
- ✅ **Tailwind CSS + Shadcn/UI**: Premium design system

### Quality Standards
- ✅ **ESLint + Prettier**: Auto-formatted code, `--max-warnings 0`
- ✅ **TypeScript Strict Mode**: No `any` types without explicit justification
- ✅ **Vitest + React Testing Library**: ≥90% component coverage
- ✅ **Playwright E2E**: Critical user flows tested (login → deploy → approve)
- ✅ **Pre-Commit Hooks**: Enforced blocking (see `.pre-commit-config.yaml`)

### Security Requirements
- ✅ **MSAL-React**: Entra ID OAuth2 integration
- ✅ **CSRF Protection**: Django CSRF tokens in all mutation requests
- ✅ **XSS Protection**: All user inputs sanitized
- ✅ **WCAG 2.1 AA**: Accessibility compliance

---

## Scope: Vite Project Structure

### Project Layout
```
frontend/
├── index.html                         # Vite entry point
├── package.json                       # Dependencies (exact pinning for state libs)
├── tsconfig.json                      # TypeScript strict config
├── vite.config.ts                     # Vite build configuration
├── tailwind.config.js                 # Tailwind + EUCORA theme
├── .env.example                       # Environment variable template
├── src/
│   ├── main.tsx                       # React entry point + MSAL provider
│   ├── App.tsx                        # Root component + routing
│   ├── routes/                        # React Router pages
│   │   ├── Dashboard.tsx              # Main dashboard (deployment status)
│   │   ├── CABPortal.tsx              # CAB approval interface
│   │   ├── DeploymentWizard.tsx       # Guided deployment creation
│   │   ├── AuditTrail.tsx             # Event store search
│   │   ├── EvidenceViewer.tsx         # Evidence pack details
│   │   └── Settings.tsx               # User preferences
│   ├── components/                    # Reusable UI components
│   │   ├── ui/                        # Shadcn/UI components (Button, Card, etc.)
│   │   ├── layout/                    # Layout components (Navbar, Sidebar)
│   │   ├── deployment/                # Deployment-specific components
│   │   ├── cab/                       # CAB-specific components
│   │   └── charts/                    # Recharts wrappers
│   ├── lib/                           # Utilities and hooks
│   │   ├── api/                       # API client (TanStack Query setup)
│   │   ├── auth/                      # MSAL configuration
│   │   ├── stores/                    # Zustand stores
│   │   ├── hooks/                     # Custom React hooks
│   │   └── utils/                     # Helper functions
│   ├── types/                         # TypeScript type definitions
│   │   ├── api.ts                     # Backend API types (generated from OpenAPI)
│   │   └── models.ts                  # Domain models
│   └── styles/                        # Global styles
│       ├── globals.css                # Tailwind imports + CSS variables
│       └── themes/                    # Light/Dark mode themes
├── public/                            # Static assets
│   ├── EUCORA-logo2.png               # Logo (from branding.md)
│   └── favicon.ico
├── tests/                             # Tests
│   ├── unit/                          # Vitest component tests
│   ├── e2e/                           # Playwright E2E tests
│   └── setup.ts                       # Test configuration
└── .pre-commit-config.yaml            # Pre-commit hooks
```

---

## Phase 9.1: Vite Project Initialization (Week 1, Days 1-2)

### Deliverables
1. Vite project scaffolding with TypeScript
2. Tailwind CSS + Shadcn/UI setup
3. MSAL-React configuration
4. React Router setup
5. TanStack Query + Zustand configuration

### Implementation Steps

#### 1. Initialize Vite Project
```bash
# From /Users/raghunathchava/Code/EUCORA/
cd frontend
npm create vite@latest . -- --template react-ts
npm install

# Install dependencies
npm install react-router-dom@6.22.0 \
  @azure/msal-react@latest @azure/msal-browser@latest \
  @tanstack/react-query@latest \
  zustand@latest \
  tailwindcss@3.4.17 autoprefixer postcss \
  @radix-ui/react-* lucide-react \
  react-hook-form@7.54.1 zod@3.24.1 @hookform/resolvers@3.9.1 \
  recharts@2.15.0 sonner@1.7.1 date-fns@2.28.0

# Dev dependencies
npm install -D @types/node \
  @tanstack/eslint-plugin-query \
  vitest@latest @vitest/ui \
  @testing-library/react @testing-library/jest-dom \
  @playwright/test \
  eslint@9.34.0 prettier \
  @typescript-eslint/eslint-plugin @typescript-eslint/parser
```

#### 2. Tailwind CSS Configuration
**File**: `frontend/tailwind.config.js`

```javascript
/** @type {import('tailwindcss').Config} */
export default {
  darkMode: ['class'],
  content: [
    './index.html',
    './src/**/*.{js,ts,jsx,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        eucora: {
          deepBlue: '#0A1E3D',     // Primary brand color
          teal: '#17A589',          // Accent 1
          gold: '#F39C12',          // Accent 2 (warnings, highlights)
          green: '#27AE60',         // Success
          red: '#E74C3C',           // Danger
          gray: {
            50: '#F8F9FA',
            100: '#E9ECEF',
            200: '#DEE2E6',
            300: '#CED4DA',
            400: '#ADB5BD',
            500: '#6C757D',
            600: '#495057',
            700: '#343A40',
            800: '#212529',
            900: '#0D1117',
          },
        },
      },
      backdropBlur: {
        xs: '2px',
      },
      animation: {
        'fade-in': 'fadeIn 0.3s ease-in-out',
        'slide-up': 'slideUp 0.4s ease-out',
      },
      keyframes: {
        fadeIn: {
          '0%': { opacity: 0 },
          '100%': { opacity: 1 },
        },
        slideUp: {
          '0%': { transform: 'translateY(20px)', opacity: 0 },
          '100%': { transform: 'translateY(0)', opacity: 1 },
        },
      },
    },
  },
  plugins: [require('tailwindcss-animate')],
}
```

#### 3. TypeScript Configuration
**File**: `frontend/tsconfig.json`

```json
{
  "compilerOptions": {
    "target": "ES2020",
    "useDefineForClassFields": true,
    "lib": ["ES2020", "DOM", "DOM.Iterable"],
    "module": "ESNext",
    "skipLibCheck": true,

    /* Bundler mode */
    "moduleResolution": "bundler",
    "allowImportingTsExtensions": true,
    "resolveJsonModule": true,
    "isolatedModules": true,
    "noEmit": true,
    "jsx": "react-jsx",

    /* Linting */
    "strict": true,
    "noUnusedLocals": true,
    "noUnusedParameters": true,
    "noFallthroughCasesInSwitch": true,
    "noImplicitAny": true,
    "strictNullChecks": true,

    /* Path aliases */
    "baseUrl": ".",
    "paths": {
      "@/*": ["./src/*"]
    }
  },
  "include": ["src"],
  "references": [{ "path": "./tsconfig.node.json" }]
}
```

#### 4. Global Styles
**File**: `frontend/src/styles/globals.css`

```css
@tailwind base;
@tailwind components;
@tailwind utilities;

@layer base {
  :root {
    --background: 0 0% 100%;
    --foreground: 222.2 84% 4.9%;
    --card: 0 0% 100%;
    --card-foreground: 222.2 84% 4.9%;
    --primary: 210 100% 12%;      /* eucora-deepBlue */
    --primary-foreground: 210 40% 98%;
    --accent: 168 56% 37%;        /* eucora-teal */
    --accent-foreground: 210 40% 98%;
    --destructive: 0 72% 51%;     /* eucora-red */
    --border: 214.3 31.8% 91.4%;
    --radius: 0.5rem;
  }

  .dark {
    --background: 222 47% 7%;     /* eucora-gray-900 */
    --foreground: 210 40% 98%;
    --card: 217 33% 17%;
    --card-foreground: 210 40% 98%;
    --primary: 168 56% 37%;       /* eucora-teal */
    --primary-foreground: 222 47% 11%;
    --accent: 43 74% 49%;         /* eucora-gold */
    --accent-foreground: 222 47% 11%;
    --destructive: 0 72% 51%;
    --border: 217 33% 17%;
  }
}

@layer utilities {
  /* Glassmorphism effect */
  .glass {
    @apply bg-white/10 backdrop-blur-md border border-white/20;
  }

  .glass-dark {
    @apply bg-gray-800/30 backdrop-blur-md border border-gray-700/50;
  }
}

body {
  @apply bg-background text-foreground;
  font-family: 'Inter', system-ui, -apple-system, sans-serif;
}
```

---

## Phase 9.2: Authentication (MSAL-React) (Week 1, Days 3-4)

### MSAL Configuration
**File**: `frontend/src/lib/auth/msalConfig.ts`

```typescript
/**
 * MSAL (Microsoft Authentication Library) configuration for Entra ID OAuth2.
 */
import { Configuration, PublicClientApplication } from '@azure/msal-browser';

const msalConfig: Configuration = {
  auth: {
    clientId: import.meta.env.VITE_ENTRA_CLIENT_ID,
    authority: `https://login.microsoftonline.com/${import.meta.env.VITE_ENTRA_TENANT_ID}`,
    redirectUri: import.meta.env.VITE_REDIRECT_URI || 'http://localhost:5173',
  },
  cache: {
    cacheLocation: 'sessionStorage', // Use sessionStorage (not localStorage for security)
    storeAuthStateInCookie: false,
  },
};

export const msalInstance = new PublicClientApplication(msalConfig);

export const loginRequest = {
  scopes: ['User.Read'],
};
```

### MSAL Provider Setup
**File**: `frontend/src/main.tsx`

```tsx
/**
 * React entry point with MSAL provider.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { MsalProvider } from '@azure/msal-react';
import { msalInstance } from './lib/auth/msalConfig';
import App from './App';
import './styles/globals.css';

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <MsalProvider instance={msalInstance}>
      <App />
    </MsalProvider>
  </React.StrictMode>
);
```

### Authentication Hook
**File**: `frontend/src/lib/hooks/useAuth.ts`

```typescript
/**
 * Custom hook for authentication state and actions.
 */
import { useMsal } from '@azure/msal-react';
import { loginRequest } from '@/lib/auth/msalConfig';
import { useNavigate } from 'react-router-dom';

export function useAuth() {
  const { instance, accounts } = useMsal();
  const navigate = useNavigate();

  const login = async () => {
    try {
      const response = await instance.loginPopup(loginRequest);
      
      // Exchange authorization code for Django session
      const loginResponse = await fetch(`${import.meta.env.VITE_API_URL}/api/v1/auth/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        credentials: 'include', // Send cookies
        body: JSON.stringify({ code: response.idToken }), // NOTE: Simplified; real impl needs auth code flow
      });

      if (loginResponse.ok) {
        navigate('/dashboard');
      }
    } catch (error) {
      console.error('Login failed:', error);
    }
  };

  const logout = async () => {
    // Logout from Django backend
    await fetch(`${import.meta.env.VITE_API_URL}/api/v1/auth/logout`, {
      method: 'POST',
      credentials: 'include',
    });

    // Logout from MSAL
    await instance.logoutPopup();
  };

  return {
    isAuthenticated: accounts.length > 0,
    user: accounts[0] || null,
    login,
    logout,
  };
}
```

---

## Phase 9.3: State Management (Zustand + TanStack Query) (Week 1, Day 5)

### Zustand Store (UI State)
**File**: `frontend/src/lib/stores/uiStore.ts`

```typescript
/**
 * Global UI state (theme, sidebar, notifications).
 * 
 * Zustand is the ONLY allowed client state container (Redux banned).
 */
import { create } from 'zustand';

interface UIState {
  theme: 'light' | 'dark' | 'system';
  sidebarOpen: boolean;
  toggleSidebar: () => void;
  setTheme: (theme: 'light' | 'dark' | 'system') => void;
}

export const useUIStore = create<UIState>((set) => ({
  theme: 'system',
  sidebarOpen: true,
  toggleSidebar: () => set((state) => ({ sidebarOpen: !state.sidebarOpen })),
  setTheme: (theme) => set({ theme }),
}));
```

### TanStack Query Setup (Server State)
**File**: `frontend/src/lib/api/queryClient.ts`

```typescript
/**
 * TanStack Query client configuration.
 * 
 * Handles server state (deployments, evidence packs, etc.).
 */
import { QueryClient } from '@tanstack/react-query';

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 1000 * 60 * 5, // 5 minutes
      retry: 3,
      refetchOnWindowFocus: false,
    },
    mutations: {
      retry: 1,
    },
  },
});
```

**File**: `frontend/src/App.tsx`

```tsx
/**
 * Root component with providers and routing.
 */
import { QueryClientProvider } from '@tanstack/react-query';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { queryClient } from './lib/api/queryClient';
import { useAuth } from './lib/hooks/useAuth';
import Dashboard from './routes/Dashboard';
import CABPortal from './routes/CABPortal';
import DeploymentWizard from './routes/DeploymentWizard';
import AuditTrail from './routes/AuditTrail';
import EvidenceViewer from './routes/EvidenceViewer';
import Settings from './routes/Settings';
import Login from './routes/Login';

function App() {
  const { isAuthenticated } = useAuth();

  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<Login />} />
          
          {/* Protected routes */}
          <Route path="/" element={isAuthenticated ? <Navigate to="/dashboard" /> : <Navigate to="/login" />} />
          <Route path="/dashboard" element={isAuthenticated ? <Dashboard /> : <Navigate to="/login" />} />
          <Route path="/cab" element={isAuthenticated ? <CABPortal /> : <Navigate to="/login" />} />
          <Route path="/deploy" element={isAuthenticated ? <DeploymentWizard /> : <Navigate to="/login" />} />
          <Route path="/audit" element={isAuthenticated ? <AuditTrail /> : <Navigate to="/login" />} />
          <Route path="/evidence/:id" element={isAuthenticated ? <EvidenceViewer /> : <Navigate to="/login" />} />
          <Route path="/settings" element={isAuthenticated ? <Settings /> : <Navigate to="/login" />} />
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
```

---

## Phase 9.4: API Client & Type Generation (Week 2, Days 1-2)

### API Client (Django Integration)
**File**: `frontend/src/lib/api/client.ts`

```typescript
/**
 * API client for Django backend with CSRF protection.
 */
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

/**
 * Get CSRF token from cookie (set by Django).
 */
function getCsrfToken(): string | null {
  const match = document.cookie.match(/csrftoken=([^;]+)/);
  return match ? match[1] : null;
}

/**
 * Generic fetch wrapper with Django session credentials.
 */
async function apiRequest<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const csrfToken = getCsrfToken();

  const response = await fetch(`${API_BASE_URL}${endpoint}`, {
    ...options,
    credentials: 'include', // Send session cookies
    headers: {
      'Content-Type': 'application/json',
      ...(csrfToken && options.method !== 'GET' ? { 'X-CSRFToken': csrfToken } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Unknown error' }));
    throw new Error(error.detail || `HTTP ${response.status}`);
  }

  return response.json();
}

export const api = {
  get: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: 'GET' }),
  post: <T>(endpoint: string, data: unknown) =>
    apiRequest<T>(endpoint, { method: 'POST', body: JSON.stringify(data) }),
  put: <T>(endpoint: string, data: unknown) =>
    apiRequest<T>(endpoint, { method: 'PUT', body: JSON.stringify(data) }),
  patch: <T>(endpoint: string, data: unknown) =>
    apiRequest<T>(endpoint, { method: 'PATCH', body: JSON.stringify(data) }),
  delete: <T>(endpoint: string) => apiRequest<T>(endpoint, { method: 'DELETE' }),
};
```

### Type Definitions (Generated from OpenAPI)
**File**: `frontend/src/types/api.ts`

```typescript
/**
 * API type definitions (generated from Django OpenAPI schema).
 * 
 * Generate command: npx openapi-typescript http://localhost:8000/api/schema/ -o src/types/api.ts
 */

export interface DeploymentIntent {
  id: number;
  correlation_id: string;
  app_name: string;
  version: string;
  target_ring: 'LAB' | 'CANARY' | 'PILOT' | 'DEPARTMENT' | 'GLOBAL';
  status: 'PENDING' | 'AWAITING_CAB' | 'APPROVED' | 'REJECTED' | 'DEPLOYING' | 'COMPLETED' | 'FAILED' | 'ROLLED_BACK';
  risk_score: number | null;
  requires_cab_approval: boolean;
  created_at: string;
  updated_at: string;
}

export interface CABApproval {
  id: number;
  deployment_intent: number;
  decision: 'PENDING' | 'APPROVED' | 'REJECTED' | 'CONDITIONAL';
  approver: string | null;
  comments: string;
  conditions: string[];
  submitted_at: string;
  reviewed_at: string | null;
}

export interface EvidencePack {
  id: number;
  correlation_id: string;
  artifact_hash: string;
  artifact_signature: string;
  sbom_data: Record<string, unknown>;
  vulnerability_scan_results: Record<string, unknown>;
  scan_policy_decision: 'PASS' | 'FAIL' | 'EXCEPTION';
  rollback_plan: Record<string, unknown>;
  created_at: string;
}

export interface DeploymentEvent {
  id: number;
  correlation_id: string;
  event_type: string;
  metadata: Record<string, unknown>;
  error_classification: 'NONE' | 'TRANSIENT' | 'PERMANENT' | 'POLICY_VIOLATION';
  created_at: string;
}
```

### TanStack Query Hooks
**File**: `frontend/src/lib/api/useDeployments.ts`

```typescript
/**
 * TanStack Query hooks for deployment intents.
 */
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from './client';
import type { DeploymentIntent } from '@/types/api';

export function useDeployments(filters?: { status?: string; ring?: string }) {
  return useQuery({
    queryKey: ['deployments', filters],
    queryFn: () => {
      const params = new URLSearchParams(filters as Record<string, string>);
      return api.get<DeploymentIntent[]>(`/api/v1/deployment-intents/?${params}`);
    },
  });
}

export function useDeployment(id: number) {
  return useQuery({
    queryKey: ['deployment', id],
    queryFn: () => api.get<DeploymentIntent>(`/api/v1/deployment-intents/${id}/`),
  });
}

export function useCreateDeployment() {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: (data: { app_name: string; version: string; target_ring: string; evidence_pack: unknown }) =>
      api.post<DeploymentIntent>('/api/v1/deployment-intents/', data),
    onSuccess: () => {
      // Invalidate cache to refetch deployment list
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
    },
  });
}

export function usePromoteRing(id: number) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: () => api.post<DeploymentIntent>(`/api/v1/deployment-intents/${id}/promote_ring/`, {}),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['deployment', id] });
      queryClient.invalidateQueries({ queryKey: ['deployments'] });
    },
  });
}
```

---

## Phase 9.5: UI Components (Shadcn/UI + Custom) (Week 2, Days 3-5)

### Shadcn/UI Setup
```bash
# Install Shadcn CLI
npx shadcn-ui@latest init

# Add core components
npx shadcn-ui@latest add button card input label select table badge dialog dropdown-menu
```

### Custom Components

**File**: `frontend/src/components/deployment/RingProgressIndicator.tsx`

```tsx
/**
 * Visual indicator for ring-based rollout progress.
 */
import { CheckCircle, Circle, XCircle, Clock } from 'lucide-react';
import { cn } from '@/lib/utils';

interface Ring {
  name: string;
  status: 'pending' | 'in_progress' | 'completed' | 'failed';
  successRate?: number;
}

interface RingProgressIndicatorProps {
  rings: Ring[];
}

export function RingProgressIndicator({ rings }: RingProgressIndicatorProps) {
  return (
    <div className="flex items-center gap-4">
      {rings.map((ring, index) => (
        <div key={ring.name} className="flex items-center gap-2">
          {/* Ring status icon */}
          <div className={cn(
            'flex items-center justify-center w-12 h-12 rounded-full border-2',
            ring.status === 'completed' && 'bg-eucora-green/20 border-eucora-green',
            ring.status === 'in_progress' && 'bg-eucora-teal/20 border-eucora-teal animate-pulse',
            ring.status === 'failed' && 'bg-eucora-red/20 border-eucora-red',
            ring.status === 'pending' && 'bg-gray-200 border-gray-400 dark:bg-gray-700 dark:border-gray-600'
          )}>
            {ring.status === 'completed' && <CheckCircle className="w-6 h-6 text-eucora-green" />}
            {ring.status === 'in_progress' && <Clock className="w-6 h-6 text-eucora-teal" />}
            {ring.status === 'failed' && <XCircle className="w-6 h-6 text-eucora-red" />}
            {ring.status === 'pending' && <Circle className="w-6 h-6 text-gray-400" />}
          </div>

          {/* Ring name and success rate */}
          <div className="flex flex-col">
            <span className="text-sm font-semibold">{ring.name}</span>
            {ring.successRate !== undefined && (
              <span className="text-xs text-gray-500 dark:text-gray-400">
                {ring.successRate.toFixed(1)}% success
              </span>
            )}
          </div>

          {/* Connector line to next ring */}
          {index < rings.length - 1 && (
            <div className={cn(
              'w-8 h-0.5 mx-2',
              ring.status === 'completed' ? 'bg-eucora-green' : 'bg-gray-300 dark:bg-gray-600'
            )} />
          )}
        </div>
      ))}
    </div>
  );
}
```

**File**: `frontend/src/components/deployment/RiskScoreBadge.tsx`

```tsx
/**
 * Risk score badge with color-coded severity.
 */
import { Badge } from '@/components/ui/badge';

interface RiskScoreBadgeProps {
  score: number;
}

export function RiskScoreBadge({ score }: RiskScoreBadgeProps) {
  const getVariant = () => {
    if (score <= 30) return 'success';
    if (score <= 50) return 'warning';
    return 'destructive';
  };

  const getLabel = () => {
    if (score <= 30) return 'Low Risk';
    if (score <= 50) return 'Medium Risk';
    return 'High Risk (CAB Required)';
  };

  return (
    <Badge variant={getVariant()} className="font-semibold">
      {score} - {getLabel()}
    </Badge>
  );
}
```

---

## Phase 9.6: Core Pages (Week 3)

### Dashboard Page
**File**: `frontend/src/routes/Dashboard.tsx`

```tsx
/**
 * Main dashboard showing deployment status and ring progress.
 */
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { useDeployments } from '@/lib/api/useDeployments';
import { RingProgressIndicator } from '@/components/deployment/RingProgressIndicator';
import { RiskScoreBadge } from '@/components/deployment/RiskScoreBadge';
import { Package, Clock, CheckCircle, XCircle } from 'lucide-react';

export default function Dashboard() {
  const { data: deployments, isLoading } = useDeployments();

  if (isLoading) return <div>Loading...</div>;

  // Calculate summary stats
  const stats = {
    total: deployments?.length || 0,
    inProgress: deployments?.filter(d => d.status === 'DEPLOYING').length || 0,
    completed: deployments?.filter(d => d.status === 'COMPLETED').length || 0,
    failed: deployments?.filter(d => d.status === 'FAILED').length || 0,
  };

  return (
    <div className="p-8 space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold">Deployment Dashboard</h1>
        <p className="text-gray-500 dark:text-gray-400">Real-time deployment status across all rings</p>
      </div>

      {/* Summary Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        <Card className="glass-dark">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Total Deployments</CardTitle>
            <Package className="w-4 h-4 text-eucora-teal" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.total}</div>
          </CardContent>
        </Card>

        <Card className="glass-dark">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">In Progress</CardTitle>
            <Clock className="w-4 h-4 text-eucora-gold" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.inProgress}</div>
          </CardContent>
        </Card>

        <Card className="glass-dark">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Completed</CardTitle>
            <CheckCircle className="w-4 h-4 text-eucora-green" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.completed}</div>
          </CardContent>
        </Card>

        <Card className="glass-dark">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium">Failed</CardTitle>
            <XCircle className="w-4 h-4 text-eucora-red" />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stats.failed}</div>
          </CardContent>
        </Card>
      </div>

      {/* Recent Deployments */}
      <Card className="glass-dark">
        <CardHeader>
          <CardTitle>Recent Deployments</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            {deployments?.slice(0, 5).map((deployment) => (
              <div key={deployment.id} className="flex items-center justify-between p-4 border rounded-lg border-gray-700">
                <div className="flex-1">
                  <h3 className="font-semibold">{deployment.app_name} {deployment.version}</h3>
                  <p className="text-sm text-gray-400">Correlation ID: {deployment.correlation_id}</p>
                </div>
                <div className="flex items-center gap-4">
                  {deployment.risk_score && <RiskScoreBadge score={deployment.risk_score} />}
                  <RingProgressIndicator rings={[
                    { name: 'Lab', status: 'completed' },
                    { name: 'Canary', status: deployment.target_ring === 'CANARY' ? 'in_progress' : 'pending' },
                    { name: 'Pilot', status: 'pending' },
                    { name: 'Global', status: 'pending' },
                  ]} />
                </div>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
```

### CAB Portal Page
**File**: `frontend/src/routes/CABPortal.tsx`

```tsx
/**
 * CAB approval portal for reviewing and approving/rejecting deployments.
 */
import { useState } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/lib/api/client';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Textarea } from '@/components/ui/textarea';
import { RiskScoreBadge } from '@/components/deployment/RiskScoreBadge';
import type { DeploymentIntent, CABApproval } from '@/types/api';

export default function CABPortal() {
  const queryClient = useQueryClient();
  const [selectedIntent, setSelectedIntent] = useState<number | null>(null);
  const [comments, setComments] = useState('');

  // Fetch pending CAB approvals
  const { data: pendingApprovals } = useQuery({
    queryKey: ['cab-approvals', 'pending'],
    queryFn: () => api.get<CABApproval[]>('/api/v1/cab-approvals/?decision=PENDING'),
  });

  // Approve mutation
  const approveMutation = useMutation({
    mutationFn: (data: { id: number; comments: string }) =>
      api.post(`/api/v1/cab-approvals/${data.id}/approve/`, { comments: data.comments }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cab-approvals'] });
      setSelectedIntent(null);
      setComments('');
    },
  });

  // Reject mutation
  const rejectMutation = useMutation({
    mutationFn: (data: { id: number; comments: string }) =>
      api.post(`/api/v1/cab-approvals/${data.id}/reject/`, { comments: data.comments }),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ['cab-approvals'] });
      setSelectedIntent(null);
      setComments('');
    },
  });

  return (
    <div className="p-8 space-y-6">
      <div>
        <h1 className="text-3xl font-bold">CAB Approval Portal</h1>
        <p className="text-gray-500 dark:text-gray-400">Review and approve high-risk deployments</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Pending Approvals List */}
        <Card className="glass-dark">
          <CardHeader>
            <CardTitle>Pending Approvals ({pendingApprovals?.length || 0})</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {pendingApprovals?.map((approval) => (
              <div
                key={approval.id}
                className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                  selectedIntent === approval.id
                    ? 'border-eucora-teal bg-eucora-teal/10'
                    : 'border-gray-700 hover:border-gray-600'
                }`}
                onClick={() => setSelectedIntent(approval.id)}
              >
                <h3 className="font-semibold">Deployment Intent #{approval.deployment_intent}</h3>
                <p className="text-sm text-gray-400">Submitted {new Date(approval.submitted_at).toLocaleDateString()}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        {/* Approval Details */}
        {selectedIntent && (
          <Card className="glass-dark">
            <CardHeader>
              <CardTitle>Review & Decision</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4">
              {/* Evidence pack viewer would go here */}
              <div className="space-y-2">
                <label className="text-sm font-medium">Reviewer Comments</label>
                <Textarea
                  placeholder="Enter approval/rejection reason..."
                  value={comments}
                  onChange={(e) => setComments(e.target.value)}
                  rows={5}
                />
              </div>

              <div className="flex gap-2">
                <Button
                  onClick={() => approveMutation.mutate({ id: selectedIntent, comments })}
                  className="flex-1 bg-eucora-green hover:bg-eucora-green/80"
                >
                  Approve
                </Button>
                <Button
                  onClick={() => rejectMutation.mutate({ id: selectedIntent, comments })}
                  variant="destructive"
                  className="flex-1"
                >
                  Reject
                </Button>
              </div>
            </CardContent>
          </Card>
        )}
      </div>
    </div>
  );
}
```

---

## Phase 9.7: Testing (Week 4)

### Vitest Component Tests
**File**: `frontend/tests/unit/RiskScoreBadge.test.tsx`

```tsx
import { render, screen } from '@testing-library/react';
import { describe, it, expect } from 'vitest';
import { RiskScoreBadge } from '@/components/deployment/RiskScoreBadge';

describe('RiskScoreBadge', () => {
  it('renders low risk for score ≤ 30', () => {
    render(<RiskScoreBadge score={25} />);
    expect(screen.getByText(/Low Risk/i)).toBeInTheDocument();
  });

  it('renders high risk for score > 50', () => {
    render(<RiskScoreBadge score={75} />);
    expect(screen.getByText(/High Risk/i)).toBeInTheDocument();
    expect(screen.getByText(/CAB Required/i)).toBeInTheDocument();
  });
});
```

### Playwright E2E Tests
**File**: `frontend/tests/e2e/deployment-flow.spec.ts`

```typescript
import { test, expect } from '@playwright/test';

test.describe('Deployment Flow', () => {
  test('should create deployment and view on dashboard', async ({ page }) => {
    // Login
    await page.goto('http://localhost:5173/login');
    await page.click('button:has-text("Sign in with Microsoft")');
    // ... handle MSAL popup

    // Navigate to deployment wizard
    await page.goto('http://localhost:5173/deploy');

    // Fill form
    await page.fill('input[name="app_name"]', 'Test App');
    await page.fill('input[name="version"]', '1.0.0');
    await page.selectOption('select[name="target_ring"]', 'CANARY');
    await page.click('button:has-text("Submit")');

    // Verify redirect to dashboard
    await expect(page).toHaveURL(/\/dashboard/);

    // Verify deployment appears in list
    await expect(page.locator('text=Test App 1.0.0')).toBeVisible();
  });
});
```

---

## Quality Checklist

### Per Component
- [ ] TypeScript strict mode (no `any` without justification)
- [ ] ESLint + Prettier pass with `--max-warnings 0`
- [ ] Vitest unit tests ≥90% coverage
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] Dark mode support

### E2E
- [ ] Login flow (MSAL)
- [ ] Create deployment intent
- [ ] CAB approval flow
- [ ] View audit trail

---

## Delivery Checklist

- [ ] Vite project initialized with TypeScript
- [ ] MSAL-React authentication working
- [ ] TanStack Query + Zustand configured
- [ ] Tailwind CSS + Shadcn/UI setup
- [ ] All 6 pages implemented (Dashboard, CAB, Deploy, Audit, Evidence, Settings)
- [ ] API client with CSRF protection
- [ ] Vitest coverage ≥90%
- [ ] Playwright E2E tests passing
- [ ] README with setup instructions

---

## Related Documentation

- [.agents/rules/13-tech-stack.md](../../.agents/rules/13-tech-stack.md)
- [docs/planning/phase-8-backend-implementation-prompt.md](./phase-8-backend-implementation-prompt.md)
- [.agents/rules/branding.md](../../.agents/rules/branding.md)

---

**End of Phase 9 Prompt**
