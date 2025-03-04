import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

// https://vitejs.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    port: 3000,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        configure: (proxy, options) => {
          // Add custom handler for health check endpoint
          proxy.on('error', (err, req, res) => {
            if (req.url.startsWith('/api/health')) {
              res.writeHead(503, {
                'Content-Type': 'application/json',
              });
              res.end(JSON.stringify({ status: 'error', message: 'Backend server is not available' }));
            }
          });
        },
      },
    },
    // Custom middleware to handle health check endpoint
    middlewares: [
      (req, res, next) => {
        if (req.url === '/api/health') {
          // Try to proxy to backend, if it fails the error handler above will catch it
          next();
        } else {
          next();
        }
      },
    ],
  },
}); 