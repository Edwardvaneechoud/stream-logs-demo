# stream_logs.py
import asyncio
import json
from typing import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

app = FastAPI()

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

async def format_sse_message(data: str) -> str:
    """Format the data as a proper SSE message"""
    return f"data: {json.dumps(data)}\n\n"

async def stream_counter() -> AsyncGenerator[str, None]:
    """Stream numbers 1-9 and then 'explode' as SSE events"""
    try:
        for i in range(1, 10):
            yield await format_sse_message(str(i))
            await asyncio.sleep(1)  # Wait 1 second between numbers
        
        # Final message
        yield await format_sse_message("explode!")
        
    except Exception as e:
        error_msg = await format_sse_message(f"Error: {str(e)}")
        yield error_msg

@app.get("/api/stream")
async def stream_logs():
    """Stream logs using Server-Sent Events (SSE)"""
    return StreamingResponse(
        stream_counter(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "Content-Type": "text/event-stream",
        }
    )

@app.get("/")
async def root():
    """Basic root endpoint."""
    return {"message": "Welcome to the Simple Stream Logs API"}


def run():
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    run()
