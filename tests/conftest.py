import pytest

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