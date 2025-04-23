# Simple SSE Streaming Demo

A minimal example of Server-Sent Events (SSE) with FastAPI and Vue.js.

## Overview

This simplified branch demonstrates how to implement real-time data streaming from a FastAPI backend to a Vue.js frontend using Server-Sent Events (SSE). The demo shows **system RAM usage being monitored** in real-time without page refreshes.

## Features

- Real-time data streaming with SSE
- **Simple RAM monitor example**
- No build tools required (uses CDN for Vue)
- Minimal setup

## Project Structure
```
.
├── static/
│   ├── index.html    # Frontend Vue application
│   ├── app.js        # Vue component code
│   └── style.css     # Styling
└── stream_logs.py    # FastAPI backend with SSE endpoint
```

## Running the Demo

1. Install the required dependencies:

   ```bash
   pip install fastapi uvicorn psutil
   ```
   *(Updated from poetry to pip)*

2. Start the server:

   ```bash
   python stream_logs.py
   ```

3. Access the application at http://localhost:8000

## How It Works

1. The backend (FastAPI) exposes an endpoint `/api/stream` that streams data using the `text/event-stream` content type
2. The frontend establishes an SSE connection using the `EventSource` API
3. Each message is transmitted as a formatted SSE event
4. The Vue.js application updates the UI in real-time as events arrive

## Expanding the Demo

This simplified example can serve as a foundation for more complex streaming applications:

- Add authentication for secure streams
- Implement multiple concurrent streams for different data sources
- Enhance error handling and reconnection logic
- Integrate with real data sources or system metrics like CPU/Disk I/O