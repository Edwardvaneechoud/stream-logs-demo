import asyncio
import json
import time
import psutil
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.responses import StreamingResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

app = FastAPI()

# Mount static files (e.g. index.html, styles, JS)
app.mount("/static", StaticFiles(directory="static"), name="static")

# Optional CORS (if not needed anymore, you can remove it)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Adjust in production!
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Format data as SSE message
async def format_sse_message(data: str) -> str:
    """Format the data as a proper SSE message"""
    return f"data: {json.dumps(data)}\n\n"


# Stream logs with system RAM usage
async def stream_logs() -> AsyncGenerator[str, None]:
    """Stream system RAM usage as log entries"""
    # Initial log entry
    yield await format_sse_message("Starting system RAM monitoring...")

    # Send 20 RAM usage log entries
    for i in range(1, 21):
        # Get current timestamp
        timestamp = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())

        # Get RAM usage
        ram = psutil.virtual_memory()
        ram_percent = ram.percent
        ram_total = ram.total / (1024 * 1024 * 1024)  # Convert to GB
        ram_used = ram_total * ram_percent/100
        log_entry = f"{timestamp} - RAM usage: {ram_percent}% ({ram_used:.2f}GB / {ram_total:.2f}GB)"

        yield await format_sse_message(log_entry)
        await asyncio.sleep(1)  # One second delay between logs

    # Final log entry
    yield await format_sse_message("RAM monitoring completed")


# API endpoint to stream logs
@app.get("/api/stream")
async def stream_logs_endpoint():
    """Stream RAM usage logs using Server-Sent Events"""
    return StreamingResponse(
        stream_logs(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )


# Serve the HTML frontend from root path
@app.get("/")
async def serve_index():
    return FileResponse("static/index.html")


# Entry point
def run():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()