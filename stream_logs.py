import asyncio
import json
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

# SSE stream endpoint
async def format_sse_message(data: str) -> str:
    return f"data: {json.dumps(data)}\n\n"

async def stream_counter() -> AsyncGenerator[str, None]:
    for i in range(1, 10):
        yield await format_sse_message(str(i))
        await asyncio.sleep(1)
    yield await format_sse_message("explode!")

@app.get("/api/stream")
async def stream_logs():
    return StreamingResponse(
        stream_counter(),
        media_type="text/event-stream"
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
