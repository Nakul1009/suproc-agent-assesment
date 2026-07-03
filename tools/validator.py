from tools.search import get_entity_by_id

def validate_recommendations(recommended_ids: list[str], constraints: dict, requested_count: int = 3) -> dict:
    """
    Validates proposed recommendations against the raw dataset to ensure 
    the agent didn't hallucinate or bypass constraints.
    """
    failures = []
    seen = set()
    
    # 1. Count Check
    if len(recommended_ids) < requested_count:
        failures.append(f"Requested {requested_count} results, but only provided {len(recommended_ids)}.")
        
    for entity_id in recommended_ids:
        # 2. Duplicate Check
        if entity_id in seen:
            failures.append(f"Duplicate recommendation detected: {entity_id}.")
        seen.add(entity_id)
        
        entity = get_entity_by_id(entity_id)
        
        # 3. Existence Check (No hallucinations allowed)
        if not entity:
            failures.append(f"Entity {entity_id} does not exist in the dataset.")
            continue
            
        # 4. Active Status Check (Catches the SUP-025 suspended trap)
        if entity.get("status") != "active":
            failures.append(f"Entity {entity_id} is not active (Status: {entity.get('status')}).")
            
        # 5. Hard Constraints Re-Verification
        req_certs = constraints.get("certifications", [])
        entity_certs = entity.get("certifications") or []
        for cert in req_certs:
            if cert not in entity_certs:
                failures.append(f"Entity {entity_id} is missing required certification: '{cert}'.")
                
        req_delivery = constraints.get("maximum_delivery_days")
        entity_delivery = entity.get("max_delivery_days")
        if req_delivery and entity_delivery and entity_delivery > req_delivery:
            failures.append(
                f"Entity {entity_id} maximum delivery time ({entity_delivery} days) "
                f"exceeds the hard constraint ({req_delivery} days)."
            )

    if failures:
        return {
            "is_valid": False,
            "error_report": "\n".join(failures)
        }
        
    return {
        "is_valid": True,
        "error_report": "All recommendations passed deterministic validation."
    }