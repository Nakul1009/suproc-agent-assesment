# Suproc_Assesment
A lightweight AI agent that understands a business request, searches a local Suproc-style dataset, verifies its recommendations and prepares the next action without performing it automatically.


-suproc_agent/
│
├── config.py                 # System configurations and environmental keys
├── main.py                   # CLI entrypoint and Human-In-The-Loop loop
├── llm_client.py             # Single isolated file for HF API / Ollama swap
│
├── data/
│   ├── manifest.json         # Metadata tying datasets together
│   ├── suppliers.json        # 30+ records (with incomplete/ambiguous edge cases)
│   ├── professionals.json    # 15+ records
│   └── opportunities.json    # 10+ records
│
├── agents/
│   ├── __init__.py
│   ├── orchestrator.py       # Manages execution plan, loops, and validation state
│   ├── parser.py             # Converts natural language to structured requirements
│   └── planner.py            # Generates deterministic step execution sequences
│
├── tools/
│   ├── __init__.py
│   ├── search.py             # search_entities, get_entity_details
│   ├── matcher.py            # filter_by_constraints, calculate_match_score
│   └── validator.py          # validate_recommendations (deterministic constraints check)
│
└── tests/
    ├── __init__.py
    ├── test_cases.json       # Structured test inputs/expected boundaries
    └── test_runner.py        # Automated test framework tracking pass/fail rates