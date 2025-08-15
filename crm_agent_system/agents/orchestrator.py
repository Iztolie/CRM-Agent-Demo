import logging
from typing import Dict, Any
from ..config import config
from ..models import AgentState

logger = logging.getLogger(__name__)

class OrchestratorAgent:
    """Enhanced orchestrator with convergence detection."""
    def __init__(self, llm):
        self.llm = llm

    def check_convergence(self, state: AgentState) -> bool:
        history = state.get("convergence_history", [])
        if len(history) < config.convergence_window:
            return False
        return len(set(history[-config.convergence_window:])) == 1

    def __call__(self, state: AgentState) -> AgentState:
        iteration = state.get("iteration_count", 0)
        state["iteration_count"] = iteration + 1

        logger.info(f"Orchestrator iteration {iteration}, trace_id={state.get('trace_id')}")

        if self.check_convergence(state):
            logger.info("System converged, completing")
            state["current_task"] = "complete"
            return state
        if iteration >= config.max_iterations:
            logger.warning("Max iterations reached")
            state["current_task"] = "complete"
            return state

        crm_data = state.get("crm_data", {})
        if not crm_data or len(crm_data) < len(config.crms):
            state["current_task"] = "research"
        elif not state.get("final_comparison"):
            state["current_task"] = "analyze"
        else:
            validation = state.get("validation_results", [])
            if validation:
                last = validation[-1]
                avg_score = sum(v.get("score", 0) for v in last.values()) / max(len(last), 1)
                if avg_score < config.validation_threshold:
                    state["current_task"] = "research"
                else:
                    state["current_task"] = "complete"
            else:
                state["current_task"] = "validate"

        history = state.get("convergence_history", [])
        history.append(state["current_task"])
        state["convergence_history"] = history[-config.convergence_window:]
        return state
