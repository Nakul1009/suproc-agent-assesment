from pydantic import BaseModel, Field
from typing import List
from llm_client import llm_call
from agents.parser import BusinessRequirement

# ---------------------------------------------------------
# Pydantic Schema (Strict adherence to PS Section 4.2)
# ---------------------------------------------------------

class ExecutionPlan(BaseModel):
    steps: List[str] = Field(
        ..., 
        description="A sequential list of actions the agent will take to fulfill the request."
    )

# ---------------------------------------------------------
# Planning Logic
# ---------------------------------------------------------

def generate_plan(requirement: BusinessRequirement) -> ExecutionPlan:
    """
    Takes the structured BusinessRequirement and asks the LLM to generate 
    a deterministic, step-by-step execution plan.
    """
    system_prompt = f"""
    You are the central orchestrator for the SUPROC platform.
    Based on the following parsed business requirement, generate a short, logical execution plan.
    
    Your plan MUST include steps for:
    1. Searching the dataset based on the entity type.
    2. Inspecting and filtering records against hard constraints.
    3. Ranking the remaining records based on preferences.
    4. Validating the recommendations through the deterministic QA system.
    5. Preparing the final response (and an outreach message if requested).
    
    Do not invent steps that are outside the scope of a local search and matching system.
    
    Parsed Requirement:
    Objective: {requirement.objective}
    Entity Type: {requirement.entity_type}
    Hard Constraints: {requirement.hard_constraints.model_dump_json()}
    """
    
    return llm_call(prompt=system_prompt, schema=ExecutionPlan, temperature=0.2)