# main.py
import asyncio
import signal
from contextlib import asynccontextmanager

import uvicorn
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import ServerRun
from app.routes import logs


def handle_shutdown_signal(sig_name):
    """Signal handler for asyncio loop."""
    print(f"Signal {sig_name} received by loop signal handler.")

    # Set the shutdown event
    if not ServerRun.shutdown_event.is_set():
        print(f"Setting shutdown_event via loop signal handler ({sig_name}).")
        ServerRun.shutdown_event.set()
        ServerRun.exit = True
    else:
        print(f"Shutdown_event already set when signal ({sig_name}) received.")

    # Check server instance - use a local variable to avoid race conditions
    current_server = ServerRun.server_instance
    if current_server:
        if not current_server.should_exit:
            print(f"Signal handler setting Uvicorn's should_exit flag.")
            current_server.should_exit = True
        else:
            print(f"Uvicorn's should_exit flag was already set.")
    else:
        print("Signal handler: server_instance is None, possibly already shutting down.")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handles application startup and cleanup during shutdown."""
    print('Lifespan: Startup phase beginning...')

    registered_signals = False
    try:
        loop = asyncio.get_running_loop()
        for sig_name in ('SIGINT', 'SIGTERM'):
            sig = getattr(signal, sig_name)
            loop.add_signal_handler(
                sig,
                lambda s=sig_name: handle_shutdown_signal(s)
            )
            print(f"Lifespan: Registered asyncio signal handler for {sig_name}.")
        registered_signals = True
    except NotImplementedError:
        print("Lifespan WARNING: asyncio signal handlers not supported on this OS. CTRL+C might not trigger event directly.")
    except Exception as e:
        print(f"Lifespan ERROR: Could not register signal handlers: {e}")

    try:
        yield
    finally:
        print('Lifespan: Shutdown/Cleanup phase starting...')

        if not ServerRun.shutdown_event.is_set():
            print('Lifespan WARNING: Shutdown event NOT set before cleanup phase, setting it now.')
            ServerRun.shutdown_event.set()
            ServerRun.exit = True

        print("Lifespan: Cleaning up sessions and stopping monitors...")
        try:
            from app.session_registry import shutdown_all
            cleanup_results = shutdown_all()
            print(f"Lifespan: Cleanup complete - stopped {cleanup_results['monitors_stopped']} monitors, "
                  f"cleared {cleanup_results['sessions_cleared']} sessions, "
                  f"deleted {cleanup_results['logs_deleted']} log files")
        except ImportError as ie:
            print(f"Lifespan: Error importing session registry: {ie}")
        except Exception as e:
            print(f"Lifespan: Error during session cleanup: {e}")

        print("Lifespan: Cleaning up other service resources...")
        await asyncio.sleep(0.2)
        print("Lifespan: Application shutdown cleanup complete.")


app = FastAPI(
    title="Stream Logs Demo API",
    description="A simple API to demonstrate streaming logs with FastAPI and Server-Sent Events",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(logs.router, prefix="/api")


@app.get("/")
async def root():
    """Basic root endpoint."""
    return {"message": "Welcome to the Stream Logs Demo API"}


@app.post("/shutdown")
async def request_shutdown():
    """Endpoint to request graceful shutdown."""
    print("Shutdown endpoint called.")
    if not ServerRun.shutdown_event.is_set():
        print("Shutdown endpoint: Setting shutdown event.")
        ServerRun.shutdown_event.set()
        ServerRun.exit = True
    if ServerRun.server_instance:
        print("Shutdown endpoint: Setting Uvicorn's should_exit flag.")
        ServerRun.server_instance.should_exit = True
    else:
        print("Shutdown endpoint: Server instance not found.")
    return {"message": "Shutdown initiated"}


def run(host="0.0.0.0", port=8000):
    """Configure and run the FastAPI app using Uvicorn."""
    print(f"Configuring Uvicorn server on {host}:{port}")

    config = uvicorn.Config(
        "app.main:app",
        host=host,
        port=port,
        loop="asyncio",
        lifespan="on",
    )
    server = uvicorn.Server(config)
    ServerRun.server_instance = server  # Use ServerRun instead of ServerInstance

    print('Starting Uvicorn server run loop...')
    try:
        server.run()
    except Exception as e:
        print(f"Error during server run: {e}")
        if not ServerRun.shutdown_event.is_set():
            ServerRun.shutdown_event.set()
            ServerRun.exit = True


if __name__ == "__main__":
    run()
