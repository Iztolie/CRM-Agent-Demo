import asyncio
import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from langchain_core.messages import HumanMessage
from .config import config
from .workflow import create_agent_graph
from .formatters import format_comparison_table
from .models import AgentState


def _configure_logging(trace_id: str, level: str):
    """Configure console + file logging for a run.

    Creates output/crm_run_<trace_id>.log capturing DEBUG+ while console uses chosen level.
    Safe to call multiple times (idempotent per trace id)."""
    log_dir = Path("output")
    log_dir.mkdir(exist_ok=True)
    log_file = log_dir / f"crm_run_{trace_id}.log"

    root = logging.getLogger()
    # Avoid duplicating handlers if re-run inside same process
    # Remove existing file handlers targeting previous runs
    for h in list(root.handlers):
        if isinstance(h, logging.FileHandler) and "crm_run_" in getattr(h, 'baseFilename', ''):
            root.removeHandler(h)

    root.setLevel(logging.DEBUG)
    # Console handler
    if not any(isinstance(h, logging.StreamHandler) for h in root.handlers):
        ch = logging.StreamHandler()
        ch.setLevel(getattr(logging, level.upper(), logging.INFO))
        ch.setFormatter(logging.Formatter("[%(levelname)s] %(message)s"))
        root.addHandler(ch)
    # File handler (always debug for full detail)
    fh = logging.FileHandler(log_file, mode="a", encoding="utf-8")
    fh.setLevel(logging.DEBUG)
    fh.setFormatter(logging.Formatter("%(asctime)s | %(levelname)s | %(name)s | %(message)s"))
    root.addHandler(fh)
    logging.getLogger(__name__).info("Logging to %s (level=%s)", log_file, level.upper())

async def run(trace_id: str | None = None, log_level: str = "INFO"):
    trace_id = trace_id or datetime.now().strftime("%Y%m%d_%H%M%S")
    _configure_logging(trace_id, log_level)
    print("🚀 Starting Enhanced Multi-Agent CRM Research System")
    app = create_agent_graph()
    initial_state: AgentState = {
        "messages": [HumanMessage(content=f"Compare {', '.join(config.crms)} focusing on {', '.join(config.aspects)} for small B2B.")],
        "crm_data": {},
        "research_status": {},
        "validation_results": [],
        "final_comparison": {},
        "current_task": "",
        "iteration_count": 0,
        "error_log": [],
        "convergence_history": [],
        "trace_id": trace_id,
    }
    final_state = await app.ainvoke(initial_state)
    comparison = final_state.get("final_comparison", {})
    if comparison:
        print("\n📊 COMPARISON TABLE:")
        print(format_comparison_table(comparison))
        print("\n📌 SUMMARY:")
        print(comparison.get("summary", ""))
        out_dir = Path("output"); out_dir.mkdir(exist_ok=True)
        with open(out_dir / f"crm_report_{trace_id}.json", "w") as f:
            json.dump(comparison, f, indent=2)
    return final_state

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Multi-Agent CRM Research System")
    parser.add_argument("--crms", nargs="+")
    parser.add_argument("--aspects", nargs="+")
    parser.add_argument("--max-iterations", type=int)
    parser.add_argument("--model")
    parser.add_argument("--trace-id")
    parser.add_argument("--log-level", default="INFO", help="Console log level (DEBUG, INFO, WARNING, ERROR)")
    args = parser.parse_args()
    if args.crms: config.crms = args.crms
    if args.aspects: config.aspects = args.aspects
    if args.max_iterations: config.max_iterations = args.max_iterations
    if args.model: config.llm_model = args.model
    asyncio.run(run(args.trace_id, args.log_level))
