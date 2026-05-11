import os
from dotenv import load_dotenv
import openai

load_dotenv()

def get_llm_config():
    """Get LLM configuration from environment."""
    provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("LLM_MODEL", "gpt-4o-mini")
    
    if provider == "openrouter":
        api_key = os.getenv("OPENROUTER_API_KEY")
        base_url = "https://openrouter.ai/api/v1"
    else:  # openai
        api_key = os.getenv("OPENAI_API_KEY")
        base_url = "https://api.openai.com/v1"
    
    return {
        "provider": provider,
        "model": model,
        "api_key": api_key,
        "base_url": base_url
    }

def call_llm(prompt: str, max_tokens: int = 1000, temperature: float = 0.7) -> str:
    """Call the LLM with the given prompt."""
    config = get_llm_config()
    
    client = openai.OpenAI(
        api_key=config["api_key"],
        base_url=config["base_url"]
    )
    
    try:
        response = client.chat.completions.create(
            model=config["model"],
            messages=[
                {"role": "system", "content": "You are an expert SHL assessment recommender. You only recommend from the SHL catalog. Be concise and helpful."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=max_tokens,
            temperature=temperature,
            timeout=25  # Leave 5 sec buffer before 30 sec timeout
        )
        
        return response.choices[0].message.content
    except Exception as e:
        print(f"LLM Error: {e}")
        return ""

def generate_grounded_response(state: dict, recommendations: list, messages: list) -> str:
    """Generate a natural response grounded in retrieved recommendations. NO LLM CALL - instant template."""
    
    role = state.get('role_hiring_for')
    
    # If no role extracted, ask for more info
    if not role:
        return "I need more information to recommend assessments."
    
    # Instant template - no LLM latency!
    return f"For the {role} role, these are the recommended assessments:"