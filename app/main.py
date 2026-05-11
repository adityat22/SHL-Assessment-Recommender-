from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .schemas import ChatRequest, ChatResponse
from .agent import process_chat
from .retrieval import init_retrieval

# Initialize FastAPI
app = FastAPI(
    title="SHL Assessment Recommender",
    description="Conversational agent for recommending SHL assessments",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize lazily without blocking the main thread
import asyncio
from fastapi import BackgroundTasks

_is_initialized = False
_init_lock = asyncio.Lock()

async def ensure_initialized():
    """Lazy-load retrieval components only when needed, without blocking the event loop."""
    global _is_initialized
    if not _is_initialized:
        async with _init_lock:
            if not _is_initialized:
                try:
                    print("🚀 Starting lazy initialization of SHL Recommender Retrieval (Threaded)...")
                    loop = asyncio.get_event_loop()
                    # Run the heavy blocking function in a separate thread
                    await loop.run_in_executor(None, init_retrieval)
                    _is_initialized = True
                    print("✓ Lazy Retrieval initialization complete")
                except Exception as e:
                    print(f"✗ Error during lazy retrieval initialization: {e}")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint."""
    # Ensure retrieval components are loaded on the first request 
    await ensure_initialized()
    
    try:
        messages_dicts = [{"role": msg.role, "content": msg.content} for msg in request.messages]
        response = process_chat(messages_dicts)
        return response
    except Exception as e:
        print(f"Error in /chat: {e}")
        return ChatResponse(
            reply="An error occurred while processing your request. Please try again.",
            recommendations=[],
            end_of_conversation=False
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)