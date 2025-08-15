tavily-python
# Multi-Agent CRM Research System (Refactored)

Production-grade multi-agent orchestration for comparative CRM research (HubSpot, Zoho, Salesforce by default) featuring:
- LangGraph routing & convergence logic (non-linear, convergence-aware)
- Async multi-aspect search (pricing / features / integrations / limitations)
- Structured JSON extraction → Pydantic models (typed CRMData)
- Evidence-based confidence heuristic & transparency logging
- Retry/backoff + validation loop (completeness + semantic checks)
- Integration harvesting, normalization & deduplication
- Offline demo mode (no API keys needed)

---
## 1. Repository Structure
```
crm_agent_system/
  config.py          # Central configuration (dataclass)
  models.py          # Pydantic domain models & AgentState definition
  utils.py           # Retry/backoff utility, logging hooks (extensible)
  providers.py       # Search provider abstraction (Tavily implementation)
  workflow.py        # LangGraph assembly & tool definitions
  formatters.py      # Markdown / tabular presentation helpers
  main.py            # CLI entry for production research run
  agents/
    __init__.py
    orchestrator.py  # OrchestratorAgent (phase / convergence logic)
    research.py      # ResearchAgent (async search + structured extraction)
    analysis.py      # AnalysisAgent (scoring + recommendations + summary)
    validator.py     # ValidatorAgent (completeness + semantic checks)
demo/
  mock_data.py       # Offline mock search corpus
  sim_extraction.py  # Converters to structured CRMData for demo
  demo_runner.py     # Lightweight demo CLI (no network / LLM)
requirements.txt
README.md
```

---
## 2. Core Concepts
| Layer | Responsibility | Notes |
|-------|----------------|-------|
| Config | Central runtime parameters (CRMs, aspects, retries, thresholds) | Override via CLI |
| Providers | Abstract external search sources | Currently Tavily; extendable |
| Agents | Discrete capabilities: research / analyze / validate / orchestrate | Each pure wrt `AgentState` mutation |
| Models | Strongly-typed Pydantic objects (`CRMData`, `PricingTier`, etc.) | Enables reliable scoring & validation |
| Workflow | LangGraph state machine with conditional routing | Prevents runaway loops; supports convergence detection |
| Demo | Deterministic offline showcase | Uses production scoring for parity |
| Logging | Structured DEBUG diagnostics per run | Per-run log file in `output/` |

