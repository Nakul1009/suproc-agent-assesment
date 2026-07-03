import pytest

import time
import pytest

@pytest.fixture(autouse=True)
def rate_limit_cooldown():
    """
    Automatically pauses execution AFTER every test
    to prevent the LLM inference engine from going kaboom.
    """
    yield  # This lets the actual test execute first
    
    # Adjust this number based on how angry your API/Hardware is getting
    cooldown_seconds = 5
    print(f"\n[Cooldown] Sleeping for {cooldown_seconds}s to let the inference engine breathe...")
    time.sleep(cooldown_seconds)

def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """
    Hooks into Pytest's terminal summary to generate the exact 
    evaluation report required by the SUPROC Problem Statement.
    """
    passed_tests = terminalreporter.stats.get('passed', [])
    failed_tests = terminalreporter.stats.get('failed', [])
    
    total = len(passed_tests) + len(failed_tests)
    passed = len(passed_tests)
    failed = len(failed_tests)

    print("\n\n==================================================")
    print(" 📊 SUPROC EVALUATION REPORT")
    print("==================================================")
    print(f"• Total tests:    {total}")
    print(f"• Tests passed:   {passed}")
    print(f"• Tests failed:   {failed}")
    
    print("\n• Main failure cases:")
    if failed > 0:
        for report in failed_tests:
            # Extract just the function name (e.g., 'test_02_impossible_constraints')
            test_name = report.nodeid.split("::")[-1]
            print(f"  - {test_name}")
    else:
        print("  - None. All deterministic boundaries held successfully.")

    print("\n• Known limitations:")
    print("  1. LLM Context Window: Highly complex queries may push the limits of smaller models.")
    print("  2. Strict Filtering: The deterministic matcher will mercilessly reject records with null values in required fields, which could exclude viable but poorly documented opportunities.")
    print("  3. Latency: The self-correction loop requires multiple sequential LLM calls when a trap is hit, increasing response time.")
    print("==================================================\n")