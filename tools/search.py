import json
from config import DATA_DIR

def _load_dataset(filename: str) -> list | dict:
    """Helper to pull JSON into memory."""
    filepath = DATA_DIR / filename
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print(f"[WARNING] Dataset missing: {filepath}")
        return []
    except json.JSONDecodeError:
        print(f"[ERROR] Corrupted JSON in: {filepath}")
        return []

# ---------------------------------------------------------
# In-Memory Data Store (Loaded once on import)
# ---------------------------------------------------------
MANIFEST = _load_dataset("manifest.json")
SUPPLIERS = _load_dataset("suppliers.json")
PROFESSIONALS = _load_dataset("professionals.json")
OPPORTUNITIES = _load_dataset("opportunities.json")
INTERACTIONS = _load_dataset("interactions.json")

# ---------------------------------------------------------
# Pure Retrieval Functions
# ---------------------------------------------------------
def get_all_suppliers() -> list:
    return SUPPLIERS

def get_all_professionals() -> list:
    return PROFESSIONALS

def get_all_opportunities() -> list:
    return OPPORTUNITIES

def get_all_interactions() -> list:
    return INTERACTIONS

def get_entity_by_id(entity_id: str) -> dict | None:
    """
    Dynamically routes to the correct dataset based on the ID prefix 
    defined in the assignment manifest.
    """
    if not entity_id:
        return None
        
    if entity_id.startswith("SUP-"):
        dataset = SUPPLIERS
    elif entity_id.startswith("PRO-"):
        dataset = PROFESSIONALS
    elif entity_id.startswith("OPP-"):
        dataset = OPPORTUNITIES
    elif entity_id.startswith("INT-"):
        dataset = INTERACTIONS
    else:
        return None

    # Return the first matching record
    for record in dataset:
        if record.get("id") == entity_id:
            return record
            
    return None