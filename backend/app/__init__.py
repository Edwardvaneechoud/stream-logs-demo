import os
from pathlib import Path
import asyncio
from typing import Any


class ServerRun:
    exit: bool = False
    shutdown_event = asyncio.Event()
    server_instance: Any = None
    shutdown_in_progress: bool = False


# Create logs directory if it doesn't exist
logs_dir = Path(os.path.dirname(os.path.abspath(__file__))) / "logs"
logs_dir.mkdir(exist_ok=True, parents=True)