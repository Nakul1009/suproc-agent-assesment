import sys
import json
from pathlib import Path

# Ensure the root directory is in the path
sys.path.append(str(Path(__file__).resolve().parent.parent))

from agents.orchestrator import execute_workflow

def run_full_pipeline_test():
    print("\n=== PHASE 3 & 4: FULL ORCHESTRATION TEST ===\n")
    
    # This is the exact test prompt provided in Section 3 of the Assignment
    user_prompt = (
        "We are a sustainable food-packaging startup based in Bengaluru. "
        "We need three suppliers from South India that can provide food-grade biodegradable containers, "
        "support an initial order of 10,000 units and deliver within 30 days. "
        "Explain why each supplier is suitable, identify any missing information and prepare an outreach message."
    )
    
    print(f"USER PROMPT:\n\"{user_prompt}\"\n")
    print("-" * 50)
    
    try:
        # Fire the workflow
        result = execute_workflow(user_prompt)
        
        print("\n" + "=" * 50)
        print("🎉 WORKFLOW COMPLETE. FINAL PAYLOAD:")
        print("=" * 50)
        
        # Pretty print the final JSON payload
        print(json.dumps(result, indent=2))
        
    except Exception as e:
        print(f"\n❌ PIPELINE FAILED: {str(e)}")

if __name__ == "__main__":
    run_full_pipeline_test()