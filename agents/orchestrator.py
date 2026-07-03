import json
from pydantic import BaseModel, Field
from typing import List

from llm_client import llm_call
from agents.parser import parse_user_request, BusinessRequirement
from agents.planner import generate_plan, ExecutionPlan
from tools.search import get_all_suppliers, get_all_professionals, get_all_opportunities, get_entity_by_id
from tools.matcher import filter_by_constraints, calculate_match_score
from tools.validator import validate_recommendations

# ---------------------------------------------------------
# Pydantic Schemas for the Agent's Final Output
# ---------------------------------------------------------

class Recommendation(BaseModel):
    entity_id: str = Field(..., description="The ID of the recommended entity.")
    justification: str = Field(..., description="Evidence-backed reason why this entity is a good match.")

class AgentProposal(BaseModel):
    recommendations: List[Recommendation]
    missing_information: str = Field(..., description="Any constraints or preferences that couldn't be fully verified.")
    recommended_next_action: str = Field(..., description="What the user should do next (e.g., 'Approve outreach').")
    draft_message: str = Field(..., description="A draft outreach message to the selected entities.")

# ---------------------------------------------------------
# Core Orchestration Loop
# ---------------------------------------------------------

def execute_workflow(user_prompt: str) -> dict:
    """
    The central nervous system. 
    Parses -> Plans -> Searches -> Enters Validation Loop -> Returns HITL Output.
    """
    print("\n[Orchestrator] Starting workflow...")
    
    # 1. Parse
    requirement = parse_user_request(user_prompt)
    print(f"[Orchestrator] Parsed Requirement: {requirement.objective}")
    
    # 2. Plan
    plan = generate_plan(requirement)
    print("[Orchestrator] Execution Plan Generated.")
    for i, step in enumerate(plan.steps, 1):
        print(f"  Step {i}: {step}")

    # 3. Search & Retrieve (Fetch the correct dataset)
    if requirement.entity_type == "supplier":
        raw_pool = get_all_suppliers()
    elif requirement.entity_type == "professional":
        raw_pool = get_all_professionals()
    elif requirement.entity_type == "opportunity":
        raw_pool = get_all_opportunities()
    else:
        return {"status": "error", "message": f"Unknown entity type: {requirement.entity_type}"}

    # 4. Filter & Score (Deterministic tools prepare the grounded context)
    valid_pool = filter_by_constraints(raw_pool, requirement.hard_constraints.model_dump())
    
    scored_pool = []
    for entity in valid_pool:
        score_data = calculate_match_score(entity, requirement.model_dump())
        entity["match_score"] = score_data["total_score"]
        entity["score_breakdown"] = score_data["breakdown"]
        scored_pool.append(entity)
        
    # Sort by score descending to give the LLM the best options at the top
    scored_pool = sorted(scored_pool, key=lambda x: x.get("match_score", 0), reverse=True)

    # Compress the pool to avoid blowing up the LLM's context window
    context_pool = [
        {
            "id": e.get("id"), 
            "name": e.get("name") or e.get("title"), 
            "certifications": e.get("certifications"),
            "capacity": e.get("max_monthly_capacity"),
            "delivery_days": e.get("max_delivery_days"),
            "score": e.get("match_score")
        } for e in scored_pool
    ]

    # 5. The Self-Correction Loop (Max 3 Attempts)
    max_attempts = 3
    attempt = 1
    validation_history = ""
    
    while attempt <= max_attempts:
        print(f"\n[Orchestrator] Attempt {attempt} of {max_attempts} to generate valid recommendations...")
        
        # Build the dynamic prompt, including past failures if any
        system_prompt = f"""
        You are the SUPROC AI matching agent. Select the top {requirement.requested_results} 
        entities from the provided pool that best match the user's requirements.
        
        User Objective: {requirement.objective}
        Hard Constraints: {requirement.hard_constraints.model_dump_json()}
        Preferences: {requirement.preferences.model_dump_json()}
        
        Available Scored Pool:
        {json.dumps(context_pool, indent=2)}
        
        {validation_history}
        """
        
        # Call the LLM to make the selection and draft the response
        proposal: AgentProposal = llm_call(
            prompt=system_prompt, 
            schema=AgentProposal, 
            temperature=0.3
        )
        
        proposed_ids = [rec.entity_id for rec in proposal.recommendations]
        
        # Run the deterministic Validator against the LLM's choices
        val_result = validate_recommendations(
            recommended_ids=proposed_ids, 
            constraints=requirement.hard_constraints.model_dump(), 
            requested_count=requirement.requested_results
        )
        
        if val_result["is_valid"]:
            print("[Orchestrator] Validation passed. Preparing Human-in-the-Loop output.")
            return build_final_response(requirement, plan, proposal, val_result)
            
        else:
            print(f"[Orchestrator] Validation failed: \n{val_result['error_report']}")
            # Append the strict failure reason to the context window so the LLM learns
            validation_history += (
                f"\nWARNING: Your previous attempt failed validation for the following reasons:\n"
                f"{val_result['error_report']}\n"
                f"You MUST select different, valid IDs this time.\n"
            )
            attempt += 1

    # 6. Hard Kill-Switch Triggered
    print("\n[Orchestrator] FATAL: Maximum correction attempts reached. No valid matches found.")
    return {
        "status": "failed",
        "reason": "Agent could not find recommendations that pass strict deterministic validation.",
        "requirement": requirement.model_dump()
    }


def build_final_response(req: BusinessRequirement, plan: ExecutionPlan, proposal: AgentProposal, val_result: dict) -> dict:
    """
    Compiles the final payload required by the Problem Statement (Section 9).
    """
    final_recs = []
    for rec in proposal.recommendations:
        entity_data = get_entity_by_id(rec.entity_id)
        # Recalculate score breakdown for the final output report
        score_data = calculate_match_score(entity_data, req.model_dump()) 
        
        final_recs.append({
            "entity": entity_data.get("name") or entity_data.get("title"), # <--- Add the fallback here
            "id": rec.entity_id,
            "justification": rec.justification,
            "score_breakdown": score_data["breakdown"]
        })
        
    return {
        "status": "Awaiting user approval.",
        "interpreted_requirement": req.model_dump(),
        "execution_plan": plan.model_dump(),
        "recommendations": final_recs,
        "missing_information": proposal.missing_information,
        "recommended_next_action": proposal.recommended_next_action,
        "draft_message": proposal.draft_message,
        "validation_status": val_result["error_report"],
        "human_approval_required": True
    }