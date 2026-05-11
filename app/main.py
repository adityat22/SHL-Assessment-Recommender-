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
import threading
import time

_is_initialized = False
_is_initializing = False

def background_init():
    global _is_initialized, _is_initializing
    if _is_initialized or _is_initializing:
        return
    
    _is_initializing = True
    try:
        print("🚀 Starting SHL Recommender Retrieval Model Download in Background...")
        init_retrieval()
        _is_initialized = True
        print("✓ Lazy Retrieval initialization complete")
    except Exception as e:
        print(f"✗ Error during lazy retrieval initialization: {e}")
    finally:
        _is_initializing = False

def ensure_initialized():
    """Trigger background initialization if not started."""
    if not _is_initialized and not _is_initializing:
        # Start a totally detached native thread, so it doesn't lock asyncio
        t = threading.Thread(target=background_init, daemon=True)
        t.start()

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint."""
    ensure_initialized()
    
    if not _is_initialized:
        # If the model is currently downloading, return a user-friendly waiting message
        return ChatResponse(
            reply="The AI brain is currently powering up and downloading its assessment models on the Render server. Please wait about 30 seconds and ask me again! 🧠⏳",
            recommendations=[],
            end_of_conversation=False
        )
    
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