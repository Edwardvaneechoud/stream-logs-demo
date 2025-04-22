import asyncio
import json
import time
import uuid
from pathlib import Path
from typing import AsyncGenerator, Optional

import aiofiles
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse

from app import ServerRun
from app.logger import SessionLogger
from app.system_monitor import SystemMonitor
from app.session_registry import (
    register_session, register_monitor, unregister_session,
    stop_monitor, shutdown_all, get_active_sessions,
    update_session_activity
)

router = APIRouter()


@router.post("/sessions", tags=['sessions'])
async def create_session():
    """
    Create a new log session and return its ID
    """
    session_id = str(uuid.uuid4())

    # Initialize the logger for this session (clears any existing logs)
    logger = SessionLogger(session_id, clear_existing_logs=True)

    # Track session metadata
    session_metadata = {
        "created_at": time.time(),
        "last_activity": time.time(),
        "monitoring": False
    }

    # Register the session
    register_session(session_id, session_metadata)

    logger.info(f"Session created with ID: {session_id}")
    return {"session_id": session_id}


@router.delete("/sessions/{session_id}", tags=['sessions'])
async def delete_session(session_id: str):
    """
    Delete a session and its logs
    """
    active_sessions = get_active_sessions()
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Unregister the session (will stop monitoring and clean up logger)
    unregister_session(session_id)

    return {"message": f"Session {session_id} deleted"}


@router.post("/sessions/{session_id}/start-monitoring", tags=['sessions'])
async def start_monitoring(session_id: str, interval: int = 2):
    """
    Start background monitoring for the session
    """
    active_sessions = get_active_sessions()
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Stop existing monitor if any
    stop_monitor(session_id)

    # Get or create the logger
    logger = SessionLogger(session_id)

    # Create a new monitor and start it
    monitor = SystemMonitor(logger)
    monitor.start(interval=interval)

    # Register the monitor
    register_monitor(session_id, monitor)

    # Update last activity
    active_sessions = get_active_sessions()
    if session_id in active_sessions:
        active_sessions[session_id]["last_activity"] = time.time()

    return {"message": f"Started monitoring for session {session_id}"}


@router.post("/sessions/{session_id}/stop-monitoring", tags=['sessions'])
async def stop_monitoring_endpoint(session_id: str):
    """
    Stop background monitoring for the session
    """
    active_sessions = get_active_sessions()
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    # Stop monitoring
    if stop_monitor(session_id):
        # Update last activity timestamp
        active_sessions = get_active_sessions()
        if session_id in active_sessions:
            active_sessions[session_id]["last_activity"] = time.time()
        return {"message": f"Stopped monitoring for session {session_id}"}
    else:
        return {"message": f"Monitoring was not active for session {session_id}"}


@router.post("/clear-logs", tags=['logs'])
async def clear_logs_endpoint():
    """
    Clear all logs across all sessions
    """
    # Use our central registry to handle shutdown
    results = shutdown_all()

    return {
        "message": f"All logs have been cleared. Deleted {results['logs_deleted']} files.",
        "details": results
    }


async def format_sse_message(data: str) -> str:
    """Format the data as a proper SSE message"""
    return f"data: {json.dumps(data)}\n\n"


async def stream_log_file(
        log_file_path: Path,
        idle_timeout: int = 60  # timeout in seconds
) -> AsyncGenerator[str, None]:
    """Stream log file content as SSE events"""
    last_active = time.monotonic()
    try:
        async with aiofiles.open(log_file_path, "r") as file:
            # Ensure we start at the beginning
            await file.seek(0)
            while not ServerRun.exit:  # Check for server shutdown
                line = await file.readline()
                if line:
                    formatted_message = await format_sse_message(line.strip())
                    yield formatted_message
                    last_active = time.monotonic()  # Reset idle timer on activity
                else:
                    # Check for idle timeout
                    if time.monotonic() - last_active > idle_timeout:
                        yield await format_sse_message("Connection timed out due to inactivity.")
                        break
                    # Allow the event loop to process other tasks
                    await asyncio.sleep(0.1)

    except FileNotFoundError:
        error_msg = await format_sse_message(f"Log file not found: {log_file_path}")
        yield error_msg
        raise HTTPException(status_code=404, detail=f"Log file not found: {log_file_path}")
    except Exception as e:
        error_msg = await format_sse_message(f"Error reading log file: {str(e)}")
        yield error_msg
        raise HTTPException(status_code=500, detail=f"Error reading log file: {e}")


@router.get("/sessions/{session_id}/logs", tags=['logs'])
async def stream_logs(
        session_id: str,
        idle_timeout: int = Query(300, ge=10, le=3600)
):
    """
    Stream logs for a given session using Server-Sent Events.
    """
    active_sessions = get_active_sessions()
    if session_id not in active_sessions:
        raise HTTPException(status_code=404, detail="Session not found")

    logger = SessionLogger(session_id)
    log_file_path = Path(logger.get_log_filepath())

    if not log_file_path.exists():
        raise HTTPException(status_code=404, detail="Log file not found")

    # Update last activity timestamp
    active_sessions[session_id]["last_activity"] = time.time()

    return StreamingResponse(
        stream_log_file(log_file_path, idle_timeout),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


@router.post("/sessions/{session_id}/logs", tags=['logs'])
async def add_log(session_id: str, message: str, level: str = "INFO"):
    """
    Add a log message to the session
    """
    if session_id not in get_active_sessions():
        raise HTTPException(status_code=404, detail="Session not found")

    logger = SessionLogger(session_id)

    # Log with the appropriate level
    if level.upper() == "ERROR":
        logger.error(message)
    elif level.upper() == "WARNING":
        logger.warning(message)
    elif level.upper() == "CRITICAL":
        logger.critical(message)
    elif level.upper() == "DEBUG":
        logger.debug(message)
    else:
        logger.info(message)

    # Update last activity timestamp
    update_session_activity(session_id)

    return {"message": "Log added successfully"}