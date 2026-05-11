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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize on startup using async background task
import asyncio

@app.on_event("startup")
async def startup_event():
    """Trigger initialization in the background so it doesn't block port binding."""
    print("🚀 Starting SHL Recommender API...")
    loop = asyncio.get_event_loop()
    loop.run_in_executor(None, init_retrieval)
    print("✓ Retrieval initialization started in background")

@app.get("/health")
async def health():
    """Health check endpoint."""
    return {"status": "ok"}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """Main chat endpoint."""
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