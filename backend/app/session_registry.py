# app/session_registry.py
import logging
import threading
from time import time
from typing import Dict, Any

from app.logger import SessionLogger, clear_all_logs
from app.system_monitor import SystemMonitor

# Configure logging
registry_logger = logging.getLogger('SessionRegistry')

# Thread-safe registry lock
_registry_lock = threading.RLock()

# Main registries
active_sessions: Dict[str, Dict[str, Any]] = {}
active_monitors: Dict[str, SystemMonitor] = {}


def register_session(session_id: str, metadata: Dict[str, Any]) -> None:
    """Register a new session"""
    with _registry_lock:
        active_sessions[session_id] = metadata
        registry_logger.info(f"Registered session: {session_id}")


def register_monitor(session_id: str, monitor: SystemMonitor) -> None:
    """Register a system monitor for a session"""
    with _registry_lock:
        active_monitors[session_id] = monitor
        if session_id in active_sessions:
            active_sessions[session_id]["monitoring"] = True
        registry_logger.info(f"Registered monitor for session: {session_id}")


def unregister_session(session_id: str) -> None:
    """Unregister a session and stop its monitor if active"""
    with _registry_lock:
        # Stop monitor if active
        stop_monitor(session_id)

        # Remove session from registry
        if session_id in active_sessions:
            del active_sessions[session_id]
            registry_logger.info(f"Unregistered session: {session_id}")

        # Clean up logger
        SessionLogger.cleanup_instance(session_id)


def stop_monitor(session_id: str) -> bool:
    """Stop a session's monitor if active"""
    with _registry_lock:
        if session_id in active_monitors:
            try:
                monitor = active_monitors[session_id]
                monitor.stop()
                del active_monitors[session_id]

                if session_id in active_sessions:
                    active_sessions[session_id]["monitoring"] = False

                registry_logger.info(f"Stopped monitor for session: {session_id}")
                return True
            except Exception as e:
                registry_logger.error(f"Error stopping monitor for session {session_id}: {e}")
                return False
        return False


def shutdown_all() -> Dict[str, int]:
    """Shutdown all active monitors and clean up sessions"""
    with _registry_lock:
        monitor_count = len(active_monitors)
        session_count = len(active_sessions)

        # Stop all monitors
        stopped_count = 0
        for session_id in list(active_monitors.keys()):
            try:
                if stop_monitor(session_id):
                    stopped_count += 1
            except Exception as e:
                registry_logger.error(f"Error during shutdown of monitor {session_id}: {e}")

        # Clear registries
        active_monitors.clear()
        active_sessions.clear()

        # Clear all log files
        try:
            deleted_log_count = clear_all_logs()
        except Exception as e:
            registry_logger.error(f"Error clearing logs: {e}")
            deleted_log_count = 0

        registry_logger.info(f"Shutdown complete: {stopped_count}/{monitor_count} monitors stopped, "
                             f"{session_count} sessions cleared, {deleted_log_count} log files deleted")

        return {
            "monitors_stopped": stopped_count,
            "sessions_cleared": session_count,
            "logs_deleted": deleted_log_count
        }


def get_active_sessions() -> Dict[str, Dict[str, Any]]:
    """Get a copy of active sessions"""
    with _registry_lock:
        return dict(active_sessions)


def get_active_monitors() -> Dict[str, SystemMonitor]:
    """Get a copy of active monitors"""
    with _registry_lock:
        return dict(active_monitors)


def update_session_activity(session_id: str) -> bool:
    """Update the last activity timestamp for a session"""
    with _registry_lock:
        if session_id in active_sessions:
            active_sessions[session_id]["last_activity"] = time()
            return True
        return False