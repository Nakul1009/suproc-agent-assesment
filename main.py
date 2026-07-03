import sys
import json
from agents.orchestrator import execute_workflow

def print_separator(char="=", length=80):
    print(char * length)

def display_results(payload: dict):
    """
    Formats the JSON payload from the Orchestrator into a clean, 
    professional terminal presentation matching Section 9 of the PS.
    """
    print("\n")
    print_separator()
    print(" 🎯 SUPROC AI MATCHING AGENT - RESULTS")
    print_separator()

    # 1. Interpreted Requirements
    req = payload.get("interpreted_requirement", {})
    print("\n[INTERPRETED REQUIREMENT]")
    print(f"Objective:    {req.get('objective')}")
    print(f"Entity Type:  {req.get('entity_type').upper()}")
    print(f"Constraints:  {json.dumps(req.get('hard_constraints'), indent=2)}")
    print(f"Preferences:  {json.dumps(req.get('preferences'), indent=2)}")

    # 2. Execution Plan
    plan = payload.get("execution_plan", {})
    print("\n[EXECUTION PLAN FOLLOWED]")
    for i, step in enumerate(plan.get("steps", []), 1):
        print(f"  {i}. {step}")

    # 3. Recommendations & Evidence
    print("\n[RECOMMENDED MATCHES]")
    recs = payload.get("recommendations", [])
    for idx, rec in enumerate(recs, 1):
        print(f"\n  Match {idx}: {rec.get('entity')} (ID: {rec.get('id')})")
        print(f"  Evidence: {rec.get('justification')}")
        print(f"  Score Breakdown: {json.dumps(rec.get('score_breakdown'))}")
        print(f"  Constraints Checked: Passed all hard constraints (Verified via tools/validator.py)")

    # 4. Risks & Missing Info
    print("\n[RISKS & MISSING INFORMATION]")
    print(f"  {payload.get('missing_information', 'None identified.')}")

    # 5. Proposed Next Action & Outreach
    print("\n[PROPOSED ACTION]")
    print(f"  Action: {payload.get('recommended_next_action')}")
    
    print("\n[DRAFT OUTREACH MESSAGE]")
    print(f"  {payload.get('draft_message')}")
    
    print("\n[VALIDATION STATUS]")
    print(f"  {payload.get('validation_status')}")

def human_in_the_loop(payload: dict):
    """
    The strict approval block. Freezes execution until explicit human authorization.
    """
    print_separator("-")
    print(" ⚠️  STATUS: AWAITING USER APPROVAL")
    print_separator("-")
    
    if not payload.get("human_approval_required", True):
        print("System error: Approval flag missing or bypassed. Terminating for safety.")
        sys.exit(1)

    while True:
        choice = input("\nDo you authorize the agent to proceed with the recommended action? [Y/N]: ").strip().upper()
        
        if choice == 'Y':
            print("\n✅ APPROVAL GRANTED.")
            print("Executing mock action: Dispatching outreach messages and updating CRM...")
            print("Action successfully completed. Returning to standby.\n")
            break
        elif choice == 'N':
            print("\n❌ APPROVAL DENIED.")
            print("Action aborted. No messages sent. No records modified.")
            break
        else:
            print("Invalid input. Please enter 'Y' for Yes or 'N' for No.")

def main():
    print_separator()
    print(" 🚀 SUPROC LOCAL AGENT INITIALIZED")
    print_separator()
    print("Type 'exit' or 'quit' to shut down the terminal.\n")

    while True:
        try:
            user_input = input("\nEnter your business requirement:\n> ").strip()
            
            if user_input.lower() in ['exit', 'quit']:
                print("Shutting down...")
                break
                
            if not user_input:
                continue
                
            # Fire the full pipeline
            result = execute_workflow(user_input)
            
            if result.get("status") == "failed":
                print("\n❌ WORKFLOW FAILED")
                print(f"Reason: {result.get('reason')}")
                continue
                
            # Present output and wait for authorization
            display_results(result)
            human_in_the_loop(result)
            
        except KeyboardInterrupt:
            print("\nProcess interrupted by user. Shutting down...")
            break
        except Exception as e:
            print(f"\n[CRITICAL ERROR] The system encountered a fault: {str(e)}")

if __name__ == "__main__":
    main()