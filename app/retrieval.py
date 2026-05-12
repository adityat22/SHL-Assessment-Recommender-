from typing import List, Dict
from rank_bm25 import BM25Okapi
import os
from .catalog import get_catalog_for_retrieval

# Global indexes (will be built on startup)
bm25_index = None
catalog_items = None

CACHE_DIR = "data"
BM25_CACHE = os.path.join(CACHE_DIR, "bm25.pkl")

def init_retrieval():
    """Initialize all retrieval indexes on startup."""
    global bm25_index, catalog_items
    
    print("Initializing retrieval indexes...")
    
    catalog_items = get_catalog_for_retrieval()
    
    # Build BM25 (Uses very little memory, perfect for Render Free Tier)
    print("Building BM25 index...")
    corpus = [item["combined_text"] for item in catalog_items]
    tokenized_corpus = [text.lower().split() for text in corpus]
    bm25_index = BM25Okapi(tokenized_corpus)
    
    print(f"✓ Retrieval initialized with {len(catalog_items)} items")

def hybrid_search(query: str, top_k: int = 20) -> List[Dict]:
    """Search: BM25 + rule-based boosting. (FAISS removed to fit in 512MB RAM limit)"""
    global bm25_index, catalog_items
    
    if not bm25_index:
        return []
    
    # 1. BM25 search
    query_tokens = query.lower().split()
    bm25_scores = bm25_index.get_scores(query_tokens)
    bm25_results = sorted(
        enumerate(bm25_scores),
        key=lambda x: x[1],
        reverse=True
    )[:top_k]
    
    # 3. Merge and score (Only BM25 now)
    all_results = {}
    for idx, score in bm25_results:
        all_results[idx] = score
    
    # 4. Apply rule-based boosts
    query_lower = query.lower()
    for idx, item in enumerate(catalog_items):
        boost = 1.0
        
        # Boost personality tests if "personality", "behavior", "culture fit" mentioned
        if any(word in query_lower for word in ["personality", "behavior", "attitude", "fit", "culture"]):
            if any("Personality & Behavior" in t for t in item["test_types"]):
                boost *= 1.5
        
        # Boost knowledge tests if "skill", "knowledge", "coding", etc.
        if any(word in query_lower for word in ["skill", "knowledge", "coding", "java", "python", "sql", "aws"]):
            if any("Knowledge & Skills" in t for t in item["test_types"]):
                boost *= 1.3
        
        # Boost ability/cognitive tests if "reasoning", "cognitive", "ability" mentioned
        if any(word in query_lower for word in ["reasoning", "cognitive", "ability", "aptitude", "iq"]):
            if any("Ability & Aptitude" in t for t in item["test_types"]):
                boost *= 1.5
        
        # Boost if job level matches
        if any(word in query_lower for word in ["graduate", "entry", "junior"]):
            if "Graduate" in item["job_levels"] or "Entry-Level" in item["job_levels"]:
                boost *= 1.2
        
        if any(word in query_lower for word in ["senior", "executive", "cxo", "director"]):
            if "Senior" in item["job_levels"] or "Executive" in item["job_levels"] or "Director" in item["job_levels"]:
                boost *= 1.2
        
        if idx in all_results:
            all_results[idx] *= boost
    
    # 5. Sort and return
    sorted_results = sorted(
        [(idx, score) for idx, score in all_results.items()],
        key=lambda x: x[1],
        reverse=True
    )[:top_k]
    
    return [
        {
            **catalog_items[idx],
            "score": score
        }
        for idx, score in sorted_results
    ]

def hard_coded_recommendations(context: Dict) -> List[Dict]:
    """Apply hard-coded rules from analyzing the 10 traces."""
    global catalog_items
    
    recommendations = []
    added_ids = set()
    
    # RULE 1: If personality is requested, always add OPQ32r
    if any(word in str(context).lower() for word in ["personality", "behavior", "fit", "culture", "attitude"]):
        for item in catalog_items:
            if "OPQ" in item["name"] and "32r" in item["name"]:
                if item["id"] not in added_ids:
                    recommendations.append(item)
                    added_ids.add(item["id"])
                break
    
    # RULE 2: If cognitive/reasoning requested, add Verify G+
    if any(word in str(context).lower() for word in ["cognitive", "reasoning", "ability", "aptitude"]):
        for item in catalog_items:
            if "Verify" in item["name"] and "G+" in item["name"]:
                if item["id"] not in added_ids:
                    recommendations.append(item)
                    added_ids.add(item["id"])
                break
    
    # RULE 3: Graduate + situational judgment = Graduate Scenarios
    if "graduate" in str(context).lower() and any(word in str(context).lower() for word in ["situational", "judgment", "scenario"]):
        for item in catalog_items:
            if "Graduate Scenarios" in item["name"]:
                if item["id"] not in added_ids:
                    recommendations.append(item)
                    added_ids.add(item["id"])
                break
    
    return recommendations