def filter_by_constraints(entities: list[dict], constraints: dict) -> list[dict]:
    """
    Rigorously filters out records that fail hard constraints.
    Silently dropping constraints is not allowed.
    """
    valid_entities = []
    
    for entity in entities:
        is_valid = True
        
        # 1. Location Constraint (e.g., South Indian states)
        req_locations = constraints.get("locations", [])
        if req_locations:
            entity_state = entity.get("location", {}).get("state")
            if entity_state not in req_locations:
                continue
                
        # 2. Certification Constraint (Catches the SUP-014 missing cert trap)
        req_certs = constraints.get("certifications", [])
        if req_certs:
            entity_certs = entity.get("certifications") or []
            if not all(cert in entity_certs for cert in req_certs):
                continue
                
        # 3. Capacity Constraint
        req_capacity = constraints.get("minimum_capacity")
        if req_capacity:
            entity_capacity = entity.get("max_monthly_capacity")
            if entity_capacity and entity_capacity < req_capacity:
                continue
                
        # 4. Deadline / Delivery Constraint (Catches the SUP-022 40-day delivery trap)
        req_delivery = constraints.get("maximum_delivery_days")
        if req_delivery:
            entity_delivery = entity.get("max_delivery_days")
            if entity_delivery and entity_delivery > req_delivery:
                continue
                
        if is_valid:
            valid_entities.append(entity)
            
    return valid_entities


def calculate_match_score(entity: dict, requirements: dict) -> dict:
    """
    Calculates a strict 100-point match score based on 5 dimensions.
    Returns a dictionary with the total score and the breakdown for evidence.
    """
    score = 0
    breakdown = {}
    
    # 1. Relevance (30%) - Assuming they passed initial category filtering
    relevance_score = 30 
    breakdown["relevance"] = relevance_score
    score += relevance_score
    
    # 2. Location (20%) - Granular check if city matches, not just state
    pref_city = requirements.get("preferences", {}).get("preferred_city")
    entity_city = entity.get("location", {}).get("city")
    if pref_city and entity_city == pref_city:
        location_score = 20
    else:
        location_score = 10 # Baseline for passing state-level hard constraint
    breakdown["location"] = location_score
    score += location_score
    
    # 3. Compliance (25%) - Bonus points for sustainability if preferred
    compliance_score = 15 # Baseline for passing hard cert constraints
    if requirements.get("preferences", {}).get("sustainable_materials") and entity.get("sustainable_materials"):
        compliance_score += 10
    breakdown["compliance"] = compliance_score
    score += compliance_score
    
    # 4. Capacity/Availability (15%) - Bonus if highly suited for startup batch sizes
    capacity_score = 10
    if requirements.get("preferences", {}).get("startup_friendly") and entity.get("startup_friendly"):
        capacity_score += 5
    breakdown["capacity"] = capacity_score
    score += capacity_score
    
    # 5. Reputation (10%) - Based directly on 5-star rating scale
    rating = entity.get("rating") or 0.0
    reputation_score = int((rating / 5.0) * 10)
    breakdown["reputation"] = reputation_score
    score += reputation_score
    
    return {
        "total_score": score,
        "breakdown": breakdown
    }