# logger.py
import logging
import os
import threading
from pathlib import Path
from typing import Dict

# Configure main logger
main_logger = logging.getLogger('StreamLogger')
main_logger.setLevel(logging.INFO)
console_handler = logging.StreamHandler()
console_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
main_logger.addHandler(console_handler)


def get_logs_dir() -> Path:
    """Get the directory for application logs"""
    base_dir = Path(os.path.dirname(os.path.abspath(__file__)))
    logs_dir = base_dir / "logs"
    logs_dir.mkdir(exist_ok=True, parents=True)
    return logs_dir


def get_log_file(session_id: str) -> Path:
    """Get the path to the log file for a specific session"""
    return get_logs_dir() / f"session_{session_id}.log"


class SessionLogger:
    """Thread-safe logger for streaming sessions"""
    _instances: Dict[str, 'SessionLogger'] = {}
    _instances_lock: threading.RLock = threading.RLock()

    def __new__(cls, session_id: str, clear_existing_logs: bool = False):
        with cls._instances_lock:
            if session_id not in cls._instances:
                instance = super().__new__(cls)
                instance._initialize(session_id, clear_existing_logs)
                cls._instances[session_id] = instance
            else:
                instance = cls._instances[session_id]
                if clear_existing_logs:
                    instance.clear_log_file()
            return instance

    def _initialize(self, session_id: str, clear_existing_logs: bool = False):
        self.session_id = session_id
        self._logger = None
        self.log_file_path = get_log_file(self.session_id)
        self._file_lock = threading.RLock()
        self._setup_logger()

    def _setup_logger(self):
        """Set up the file logger for this session"""
        logger_name = f'Session.{self.session_id}'
        self._logger = logging.getLogger(logger_name)
        self._logger.setLevel(logging.INFO)

        # Remove existing handlers
        for handler in self._logger.handlers[:]:
            handler.close()
            self._logger.removeHandler(handler)

        # Add file handler
        file_handler = logging.FileHandler(self.log_file_path)
        formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)

    def clear_log_file(self):
        """Clear the log file for this session"""
        with self._file_lock:
            try:
                with open(self.log_file_path, 'w') as _:
                    pass
                main_logger.info(f"Log file cleared for session {self.session_id}")
            except Exception as e:
                main_logger.error(f"Error clearing log file {self.log_file_path}: {e}")

    def info(self, msg: str, *args, **kwargs):
        """Log an info message"""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['session_id'] = self.session_id
        self._logger.info(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log a warning message"""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['session_id'] = self.session_id
        self._logger.warning(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """Log a debug message"""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['session_id'] = self.session_id
        self._logger.debug(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log an error message"""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['session_id'] = self.session_id
        self._logger.error(msg, *args, **kwargs)

    def critical(self, msg: str, *args, **kwargs):
        """Log a critical message"""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['session_id'] = self.session_id
        self._logger.critical(msg, *args, **kwargs)

    def log(self, level: int, msg: str, *args, **kwargs):
        """Log a message with the specified level"""
        if 'extra' not in kwargs:
            kwargs['extra'] = {}
        kwargs['extra']['session_id'] = self.session_id
        self._logger.log(level, msg, *args, **kwargs)

    def get_log_filepath(self):
        """Get the path to the log file for this session"""
        return str(self.log_file_path)

    @classmethod
    def cleanup_instance(cls, session_id: str):
        """Clean up a specific session logger instance"""
        with cls._instances_lock:
            if session_id in cls._instances:
                instance = cls._instances[session_id]

                # Close handlers
                for handler in instance._logger.handlers[:]:
                    handler.close()
                    instance._logger.removeHandler(handler)

                del cls._instances[session_id]


def clear_all_logs():
    """Delete all session log files"""
    logs_dir = get_logs_dir()
    deleted_count = 0

    with SessionLogger._instances_lock:
        session_ids = list(SessionLogger._instances.keys())
        for session_id in session_ids:
            SessionLogger.cleanup_instance(session_id)

    # Now delete all log files
    for log_file in logs_dir.glob("*.log"):
        try:
            os.remove(log_file)
            deleted_count += 1
        except Exception as e:
            main_logger.error(f"Error removing log file {log_file}: {e}")

    main_logger.info(f"Successfully deleted {deleted_count} log files")
    return deleted_count
