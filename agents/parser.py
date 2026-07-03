from pydantic import BaseModel, Field
from typing import List, Optional
from llm_client import llm_call

# ---------------------------------------------------------
# Pydantic Schemas (Strict adherence to PS Section 4.1)
# ---------------------------------------------------------

class HardConstraints(BaseModel):
    locations: Optional[List[str]] = Field(
        default_factory=list, 
        description="Specific states or regions required (e.g., ['Karnataka', 'Tamil Nadu']). If none, leave empty."
    )
    certifications: Optional[List[str]] = Field(
        default_factory=list, 
        description="Required compliance certificates (e.g., 'food-grade', 'ISO9001')."
    )
    minimum_capacity: Optional[int] = Field(
        None, 
        description="Minimum quantity or capacity required."
    )
    maximum_delivery_days: Optional[int] = Field(
        None, 
        description="Maximum allowable delivery time in days."
    )

class Preferences(BaseModel):
    sustainable_materials: Optional[bool] = Field(
        None, 
        description="True if sustainable, biodegradable, or eco-friendly materials are preferred."
    )
    startup_friendly: Optional[bool] = Field(
        None, 
        description="True if the user is a startup, needs low MOQs, or specifically requests startup-friendly terms."
    )

class BusinessRequirement(BaseModel):
    objective: str = Field(
        ..., 
        description="A short summary of what the user is trying to achieve."
    )
    entity_type: str = Field(
        ..., 
        description="Must be one of: 'supplier', 'professional', 'opportunity'."
    )
    hard_constraints: HardConstraints
    preferences: Preferences
    requested_results: int = Field(
        3, 
        description="Number of matches requested by the user. Default to 3 if unspecified."
    )

# ---------------------------------------------------------
# Parsing Logic
# ---------------------------------------------------------

def parse_user_request(user_prompt: str) -> BusinessRequirement:
    """
    Forces the LLM to extract the user's natural language request into 
    the strict BusinessRequirement schema. Fails hard if JSON is invalid.
    """
    system_prompt = f"""
    You are an expert procurement and business analyst for the SUPROC platform. 
    Analyze the following user request and extract the structured requirements.
    
    CRITICAL INSTRUCTIONS:
    1. Distinguish carefully between HARD CONSTRAINTS (must-haves) and PREFERENCES (nice-to-haves).
    2. If a region is mentioned (e.g., 'South India'), map it to specific states 
       (e.g., Karnataka, Tamil Nadu, Kerala, Andhra Pradesh, Telangana) in the 'locations' list.
    3. Standardize certifications (e.g., map 'food safe' to 'food-grade').
    4. If no quantity or deadline is requested, leave those fields as null.
    
    User Request: "{user_prompt}"
    """
    
    # We enforce the schema parameter we built in Phase 1
    # Temperature is set low to prevent hallucinations during data extraction
    return llm_call(prompt=system_prompt, schema=BusinessRequirement, temperature=0.1)