import json
import os
import re
from typing import Dict, Any
from dotenv import load_dotenv

load_dotenv()

def extract_conversation_state(messages: list) -> Dict[str, Any]:
    """Extract structured state from conversation history using fast heuristics to stay under 1s latency."""
    if not messages:
        return _default_state()
        
    state = _default_state()
    last_msg = messages[-1]
    last_content = getattr(last_msg, "content", last_msg.get("content", "") if isinstance(last_msg, dict) else "").lower()
    
    state["latest_user_message"] = last_content
    
    # 1. Check for vague query on Turn 1 (or any turn)
    vague_greetings = ["hi", "hello", "hey", "help me", "i need help", "recommend me some tests", "what tests do you have"]
    is_vague = len(last_content.split()) < 3 or any(last_content == g for g in vague_greetings)
    
    if not is_vague:
        state["role_hiring_for"] = last_content # Naive fallback: treat query as role/query
        
    # 2. Check for legal or off-topic
    legal_keywords = ["legal", "lawsuit", "sue", "compliance", "regulatory", "court", "lawyer", "recipe", "weather", "president", "movie"]
    if any(k in last_content for k in legal_keywords):
        state["legal_or_off_topic_question"] = True
        
    # 3. Check for shortlist confirmation
    confirm_keywords = ["confirm", "perfect", "good", "done", "happy with", "looks good", "thanks", "that works", "finalize"]
    if any(k in last_content for k in confirm_keywords) and "but" not in last_content and "compare" not in last_content:
        # Only confirm if we've actually offered recommendations previously
        if any("https://www.shl.com" in getattr(m, "content", m.get("content", "") if isinstance(m, dict) else "") for m in messages):
            state["user_confirmed_shortlist"] = True

    # 4. Check for comparison
    if "compare" in last_content or "difference between" in last_content:
        state["asked_for_comparison"] = True
        # Naive extraction - just pass the whole message as a target list to the comparison handler
        state["comparison_targets"] = [words for words in last_content.split(" ") if len(words) > 4]

    # 5. Check for excludes/includes
    if "exclude" in last_content or "remove" in last_content or "don't include" in last_content or "no " in last_content:
        # Try to find what they want excluded (very naive heuristic)
        words = last_content.split()
        for i, word in enumerate(words):
            if word in ["exclude", "remove", "no", "without"] and i + 1 < len(words):
                state["must_exclude_tests"].append(words[i+1])
                if i + 2 < len(words):
                    state["must_exclude_tests"].append(words[i+2])

    return state

def _default_state() -> Dict[str, Any]:
    return {
        "intent": "refine",
        "role_hiring_for": None,
        "seniority": None,
        "skills_required": [],
        "test_preferences": [],
        "must_include_tests": [],
        "must_exclude_tests": [],
        "legal_or_off_topic_question": False,
        "user_confirmed_shortlist": False,
        "asked_for_comparison": False,
        "comparison_targets": [],
        "latest_user_message": ""
    }

def get_last_recommendations_from_messages(messages: list) -> list:
    """Extract the last recommendation list from conversation."""
    # Look for previous assistant messages with recommendation markers
    for msg in reversed(messages):
        role = getattr(msg, "role", msg.get("role", "") if isinstance(msg, dict) else "")
        content = getattr(msg, "content", msg.get("content", "") if isinstance(msg, dict) else "")
        if role == "assistant":
            # Try to find test names/links in the message
            if "https://www.shl.com" in content:
                # This message contains recommendations
                return extract_recs_from_text(content)
    return []

def extract_recs_from_text(text: str) -> list:
    """Extract recommendation items from agent response text."""
    # This is a heuristic - we look for SHL URLs and preceding names
    import re
    
    pattern = r'\| \d+ \| ([^|]+) \| ([^|]*) \| (https://www\.shl\.com[^\s|]+)'
    matches = re.findall(pattern, text)
    
    recs = []
    for match in matches:
        name, test_type, url = match
        recs.append({
            "name": name.strip(),
            "url": url.strip(),
            "test_type": test_type.strip() if test_type.strip() else "Unknown"
        })
    
    return recs