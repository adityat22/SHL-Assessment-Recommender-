from typing import List, Dict
from .schemas import Recommendation, ChatResponse
from .state_machine import extract_conversation_state, get_last_recommendations_from_messages
from .retrieval import hybrid_search, hard_coded_recommendations
from .llm import generate_grounded_response
from .catalog import find_item_by_fuzzy_name, get_allowed_urls

def process_chat(messages: list) -> ChatResponse:
    """Main agent logic."""
    
    # Count user turns
    user_turns = sum(1 for msg in messages if getattr(msg, "role", msg.get("role", "")) == "user")
    
    # 1. Extract conversation state
    state = extract_conversation_state(messages)
    print("DEBUG EXTRACTED STATE:", state)
    
    # 2. HARD POLICY: Turn Cap Limit
    if user_turns >= 8:
        # Wrap up the conversation with final recommendations
        search_query = f"{state.get('role_hiring_for', '')} {' '.join(state.get('skills_required', []))} {' '.join(state.get('test_preferences', []))}"
        candidates = hybrid_search(search_query, top_k=10)
        recs = [
            Recommendation(
                name=item["name"],
                url=item["url"],
                test_type=", ".join(item.get("test_types", ["Unknown"]))
            )
            for item in candidates
        ]
        return ChatResponse(
            reply="We've reached our time limit for this conversation. Here are the final recommendations based on our discussion.",
            recommendations=recs,
            end_of_conversation=True
        )

    # 3. HARD POLICY: Legal/Off-Topic
    if state["legal_or_off_topic_question"]:
        return ChatResponse(
            reply="I can help you select assessments from the SHL catalog, but I cannot provide legal advice or interpret regulatory obligations. For legal questions, please consult your HR or legal team.",
            recommendations=[],
            end_of_conversation=False
        )
    
    # 4. HARD POLICY: User confirmed shortlist
    if state["user_confirmed_shortlist"]:
        last_recs = get_last_recommendations_from_messages(messages)
        recs = [
            Recommendation(
                name=r.get("name", ""),
                url=r.get("url", ""),
                test_type=r.get("test_type", "")
            )
            for r in last_recs
        ]
        return ChatResponse(
            reply="Perfect, your assessment battery is confirmed.",
            recommendations=recs,
            end_of_conversation=True
        )
    
    # 4. HARD POLICY: Comparison request
    if state["asked_for_comparison"]:
        comparison_reply = handle_comparison(state["comparison_targets"])
        return ChatResponse(
            reply=comparison_reply,
            recommendations=[],
            end_of_conversation=False
        )
    
    # 5. HARD POLICY: Insufficient context for recommendation
    if not state["role_hiring_for"] and not state["skills_required"]:
        return ChatResponse(
            reply="I'd like to help narrow down the right assessments. What role or job family are you hiring for, and what specific skills, traits, or competencies do you want to measure?",
            recommendations=[],
            end_of_conversation=False
        )
    
    # 6. Retrieval & Recommendation
    # Build search query
    search_query = f"{state.get('role_hiring_for', '')} {' '.join(state.get('skills_required', []))} {' '.join(state.get('test_preferences', []))}"
    
    # Get candidates
    candidates = hybrid_search(search_query, top_k=30)
    
    # Apply hard-coded rules
    hard_coded = hard_coded_recommendations(search_query)
    
    # Merge and deduplicate
    all_items = {item["id"]: item for item in candidates + hard_coded}
    
    # Filter out excluded items
    must_exclude_ids = set()
    for exclude_name in state.get("must_exclude_tests", []):
        item = find_item_by_fuzzy_name(exclude_name)
        if item:
            must_exclude_ids.add(item["entity_id"])
    
    filtered_items = [
        item for item in all_items.values()
        if item["id"] not in must_exclude_ids
    ]
    
    # Sort by score (if available)
    filtered_items.sort(key=lambda x: x.get("score", 0), reverse=True)
    
    # Limit to 10 recommendations
    final_recs = filtered_items[:10]
    
    # 7. Generate natural response
    reply = generate_grounded_response(state, final_recs, messages)
    
    # 8. Format recommendations
    recommendations = [
        Recommendation(
            name=item["name"],
            url=item["url"],
            test_type=", ".join(item.get("test_types", ["Unknown"]))
        )
        for item in final_recs
    ]
    
    # Validate all URLs
    allowed_urls = get_allowed_urls()
    recommendations = [
        r for r in recommendations
        if r.url in allowed_urls
    ]
    
    return ChatResponse(
        reply=reply,
        recommendations=recommendations if recommendations else [],
        end_of_conversation=False
    )

def handle_comparison(target_names: List[str]) -> str:
    """Generate a comparison between two assessments."""
    from .catalog import get_all_items
    
    items = get_all_items()
    found_items = {}
    
    for target in target_names:
        for item in items:
            if target.lower() in item["name"].lower():
                found_items[target] = item
                break
    
    if len(found_items) < 2:
        return f"I couldn't find sufficient details to compare. Please specify the exact assessment names you'd like me to compare."
    
    comparison_text = "Here's how they compare:\n\n"
    for name, item in found_items.items():
        comparison_text += f"**{item['name']}**: {item['description']}\n"
        comparison_text += f"Test Types: {', '.join(item['test_types'])}\n"
        comparison_text += f"Duration: {item['duration'] if item['duration'] else 'Variable'}\n\n"
    
    return comparison_text