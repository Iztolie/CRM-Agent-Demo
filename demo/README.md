# CRM Agent System Demo (Offline Mock Mode)

This directory contains a self‑contained offline demonstration of the CRM Agent System. It simulates research and structured extraction without invoking external search providers or LLM APIs, while reusing the production scoring and recommendation logic for parity.

---
## Purpose
Provide a deterministic, API‑key‑free way to:
- Exercise the scoring and recommendation pipeline.
- Inspect the structured `CRMData` objects produced from mock inputs.
- Validate formatting of comparison outputs.

---
## Scope
Included:
- Mock search corpus and deterministic extraction.
- Parallel “research” simulation with optional artificial delay.
- Scoring + recommendations identical to production logic.

Excluded:
- Live web search (Tavily).
- LLM-driven JSON extraction.
- LLM-generated executive summary (replaced with timestamped stub).

---
## Files
| File | Role |
|------|------|
| `mock_data.py` | Static mock search snippets keyed by CRM and aspect. |
| `sim_extraction.py` | Deterministic conversion of mock blocks into `CRMData` instances. |
| `demo_runner.py` | CLI entrypoint orchestrating mock research, scoring, and output formatting. |

---
## Execution Flow
1. Collect pending CRMs from configuration (`config.crms`).
2. For each CRM, gather mock blocks from `MOCK_SEARCH_DATA` and build a `CRMData` object via `build_crm_data`.
3. Invoke `AnalysisAgent` (with `llm=None`) to compute scores and derive recommendations.
4. Assemble the `final_comparison` dictionary, including a stub summary and timestamp.
5. Print formatted comparison table and recommendations to stdout.

---
## Determinism & Reproducibility
- Randomness (if any future stochastic elements are introduced) is seeded via the `--seed` flag.
- Setting `--fast` removes the artificial per‑CRM delay for quicker iterations.

---
## Running the Demo
PowerShell example:
```powershell
python -m demo.demo_runner --fast --seed 42
```
Generic (any shell):
```bash
python -m demo.demo_runner --seed 123
```
Arguments:
- `--fast`  Skip simulated network delay.
- `--seed`  Integer seed for reproducibility (default 42).

No API keys or `.env` entries are required for the demo.

---
## Output Structure
The demo produces (stdout only) a `final_comparison` object internally shaped as:
```
{
  "summary": <demo_summary>,
  "scores": { <crm>: { pricing, features, integrations, overall }, ... },
  "recommendations": { best_overall, best_value, most_features, best_integrations },
  "detailed_data": { <crm>: CRMData as dict, ... },
  "timestamp": ISO8601
}
```
The recommendation fields are selected by argmax across each dimension.

---
## Relationship to Production System
Shared components:
- `CRMData` and related Pydantic models.
- Scoring formula and recommendation derivation from `AnalysisAgent`.
- Formatting utilities (`format_comparison_table`).

Demo substitutes network & LLM layers with deterministic mock data generation, preserving the downstream analytics surface.

---
## Limitations
- Does not reflect real‑time pricing, features, or integrations.
- Summary text is a fixed template with timestamp, not an LLM analysis.
- Semantic and completeness validation loops are not executed here.

---
## Dependencies
Uses only the subset of project dependencies required for models and analysis (refer to root `requirements.txt`). No external API connectivity is invoked.

---
This README documents the current, offline-only demo system state.
