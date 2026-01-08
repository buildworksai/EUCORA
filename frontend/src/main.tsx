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

// Suppress authentication errors in console for demo/testing
if (import.meta.env.DEV) {
  const originalError = console.error;
  console.error = (...args: unknown[]) => {
    const message = args[0]?.toString() || '';
    // Suppress authentication-related errors
    if (
      message.includes('401') ||
      message.includes('403') ||
      message.includes('Unauthorized') ||
      message.includes('Forbidden') ||
      message.includes('authentication') ||
      message.includes('Authentication')
    ) {
      // Silently ignore or log at debug level
      console.debug('Suppressed auth error:', ...args);
      return;
    }
    originalError.apply(console, args);
  };
}

// Session-based auth - no MSAL provider needed for pure session auth
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