---
## 3. Structured Data Models
`CRMData` captures normalized information:
```python
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
This enables quantitative scoring instead of free‑text heuristics.

---
## 4. Agent Behaviors (Refactored)
### OrchestratorAgent
Adaptive phase selection + convergence window (repeats of identical decisions → completion). Incorporates validation score threshold & max iteration guard.

### ResearchAgent
Asynchronously queries search tool per aspect; consolidates raw snippets; invokes LLM for **JSON-constrained extraction** into `CRMData` with fallback JSON fragment salvage.

Enhancements:
- Multi-aspect templated queries (year + context terms)
- Integration keyword harvesting (heuristic pass)
- Post-pass enrichment if sparse
- Normalization & case-insensitive dedupe of integrations
- Confidence components logged (pricing presence, feature coverage, integration density, limitations)

### AnalysisAgent
Calculates weighted scores (pricing 30%, features 40%, integrations 30%) and derives data-driven recommendations. Logs integration counts & applies disclaimer if any CRM confidence < threshold.

### ValidatorAgent
Two-stage validation:
1. Completeness scoring (pricing/features/integrations/limitations each 25%)
2. Semantic heuristics (feature overlap & pricing anomalies)
Marks deficient CRMs for re-research when average below threshold, enabling non-linear loop.

---
## 5. Search & Tooling Improvements
| Feature | Old | New |
|---------|-----|-----|
| Search | Direct Tavily call inline | Abstracted provider w/ retry loop + per-query timing |
| Extraction | Freeform strings | Structured JSON → Pydantic validation |
| Recommendations | Static text | Score-driven categories |
| Validation | Length + presence | Scored completeness + semantic checks + re-entry |
| State finalization | Streaming last event | Deterministic `ainvoke` result |
| Confidence | None | Evidence-based heuristic (features, integrations, pricing, limitations) |
| Integrations | Minimal | Keyword harvesting + enrichment + normalization |

---
## 6. Resilience & Observability
- Retry/backoff wrapper (sync + async) for external calls
- Convergence history prevents endless oscillation
- Per-run log file: `output/crm_run_<trace>.log`
- DEBUG logging includes: query latencies, raw truncated search results, harvested integration candidates, post-normalization integration sample, confidence components, integration counts (analysis)
- Trace ID propagation for correlation across agents

---
## 7. Configuration
Override defaults via CLI (`main.py`):
| Flag | Purpose |
|------|---------|
| `--crms` | Custom CRM list |
| `--aspects` | Aspects to research |
| `--max-iterations` | Iteration cap |
| `--model` | Alternate OpenAI model |
| `--trace-id` | Explicit trace grouping |

Environment (.env supported): `OPENAI_API_KEY`, `TAVILY_API_KEY`.

---
## 8. Offline Demo Mode
Run without API keys:
```powershell
python -m demo.demo_runner --fast --seed 42
```
Leverages production scoring logic while replacing network/LLM calls with deterministic mock extraction.

---
## 9. Running Production Workflow
```powershell
# PowerShell example
$env:OPENAI_API_KEY = "<your-openai-key>"
$env:TAVILY_API_KEY = "<your-tavily-key>"
python -m crm_agent_system.main --crms HubSpot Zoho Salesforce --aspects pricing features integrations limitations --trace-id run1
```
Artifacts:
- `output/crm_report_<trace>.json`
- `output/crm_run_<trace>.log` (full diagnostics)

---
## 10. Scoring & Confidence Formulas
```
overall = pricing*0.30 + features*0.40 + integrations*0.30
pricing: inverse of lowest monthly tier (bounded)
features: normalized feature bucket counts (capped)
integrations: normalized integration list size (capped)

confidence = 0.15
            + 0.15 * pricing_present
            + 0.35 * feature_category_coverage (0..1 of 4 buckets)
            + 0.25 * min(integration_count/15, 1)
            + 0.10 * limitations_present
(capped at 0.95)
```

---
## 11. Testing (Initial Plan)
Planned test coverage (next step):
| Test | Purpose |
|------|---------|
| Model instantiation | Ensure Pydantic schemas accept typical data |
| Scoring determinism | Given fixed CRMData → stable scores |
| Validation scoring | Completeness percentages correct |
| Routing logic | Orchestrator transitions under different states |
| Demo runner smoke | End-to-end offline path produces report |

---
## 12. Security & Secrets
No secrets checked into source. Use env vars or secret manager. DO NOT embed API keys in code. `.env` loading via `python-dotenv`.

---
## 13. Dependencies
See `requirements.txt`. Add dev-only extras (pytest, coverage) if tests introduced:
```
pytest
```
---
## 14. Slide Deck
Three-slide presentation (agentic concept, architecture diagram, trade-offs/future work): `slides/agentic_crm_research_slides.md`.

## 15. Summary
The system demonstrates a production-aligned multi-agent architecture with structured data models, configurable orchestration, confidence instrumentation, and an offline demo path. Remaining potential enhancements: source-level provenance, adaptive gap re-queries, richer pricing normalization, integration classification, automated tests.

## 16. GitHub Quick Start
Clone & install:
```bash
git clone https://github.com/Iztolie/CRM-Agent-Demo.git
cd CRM-Agent-Demo
python -m venv venv && source venv/bin/activate  # PowerShell: venv\Scripts\Activate.ps1
pip install -r requirements.txt
```
Run a live research (requires keys in environment or .env):
```bash
export OPENAI_API_KEY=...; export TAVILY_API_KEY=...
python -m crm_agent_system.main --trace-id quickstart --log-level INFO
```
Run offline demo (no keys):
```bash
python -m demo.demo_runner --fast
```

## 17. Contributing
1. Fork the repo & create a feature branch.
2. Add/adjust code with focused commits.
3. Include or update doc/README sections for new behavior.
4. (Optional) Add tests under `tests/` (not yet created) for new scoring/validation logic.
5. Open a PR describing motivation & changes; attach sample log and JSON output.

## 18. License
MIT (see `LICENSE`).
