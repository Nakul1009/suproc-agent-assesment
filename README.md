# 🤖 SUPROC AI Matching Agent

> A fully local, privacy-first AI agent that interprets natural-language business requirements, searches a curated procurement dataset, scores and ranks candidates, self-corrects invalid recommendations, and gates every action behind a **human-in-the-loop approval step** — all without a single cloud API call.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Model Used](#-model-used)
- [Architecture & Design](#-architecture--design)
- [Project Structure](#-project-structure)
- [Data Layer](#-data-layer)
- [Agent Pipeline](#-agent-pipeline-step-by-step)
- [Scoring System](#-scoring-system)
- [Validation & Self-Correction Loop](#-validation--self-correction-loop)
- [Human-in-the-Loop (HITL)](#-human-in-the-loop-hitl)
- [Setup & Installation](#-setup--installation)
- [Running the Agent](#-running-the-agent)
- [Running the Tests](#-running-the-tests)
- [Test Case Catalogue](#-test-case-catalogue)
- [Known Limitations](#-known-limitations)

---

## 🧭 Overview

The **SUPROC AI Matching Agent** is a procurement intelligence system built for the SUPROC platform assessment. Given a plain-English business requirement, the agent:

1. **Parses** the requirement into a strict, structured format using an LLM.
2. **Plans** a deterministic execution strategy.
3. **Searches** a local JSON dataset of suppliers, professionals, and opportunities.
4. **Filters** candidates against hard constraints (location, certifications, capacity, delivery).
5. **Scores** passing candidates across five dimensions to rank them.
6. **Selects** the best matches using the LLM, grounded in pre-scored data.
7. **Validates** every selection deterministically — the LLM cannot bypass guardrails.
8. **Self-corrects** up to 3 times if validation fails, feeding failure reasons back to the LLM.
9. **Presents** results and waits for explicit human approval before taking any action.

The system is designed with a strict **"LLM suggests, code decides"** philosophy — the model is never trusted to enforce constraints on its own.

---

## 🧠 Model Used

| Property | Value |
|---|---|
| **Model** | `qwen3:4b` |
| **Provider** | [Ollama](https://ollama.com/) (fully local) |
| **API Compatibility** | OpenAI-compatible endpoint (`/v1`) |
| **Base URL** | `http://localhost:11434/v1` |
| **Temperature (Parsing)** | `0.1` — near-deterministic, minimises hallucinations |
| **Temperature (Planning)** | `0.2` — slightly more creative for step generation |
| **Temperature (Selection)** | `0.3` — enough flexibility to reason over scored candidates |
| **Max Retries per LLM call** | `3` (with sleep on connectivity errors) |

**Why Qwen3 4B?**
Qwen3 4B is a compact, instruction-following model that runs comfortably on consumer hardware with no GPU required. It handles structured JSON output reliably at low temperature, making it well-suited for schema-enforced pipelines. The LLM client strips any markdown code-fence wrappers before Pydantic validation, making the output chain robust against common small-model quirks.

---

## 🏗 Architecture & Design

```
┌─────────────────────────────────────────────────────────────────┐
│                         main.py  (CLI)                          │
│  • Accepts user input  • Renders results  • HITL approval gate  │
└────────────────────────────┬────────────────────────────────────┘
                             │  execute_workflow(prompt)
                             ▼
┌─────────────────────────────────────────────────────────────────┐
│                    agents/orchestrator.py                        │
│  1. parse_user_request()  →  BusinessRequirement (Pydantic)     │
│  2. generate_plan()       →  ExecutionPlan (Pydantic)           │
│  3. tools/search.py       →  Raw entity pool                    │
│  4. tools/matcher.py      →  Filtered & scored pool             │
│  5. llm_call(AgentProposal) →  LLM selects top N               │
│  6. tools/validator.py    →  Deterministic pass/fail gate       │
│  7. Self-correction loop  →  Up to 3 attempts                   │
│  8. build_final_response() → Structured payload for HITL        │
└─────────────────────────────────────────────────────────────────┘
         │                    │                    │
         ▼                    ▼                    ▼
  agents/parser.py    agents/planner.py    tools/ (pure Python)
  (LLM → schema)      (LLM → steps)     search / matcher / validator
```

**Core Design Principles:**

- **Deterministic Guardrails First** — Filtering and validation are pure Python; the LLM has no say in whether constraints pass.
- **Schema Enforcement** — Every LLM response is validated through a Pydantic model. If the model drifts, it is retried automatically.
- **Context Compression** — Only a compact summary of each entity is sent to the LLM to avoid context window overflow on small models.
- **Grounded Prompting** — The LLM receives pre-scored, pre-filtered data, so it reasons over a curated subset, not the raw dataset.
- **Failure Transparency** — Every validation failure is appended to the LLM's context verbatim, so the model sees exactly what it did wrong on its next attempt.

---

## 📂 Project Structure

```
suproc-agent-assesment/
│
├── config.py                 # Ollama base URL, model name, data paths
├── main.py                   # CLI entrypoint + Human-in-the-Loop approval gate
├── llm_client.py             # OpenAI-compatible client pointed at local Ollama
├── requirements.txt          # Pinned Python dependencies
├── .env                      # (Optional) Environment overrides
│
├── agents/
│   ├── orchestrator.py       # Central workflow controller (parse→plan→search→validate→HITL)
│   ├── parser.py             # NL → structured BusinessRequirement via LLM + Pydantic
│   └── planner.py            # Generates a step-by-step ExecutionPlan via LLM
│
├── tools/
│   ├── search.py             # In-memory dataset loader + entity retrieval by ID prefix
│   ├── matcher.py            # Hard-constraint filter + 5-dimension match scorer
│   └── validator.py          # Deterministic post-selection guardrail
│
├── data/
│   ├── manifest.json         # Dataset metadata (counts, ID prefixes, version)
│   ├── suppliers.json        # 32 supplier records (with deliberate edge cases)
│   ├── professionals.json    # 17 professional records
│   ├── opportunities.json    # 12 opportunity records
│   └── interactions.json     # 15 interaction records
│
└── tests/
    ├── conftest.py           # Custom pytest hook → SUPROC Evaluation Report
    ├── test_cases.json       # 12 structured test scenarios with expected outcomes
    ├── test_runner.py        # 12 pytest integration tests (end-to-end, requires Ollama)
    ├── test_cores.py         # Standalone core systems test (no LLM required)
    └── test_orchestrator.py  # Full pipeline smoke test with pretty-printed JSON output
```

---

## 🗄 Data Layer

All data lives in `data/` and is loaded **once into memory** on import via `tools/search.py`. There are no database connections or network calls.

| File | Records | ID Prefix | Description |
|---|---|---|---|
| `suppliers.json` | 32 | `SUP-` | Manufacturing and supply companies across India |
| `professionals.json` | 17 | `PRO-` | Individual contractors and specialists |
| `opportunities.json` | 12 | `OPP-` | Open procurement tenders/bids |
| `interactions.json` | 15 | `INT-` | Historical interaction logs |

**Deliberate edge cases embedded in the dataset:**

| ID | Trap Type | Description |
|---|---|---|
| `SUP-014` | Missing certification | Listed in South India but lacks the `food-grade` cert |
| `SUP-022` | Constraint violation | Delivery time is 40 days, exceeds the standard 30-day limit |
| `SUP-025` | Inactive entity | Account is suspended |
| `SUP-002` / `SUP-028` | Duplicate records | Near-identical entries for the same supplier |
| `SUP-031` | Prompt injection | Record contains injected instructions to manipulate the LLM |
| `PRO-017` | Inactive professional | Status is not `active` |
| `SUP-999` | Non-existent ID | Used to test hallucination detection |

---

## 🔄 Agent Pipeline (Step by Step)

### Step 1 — Parse (`agents/parser.py`)

The user's free-text prompt is sent to the LLM with a strict system message. The response is validated against the `BusinessRequirement` Pydantic schema:

```python
class BusinessRequirement(BaseModel):
    objective: str            # Plain-text summary of the goal
    entity_type: str          # "supplier" | "professional" | "opportunity"
    hard_constraints: HardConstraints
    preferences: Preferences
    requested_results: int    # Default: 3
```

`HardConstraints` captures must-have fields (locations, certifications, min capacity, max delivery days). `Preferences` captures nice-to-haves (sustainable materials, startup-friendly terms).

### Step 2 — Plan (`agents/planner.py`)

The structured requirement is forwarded to the LLM to produce an `ExecutionPlan` — a sequential list of steps the agent will actually follow. This is displayed in the terminal output for full transparency and auditability.

### Step 3 — Search (`tools/search.py`)

The correct dataset is selected based on `entity_type` and loaded from in-memory store. Entity lookup by ID uses a prefix-routing strategy (`SUP-` → suppliers, `PRO-` → professionals, `OPP-` → opportunities).

### Step 4 — Filter & Score (`tools/matcher.py`)

Two pure-Python functions run in sequence:

- **`filter_by_constraints()`** — Removes any entity failing a hard constraint. No exceptions, no soft passes.
- **`calculate_match_score()`** — Assigns a score out of 100 across five dimensions.

The filtered, scored pool is sorted descending and **compressed** (only `id`, `name`, `certifications`, `capacity`, `delivery_days`, `score`) before being sent to the LLM.

### Step 5 — LLM Selection

The LLM is given the compressed, pre-scored pool and asked to pick the best N entities, provide evidence-backed justifications, note missing information, and draft an outreach message. Response validated against `AgentProposal`.

### Step 6 — Validate (`tools/validator.py`)

The LLM's chosen IDs are run through a deterministic validator (5 checks — see [Validation section](#-validation--self-correction-loop)).

### Step 7 — Self-Correction Loop

If validation fails, the exact error report is injected back into the LLM's context and the selection is retried (up to **3 attempts**). On total failure, returns `status: "failed"`.

### Step 8 — Human-in-the-Loop

The final payload is presented in a formatted terminal report. The agent then **freezes** and awaits explicit `Y/N` approval.

---

## 📊 Scoring System

Each entity is scored out of **100 points** across five weighted dimensions:

| Dimension | Max Points | Logic |
|---|---|---|
| **Relevance** | 30 | Baseline for passing the category filter — always 30 |
| **Location** | 20 | 20 pts if city matches preference; 10 pts baseline for state-level pass |
| **Compliance** | 25 | 15 pts baseline; +10 bonus if `sustainable_materials` preferred AND entity qualifies |
| **Capacity** | 15 | 10 pts baseline; +5 bonus if `startup_friendly` preferred AND entity qualifies |
| **Reputation** | 10 | `int((rating / 5.0) * 10)` — scaled from entity's 5-star rating field |

> Entities that fail any hard constraint are **excluded before scoring** and never reach the LLM.

---

## 🛡 Validation & Self-Correction Loop

```
LLM proposes entity IDs
           │
           ▼
┌──────────────────────────────────┐
│       tools/validator.py         │
│  1. Count check                  │
│  2. Duplicate check              │
│  3. Existence check (no halluc.) │
│  4. Active / open status check   │
│  5. Cert & delivery re-verify    │
└──────────┬───────────────────────┘
           │
     ┌─────┴──────┐
   PASS          FAIL
     │              │
     ▼              ▼
Final response   Error appended verbatim
                 to LLM context → retry
                 (max 3 attempts)
                      │
                    All fail
                      │
                      ▼
               status: "failed"
```

---

## 👤 Human-in-the-Loop (HITL)

Every successful workflow ends with a hard stop in `main.py`:

```
⚠️  STATUS: AWAITING USER APPROVAL
------------------------------------------------------------
Do you authorize the agent to proceed with the recommended action? [Y/N]:
```

- **Y** → Executes the mock action (simulates CRM update + outreach dispatch).
- **N** → Aborts cleanly. No messages sent, no records modified.
- **Any other input** → Loops until a valid response is given.

The `human_approval_required: true` flag is always present in the output payload. If it is missing or falsy, the system calls `sys.exit(1)` immediately as a safety measure.

---

## ⚙️ Setup & Installation

### Prerequisites

| Requirement | Version | Notes |
|---|---|---|
| Python | ≥ 3.11 | Required for modern type hints (`list[dict]`, `str \| T`) |
| [Ollama](https://ollama.com/download) | Latest | Must be running in the background |
| `qwen3:4b` model | — | Pulled via Ollama CLI (see below) |

### 1. Clone the Repository

```bash
git clone <your-repo-url>
cd suproc-agent-assesment
```

### 2. Create and Activate a Virtual Environment

```bash
# Windows
python -m venv env
env\Scripts\activate

# macOS / Linux
python -m venv env
source env/bin/activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Start Ollama and Pull the Model

```bash
# Pull the model (one-time, ~2.5 GB download)
ollama pull qwen3:4b

# Verify it is available
ollama list
```

Ollama starts automatically on most systems. If not, run `ollama serve` in a separate terminal.

### 5. Verify Configuration

Open `config.py` and confirm the settings match your environment:

```python
OLLAMA_BASE_URL = "http://localhost:11434/v1"   # Default Ollama port
DEFAULT_MODEL   = "qwen3:4b"
```

No `.env` file is required for the default configuration.

---

## 🚀 Running the Agent

```bash
python main.py
```

**Example session:**

```
════════════════════════════════════════════════════════════════
 🚀 SUPROC LOCAL AGENT INITIALIZED
════════════════════════════════════════════════════════════════
Type 'exit' or 'quit' to shut down the terminal.

Enter your business requirement:
> We are a sustainable food-packaging startup in Bengaluru. We need three
  suppliers from South India with food-grade biodegradable containers,
  minimum 10,000 units, delivery within 30 days.

[Orchestrator] Starting workflow...
[Orchestrator] Parsed Requirement: ...
[Orchestrator] Execution Plan Generated.
  Step 1: Search suppliers dataset...
  ...
[Orchestrator] Attempt 1 of 3 to generate valid recommendations...
[Orchestrator] Validation passed. Preparing Human-in-the-Loop output.

════════════════════════════════════════════════════════════════
 🎯 SUPROC AI MATCHING AGENT - RESULTS
════════════════════════════════════════════════════════════════
[INTERPRETED REQUIREMENT]
...
[RECOMMENDED MATCHES]
...
⚠️  STATUS: AWAITING USER APPROVAL
Do you authorize the agent to proceed with the recommended action? [Y/N]:
```

---

## 🧪 Running the Tests

Runs all 12 scenario-based integration tests with a custom evaluation report at the end.

```bash
# Standard run
pytest tests/test_runner.py -v

```

**Terminal summary after all tests:**

```
==================================================
 📊 SUPROC EVALUATION REPORT
==================================================
• Total tests:    12
• Tests passed:   12
• Tests failed:   0

• Main failure cases:
  - None. All deterministic boundaries held successfully.

• Known limitations:
  1. LLM Context Window: Highly complex queries may push the limits of smaller models.
  2. Strict Filtering: The deterministic matcher will reject records with null values.
  3. Latency: The self-correction loop requires multiple sequential LLM calls.
==================================================
```

> **Timing note:** Tests that invoke the LLM can take 30–120 seconds each on CPU-only hardware. The full suite may run for 15–20 minutes. Tests accept `schema_error` as a valid graceful outcome alongside `"Awaiting user approval."` or `"failed"`.

---

## 📋 Test Case Catalogue

| ID | Scenario | What is Being Validated |
|---|---|---|
| `TC-01` | Normal request with valid matches | Happy path — returns ≥ 3 results including `SUP-001`, `SUP-002`; excludes `SUP-006`, `SUP-015` |
| `TC-02` | Impossible constraints (no matching records) | Returns 0 results; workflow returns `failed` gracefully |
| `TC-03` | Self-contradicting requirements (rate < 1000 AND > 2500 INR/hr) | Returns 0 results; no crash or hallucination |
| `TC-04` | Vague / incomplete request ("Find me a supplier") | Agent handles missing info and still returns ≥ 1 result |
| `TC-05` | Dataset records with missing fields (`SUP-009`) | Matcher silently drops incomplete records |
| `TC-06` | Ambiguous location or category | Agent makes a reasonable interpretation and returns ≥ 1 result |
| `TC-07` | Duplicate records in dataset (`SUP-002` / `SUP-028`) | Returns ≤ 1 unique match; duplicate suppressed |
| `TC-08` | Non-existent and inactive IDs requested explicitly | Validator rejects `SUP-999` (hallucination) and `SUP-031` (inactive) |
| `TC-09` | LLM tries to include `SUP-004` (invalid cert) | Self-correction loop catches it; `SUP-004` excluded from final output |
| `TC-10` | Prompt injection embedded in a dataset record | Workflow completes without executing injected instructions |
| `TC-11` | Request for autonomous action without approval | `human_approval_required: true` is always enforced |
| `TC-12` | User explicitly asks agent to bypass validation | Guardrails hold; validation runs regardless |

---

## ⚠️ Known Limitations

1. **Small Model Schema Drift** — `qwen3:4b` occasionally drops required JSON keys, triggering a Pydantic `ValidationError`. `llm_client.py` retries up to 3 times. The test suite treats `schema_error` as a graceful partial failure, not a test failure.

2. **Prompt Injection Resilience** — Small 4B parameter models are more susceptible to injected instructions embedded in dataset records (e.g., `SUP-031`). The deterministic validator catches most cases post-selection, but the model may still reason incorrectly during selection.

3. **Latency on Self-Correction** — Each retry requires an additional full LLM inference pass. With 3 attempts and local CPU inference, worst-case latency can reach several minutes.

4. **Strict Null Handling** — The matcher drops any entity with `null` values in required constraint fields (e.g., missing `max_monthly_capacity`). This is intentional but may exclude otherwise viable, under-documented records.

5. **No Semantic Search** — The current implementation uses exact-match filtering and rule-based scoring. Embedding/vector-based semantic search is not implemented; matching quality depends entirely on the exact field values in the JSON dataset.

---

## 📄 License

This project was created for the SUPROC platform technical assessment. All data in `data/` is entirely synthetic and was generated for evaluation purposes only. It does not represent any real suppliers, professionals, or business opportunities.
'
