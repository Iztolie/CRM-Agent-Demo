import logging
from langgraph.graph import StateGraph, END
from langchain_core.tools import tool
import json
from .models import AgentState
from .agents import OrchestratorAgent, ResearchAgent, AnalysisAgent, ValidatorAgent
from .providers import get_search_provider
from .config import config
from .utils import retry_with_backoff

logger = logging.getLogger(__name__)

# LLM factory kept local to avoid circular imports
from langchain_openai import ChatOpenAI
from pydantic import SecretStr
import os
import time
import inspect

def get_llm():
    """Instantiate an OpenAI Chat model using OPENAI_API_KEY only."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise ValueError("OPENAI_API_KEY not set")
    safe_prefix = api_key[:5] + ("..." if len(api_key) > 5 else "")
    logger.debug(f"Using OpenAI key prefix: {safe_prefix}")
    return ChatOpenAI(
        model=config.llm_model,
        temperature=config.llm_temperature,
        api_key=SecretStr(api_key),
    )

search_provider = get_search_provider()
llm = get_llm()

@tool
async def search_crm_info(crm_name: str, aspect: str) -> str:
    """Async search for a CRM aspect; returns JSON list of result objects.

    Uses the configured provider (Tavily) to fetch up to `config.max_search_results`.
    Performs manual retry with exponential backoff. Returns JSON-encoded list or
    an error object.
    """
    # Build an aspect-specific query using configurable template
    template = config.aspect_query_templates.get(aspect, aspect)
    query = f"{crm_name} CRM {template} small business B2B"
    results = []
    for attempt in range(1, 1 + config.max_retries):
        try:
            raw_call = search_provider.search(query)
            raw = await raw_call if inspect.isawaitable(raw_call) else raw_call
            results = raw or []
            logger.debug(
                "Search success: crm=%s aspect=%s attempt=%d results=%d", crm_name, aspect, attempt, len(results)
            )
            break
        except Exception as e:  # pragma: no cover
            if attempt == config.max_retries:
                logger.error("Search failed after retries: %s %s: %s", crm_name, aspect, e)
                return json.dumps({"error": str(e)})
            backoff = config.retry_delay * (2 ** (attempt - 1) if config.exponential_backoff else 1)
            logger.warning(
                "Search attempt %d failed (%s) crm=%s aspect=%s; retrying in %.2fs", attempt, e, crm_name, aspect, backoff
            )
            time.sleep(backoff)
    # Trim to configured max
    return json.dumps(results[: config.max_search_results])

@tool
def validate_data_completeness(crm_data: dict) -> dict:
    """Evaluate completeness of collected CRMData objects.

    For each CRM entry present, awards 25% for each of pricing tiers, feature
    details, integrations, and limitations. Returns a mapping of CRM name to a
    dict: { score (0..1), issues (list[str]), complete (bool) }.
    """
    report = {}
    for name, data in crm_data.items():
        score = 0
        max_score = 100
        issues = []
        if getattr(data, "pricing_tiers", None):
            score += 25
        else:
            issues.append("Missing pricing information")
        features = getattr(data, "features", None)
        if features and features.core_features:
            score += 25
        else:
            issues.append("Missing feature details")
        if getattr(data, "integrations", None):
            score += 25
        else:
            issues.append("Missing integration data")
        if getattr(data, "limitations", None):
            score += 25
        else:
            issues.append("Missing limitations")
        report[name] = {"score": score / max_score, "issues": issues, "complete": score == max_score}
    return report


def create_agent_graph():
    orchestrator = OrchestratorAgent(llm)
    research_agent = ResearchAgent(llm, search_crm_info)
    analysis_agent = AnalysisAgent(llm)
    validator = ValidatorAgent(llm, validate_data_completeness)

    workflow = StateGraph(AgentState)
    workflow.add_node("orchestrator", orchestrator)
    workflow.add_node("research", research_agent)
    workflow.add_node("analyze", analysis_agent)
    workflow.add_node("validate", validator)

    def route_next(state: AgentState) -> str:
        task = state.get("current_task", "orchestrator")
        if task == "complete":
            return END
        if task == "research":
            return "research"
        if task == "analyze":
            return "analyze"
        if task == "validate":
            return "validate"
        return "orchestrator"

    workflow.add_conditional_edges("orchestrator", route_next)
    workflow.add_edge("research", "orchestrator")
    workflow.add_edge("analyze", "validate")
    workflow.add_edge("validate", "orchestrator")
    workflow.set_entry_point("orchestrator")
    return workflow.compile()
