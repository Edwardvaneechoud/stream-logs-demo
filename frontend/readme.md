# Stream Logs Demo Frontend

A Vue.js frontend for demonstrating streaming logs with Server-Sent Events (SSE).

## Features

- Create and manage log sessions
- Stream logs in real-time using Server-Sent Events
- Monitor system statistics (CPU, memory)
- Send custom log messages
- Clean, responsive UI

## Setup

1. Install dependencies:
   ```bash
   npm install
   ```

2. Start the development server:
   ```bash
   npm run dev
   ```

The app will be available at http://localhost:5173.

## Build for Production

```bash
npm run build
```

This will create a production-ready build in the `dist` directory that you can deploy to any static hosting service.

## Project Structure

- `src/App.vue` - Main application component
- `src/components/LogViewer.vue` - Component for streaming and displaying logs
- `public/index.html` - HTML template
- `vite.config.js` - Vite configuration with proxy settings for API

## Note

The frontend assumes the backend is running on `http://localhost:8000`. If your backend is running on a different port or host, update the proxy configuration in `vite.config.js`.