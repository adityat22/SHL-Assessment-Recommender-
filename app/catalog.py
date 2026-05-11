import requests
import json
import os
from typing import List, Dict, Optional

CATALOG_URL = "https://tcp-us-prod-rnd.shl.com/voiceRater/shl-ai-hiring/shl_product_catalog.json"
DATA_DIR = "data"
CATALOG_FILE = os.path.join(DATA_DIR, "catalog.json")

def ensure_data_dir():
    if not os.path.exists(DATA_DIR):
        os.makedirs(DATA_DIR)

def download_catalog() -> List[Dict]:
    """Download and cache the SHL catalog."""
    ensure_data_dir()
    
    if os.path.exists(CATALOG_FILE):
        print(f"Loading catalog from cache: {CATALOG_FILE}")
        with open(CATALOG_FILE, "r", encoding="utf-8") as f:
            return json.loads(f.read(), strict=False)
    
    print("Downloading catalog from SHL...")
    response = requests.get(CATALOG_URL, timeout=10)
    response.raise_for_status()
    
    catalog = json.loads(response.text, strict=False)
    
    # Save to cache
    with open(CATALOG_FILE, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)
    
    print(f"Catalog downloaded and cached: {len(catalog)} items")
    return catalog

def normalize_catalog_item(item: Dict) -> Dict:
    """Normalize a catalog item to a standard format."""
    return {
        "entity_id": item.get("entity_id"),
        "name": item.get("name", ""),
        "url": item.get("link", ""),
        "description": item.get("description", ""),
        "job_levels": item.get("job_levels", []),
        "languages": item.get("languages", []),
        "duration": item.get("duration", ""),
        "remote": item.get("remote", "no"),
        "adaptive": item.get("adaptive", "no"),
        "test_types": item.get("keys", []),  # This is the "test type"
        "raw": item
    }

def get_all_items() -> List[Dict]:
    """Load and normalize all catalog items."""
    raw_catalog = download_catalog()
    return [normalize_catalog_item(item) for item in raw_catalog]

def get_allowed_urls() -> set:
    """Get set of all valid catalog URLs for validation."""
    items = get_all_items()
    return {item["url"] for item in items if item["url"]}

def find_item_by_name(name: str) -> Optional[Dict]:
    """Find a catalog item by exact name match."""
    items = get_all_items()
    for item in items:
        if item["name"].lower().strip() == name.lower().strip():
            return item
    return None

def find_item_by_fuzzy_name(name: str) -> Optional[Dict]:
    """Find a catalog item by fuzzy name match."""
    items = get_all_items()
    name_lower = name.lower().strip()
    
    # Exact match first
    for item in items:
        if item["name"].lower() == name_lower:
            return item
    
    # Substring match
    for item in items:
        if name_lower in item["name"].lower():
            return item
    
    # Reverse: check if item name is in the query
    for item in items:
        if item["name"].lower() in name_lower:
            return item
    
    return None

def get_catalog_for_retrieval() -> List[Dict]:
    """Return catalog in a format optimized for retrieval."""
    items = get_all_items()
    return [
        {
            "id": item["entity_id"],
            "name": item["name"],
            "url": item["url"],
            "description": item["description"],
            "job_levels": item["job_levels"],
            "test_types": item["test_types"],
            "languages": item["languages"],
            "duration": item["duration"],
            "combined_text": f"{item['name']} {item['description']} {' '.join(item['job_levels'])} {' '.join(item['test_types'])}"
        }
        for item in items
    ]