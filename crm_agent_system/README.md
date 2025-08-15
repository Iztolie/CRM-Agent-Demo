# CRM Agent System

Production-oriented multi-agent system for comparative CRM research across configurable vendors (default: HubSpot, Zoho, Salesforce). It orchestrates research, structured extraction, scoring, validation, and summarization using LangGraph and typed domain models.

---
## Contents
- Architecture Overview
- Components
- Data Models
- Agent Responsibilities
- Orchestration Workflow
- Configuration & Environment
- Execution (CLI)
- Scoring Logic
- Validation Logic
- Output Structure
- Dependencies

---
## Architecture Overview
The system separates concerns into distinct layers:
- Configuration: Tunable runtime parameters (CRMs, aspects, iteration limits, thresholds, retry/backoff behavior, model settings).
- Providers: Pluggable external search interface (currently Tavily) behind an abstraction for extensibility.
- Agents: Independent state mutators (Orchestrator, Research, Analysis, Validator) operating over a shared typed state object.
- Workflow: LangGraph state machine with conditional routing and convergence detection to avoid unnecessary iterations.
- Models: Pydantic-based domain schemas ensuring structured, validated CRM data for deterministic scoring and validation.
- Utilities: Cross-cutting helpers (retry/backoff) to harden I/O paths.

---
## Components
| Module | Purpose |
|--------|---------|
| `config.py` | Central config dataclass instanced at import time. |
| `models.py` | Domain schemas (`CRMData`, `PricingTier`, `CRMFeatures`, `Integration`) + `AgentState` definition. |
| `providers.py` | Search provider abstraction + Tavily implementation. |
| `agents/` | Agent implementations (orchestrator, research, analysis, validator). |
| `workflow.py` | LangGraph assembly, tool definitions, LLM instantiation. |
| `formatters.py` | Formatting utilities (e.g., Markdown comparison table). |
| `main.py` | CLI entrypoint for executing the full research workflow. |
| `utils.py` | Retry/backoff decorator supporting sync & async call paths. |

---
## Data Models
Core container: `CRMData`
```
CRMData(
  name: str,
  pricing_tiers: List[PricingTier],
  features: CRMFeatures,
  integrations: List[Integration],
  limitations: List[str],
  best_for: List[str],
  confidence_score: float
)
```
Supporting types:
- `PricingTier(name, monthly_price, annual_price, user_limit, notes)`
- `CRMFeatures(core_features, automation, analytics, customization)`
- `Integration(name, category, notes)`

The shared agent state (`AgentState` TypedDict) tracks:
- `messages`
- `crm_data`
- `research_status`
- `validation_results`
- `final_comparison`
- `current_task`
- `iteration_count`
- `error_log`
- `convergence_history`
- `trace_id`

---
## Agent Responsibilities
| Agent | Role |
|-------|------|
| OrchestratorAgent | Decides next phase (research, analyze, validate, complete) with convergence & iteration safeguards. |
| ResearchAgent | Parallel aspect-level search + LLM-driven JSON extraction into structured `CRMData`. |
| AnalysisAgent | Computes normalized scores & categorical recommendations; produces executive summary via LLM. |
| ValidatorAgent | Completeness scoring + semantic anomaly checks; may trigger selective re-research cycles. |

---
## Orchestration Workflow
1. Orchestrator selects phase based on presence/completeness of `crm_data`, validation results, and convergence.
2. Research gathers aspect snippets per CRM → structured extraction → updates `crm_data` & `research_status`.
3. Analysis calculates scores, recommendations, and summary once all CRMs are researched.
4. Validation scores completeness and checks semantic conditions (feature overlap, invalid pricing). If below threshold, orchestrator re-enters research for deficient CRMs.
5. Convergence window (configurable) short-circuits repetitive decisions, marking completion.

---
## Configuration & Environment
Defaults reside in `config.Config` (instantiated as `config`). Override selectively via CLI flags (see Execution) or environment variables for credentials. Key fields:
- `crms`, `aspects`, `max_iterations`, `validation_threshold`
- `convergence_window`, `max_retries`, `retry_delay`, `exponential_backoff`
- `llm_provider`, `llm_model`, `llm_temperature`

Environment variables (required for production run):
- `OPENAI_API_KEY`
- `TAVILY_API_KEY`

---
## Execution (CLI)
Example PowerShell invocation:
```powershell
$env:OPENAI_API_KEY = "<key>"
$env:TAVILY_API_KEY = "<tavily>"
python -m crm_agent_system.main --crms HubSpot Zoho Salesforce --aspects pricing features integrations limitations --max-iterations 8 --trace-id run001
```
CLI Flags:
- `--crms` (list) custom vendor set
- `--aspects` (list) research focus areas
- `--max-iterations` cap on orchestration cycles
- `--model` alternative LLM model name
- `--trace-id` explicit identifier for correlation

Outputs:
- Structured comparison object printed & persisted as `output/crm_report_<trace>.json` (created if absent).

---
## Scoring Logic
Per CRM:
- Pricing Score: Inverse of lowest monthly tier (bounded & normalized).
- Feature Score: Combined feature list size across defined buckets, capped.
- Integration Score: Count of integrations normalized with an upper bound.
Weighted aggregate:
```
overall = pricing*0.30 + features*0.40 + integrations*0.30
```
Recommendations derived by argmax over each dimension (overall, pricing, features, integrations).

---
## Validation Logic
Completeness scoring (25% each): pricing tiers, feature details, integrations, limitations. Semantic checks:
- High feature set overlap across CRMs (suspicious duplication)
- Negative pricing values
Reports feed re-research decisions if average completeness < threshold.

---
## Output Structure
`final_comparison` object contains:
```
{
  "summary": <llm_summary>,
  "scores": { <crm>: {pricing, features, integrations, overall}, ... },
  "recommendations": { best_overall, best_value, most_features, best_integrations },
  "detailed_data": { <crm>: CRMData as dict, ... },
  "timestamp": ISO8601
}
```

---
## Dependencies
Core libraries (see `requirements.txt` for versions):
- langgraph
- langchain-core / langchain-openai
- pydantic
- tavily
- python-dotenv

Auxiliary: `pytest` (if tests are added externally to this module).

---
This README documents the current operational state of the CRM Agent System and its runtime contract.
