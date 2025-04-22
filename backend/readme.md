# Stream Logs Demo Backend

A FastAPI backend for demonstrating streaming logs with Server-Sent Events (SSE).

## Features

- Create log sessions with unique IDs
- Stream logs in real-time using Server-Sent Events
- Background monitoring that logs system stats (CPU, memory)
- Thread-safe logging implementation
- Graceful shutdown handling

## Setup

1. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Run the server:
   ```bash
   uvicorn app.main:app --reload
   ```

The API will be available at http://localhost:8000.

## API Endpoints

- `POST /api/sessions` - Create a new log session
- `DELETE /api/sessions/{session_id}` - Delete a session
- `POST /api/sessions/{session_id}/start-monitoring` - Start background monitoring
- `POST /api/sessions/{session_id}/stop-monitoring` - Stop background monitoring
- `POST /api/sessions/{session_id}/logs` - Add a custom log message
- `GET /api/sessions/{session_id}/logs` - Stream logs as SSE events
- `POST /api/clear-logs` - Clear all logs

## API Documentation

FastAPI automatic documentation is available at:
- http://localhost:8000/docs (Swagger UI)
- http://localhost:8000/redoc (ReDoc)