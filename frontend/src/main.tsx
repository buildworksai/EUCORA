// SPDX-License-Identifier: Apache-2.0
// Copyright (c) 2026 BuildWorks.AI
/**
 * React entry point with session-based authentication.
 */
import React from 'react';
import ReactDOM from 'react-dom/client';
import { BrowserRouter } from 'react-router-dom';
import App from './App';
import './styles/globals.css';

// Validate required environment variables in production
const isProduction = import.meta.env.PROD;

if (isProduction) {
  const requiredVars = ['VITE_API_URL'];
  const missingVars = requiredVars.filter((varName) => !import.meta.env[varName]);

  if (missingVars.length > 0) {
    throw new Error(
      `Missing required environment variables in production: ${missingVars.join(', ')}. ` +
      'Please configure these variables before deploying.'
    );
  }

  // Warn if mock auth is enabled in production
  if (import.meta.env.VITE_USE_MOCK_AUTH === 'true') {
    console.warn(
      'WARNING: VITE_USE_MOCK_AUTH is enabled in production. ' +
      'This should only be used in development environments.'
    );
  }
}

// Note: Authentication errors are now properly handled by the API client
// and will redirect to login when session expires

// Session-based auth - no MSAL provider needed for pure session auth
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter
      future={{
        v7_startTransition: true,
        v7_relativeSplatPath: true,
      }}
    >
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
