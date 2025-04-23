# Stream Logs Demo

A real-time log streaming application built with FastAPI and Vue.js, demonstrating Server-Sent Events (SSE) for live log monitoring.

## Features

- Real-time log streaming with Server-Sent Events (SSE)
- System resource monitoring
- Custom log messages
- Thread-safe logging implementation
- Responsive Vue.js frontend

## Setup

### Backend

```bash
# From root directory with Poetry
poetry install
poetry run uvicorn app.main:app --reload

# Or using the script in pyproject.toml
poetry run start-process
```

### Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at http://localhost:5173, with the API at http://localhost:8000.

## API Endpoints

- `POST /api/sessions` - Create a new log session
- `DELETE /api/sessions/{session_id}` - Delete a session
- `POST /api/sessions/{session_id}/start-monitoring` - Start monitoring
- `POST /api/sessions/{session_id}/stop-monitoring` - Stop monitoring
- `POST /api/sessions/{session_id}/logs` - Add a custom log message
- `GET /api/sessions/{session_id}/logs` - Stream logs as SSE events
- `POST /api/clear-logs` - Clear all logs

## Project Structure

- `backend/` - FastAPI server, logging system, and system monitoring
- `frontend/` - Vue.js client with real-time log viewer