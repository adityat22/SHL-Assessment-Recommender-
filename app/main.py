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

# Initialize on startup using background task securely bounded to the app lifecycle
from fastapi import BackgroundTasks

# Remove the on_event startup logic completely
# Instead, we will lazily initialize during the first chat request

_is_initialized = False

def ensure_initialized():
    """Lazy-load retrieval components only when needed."""
    global _is_initialized
    if not _is_initialized:
        try:
            print("🚀 Starting lazy initialization of SHL Recommender Retrieval...")
            init_retrieval()
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
    # Ensure retrieval components are loaded on the first request rather than blocking startup
    ensure_initialized()
    
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