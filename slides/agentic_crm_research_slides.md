# Slide 1: Agentic Orchestration Concept

**Agentic orchestration** = a cooperative loop of specialized autonomous agents operating over shared structured state, each:
- Observes current state & goals
- Decides next best contribution (plan, gather, validate, summarize)
- Emits structured deltas (not just text) enabling downstream reasoning & re-entry

Key Principles applied here:
- Non-linear control flow (dynamic routing via Orchestrator + validation feedback)
- Parallel evidence gathering (multi-aspect async search)
- Structured intermediate artifacts (typed Pydantic models) for deterministic scoring
- Self-check + escalation (Validator triggers targeted re-research)

Outcome: Reduced hallucination risk, clearer provenance, and adaptive iteration until convergence.

---
# Slide 2: System Architecture
```
┌──────────────┐        ┌─────────────┐       ┌──────────────┐
│  Orchestrator│◄──────►│   Validator │       │  Config /    │
│ (routing &   │        │ completeness│       │  Models      │
│ convergence) │        │  & semantic │       └──────────────┘
└──────┬───────┘        └──────┬──────┘                    ▲
       │                       │                           │
       ▼                       │                           │
┌──────────────┐   async / parallel   ┌──────────────┐     │
│  Research    │──────────────────────│  Search API  │     │
│  (multi-     │  (per CRM x aspect)  │  (Tavily)    │     │
│  aspect LLM  │                      └──────────────┘     │
│  extraction) │           ▲                               │
└──────┬───────┘           │ snippets                      │
       │                   │                               │
       ▼                   │                               │
┌──────────────┐           │                               │
│  Analysis    │───────────┘                               │
│ (scoring,    │  structured comparison + summary          │
│ recs, report)│                                           │
└──────────────┘                                           │
        │                                                  │
        ▼                                                  │
   JSON Report + Table + Logs (output/) ◄──────────────────┘
```
Data Flow Highlights:
- Shared `AgentState` holds CRMData objects, validation reports, convergence history
- Orchestrator uses state-derived heuristics (completeness, convergence window) to choose next agent
- Research builds evidence → structured `CRMData` (with confidence heuristic)
- Analysis converts structured data → normalized scores & recommendations
- Validator supplies completeness metrics and semantic anomaly signals

---
# Slide 3: Trade-offs, Assumptions, Future Work
**Trade-offs & Design Choices**
- Simplicity over exhaustive retrieval: single-pass per aspect (retry-enabled) vs full RAG pipeline
- Confidence heuristic (feature & integration coverage) instead of full citation-based verification
- JSON structured extraction with fallback fragment salvage to reduce parsing failures
- LangGraph for explicit state machine (transparent) rather than implicit event bus

**Assumptions**
- Tavily results are timely & representative for 2025 CRM landscape
- Core feature categories (automation/analytics/customization) sufficient for relative scoring
- Integration count is a reasonable proxy for ecosystem richness (capped normalization)
