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
