import path from "path";
import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
// https://vite.dev/config/
export default defineConfig({
    plugins: [react()],
    resolve: {
        alias: {
            "@": path.resolve(__dirname, "./src"),
        },
    },
    server: {
        host: true, // Expose to Docker host
        port: 5173,
        watch: {
            usePolling: true, // Needed for Docker on some systems, though standard events often work on Mac
        }
    }
});
