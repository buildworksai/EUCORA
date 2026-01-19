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

// Note: Authentication errors are now properly handled by the API client
// and will redirect to login when session expires

// Session-based auth - no MSAL provider needed for pure session auth
ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <BrowserRouter>
      <App />
    </BrowserRouter>
  </React.StrictMode>
);
