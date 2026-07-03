import json
import sys
from pathlib import Path

# Ensure the root directory is in the path so we can import our modules
sys.path.append(str(Path(__file__).resolve().parent.parent))

from tools.search import get_all_suppliers, get_entity_by_id
from tools.matcher import filter_by_constraints, calculate_match_score
from tools.validator import validate_recommendations

def run_core_tests():
    print("\n=== PHASE 1 & 2: SYSTEMS TEST ===\n")
    
    # 1. Test Data Binding
    suppliers = get_all_suppliers()
    if not suppliers:
        print("❌ FAILED: Data not loaded. Check config.py and dataset paths.")
        return
    print(f"✅ Data Binding: Loaded {len(suppliers)} suppliers from memory.")

    # 2. Define Mock Requirements (Matching the PS Example)
    constraints = {
        "locations": ["Karnataka", "Tamil Nadu", "Kerala", "Andhra Pradesh", "Telangana"],
        "certifications": ["food-grade"],
        "minimum_capacity": 10000,
        "maximum_delivery_days": 30
    }
    preferences = {
        "sustainable_materials": True,
        "startup_friendly": True
    }
    
    # 3. Test Matcher Filters
    print("\n--- Running Matcher (Filter) ---")
    valid_suppliers = filter_by_constraints(suppliers, constraints)
    print(f"✅ Filtered down to {len(valid_suppliers)} valid suppliers.")
    for s in valid_suppliers:
        print(f"  -> {s['id']}: {s['name']} (Cap: {s['max_monthly_capacity']}, Del: {s['max_delivery_days']})")

    # 4. Test Matcher Scoring
    print("\n--- Running Matcher (Scoring) ---")
    reqs_for_scoring = {"preferences": preferences}
    for s in valid_suppliers[:3]: # Just show top 3 for brevity
        score_data = calculate_match_score(s, reqs_for_scoring)
        print(f"  -> {s['id']} | Total Score: {score_data['total_score']} | Breakdown: {score_data['breakdown']}")

    # 5. Test Validator Traps
    print("\n--- Running Validator Traps ---")
    # We will intentionally feed it bad IDs to ensure the automated QA catches them.
    # SUP-014: Missing food-grade
    # SUP-022: Delivery is 40 days (Max is 30)
    # SUP-025: Suspended/Inactive account
    # SUP-999: Hallucination (Doesn't exist)
    bad_ids = ["SUP-014", "SUP-022", "SUP-025", "SUP-999"]
    
    validation_result = validate_recommendations(bad_ids, constraints, requested_count=3)
    
    if not validation_result['is_valid']:
        print("✅ Validator successfully caught the traps!")
        print(f"Validator Error Report:\n{validation_result['error_report']}")
    else:
        print("❌ FAILED: Validator let bad data through.")

if __name__ == "__main__":
    run_core_tests()