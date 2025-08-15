"""CLI demo runner using mock data and production scoring utilities."""
import asyncio
import argparse
import random
from datetime import datetime
from typing import Dict

from crm_agent_system.models import CRMData
from crm_agent_system.agents.analysis import AnalysisAgent
from crm_agent_system.formatters import format_comparison_table
from crm_agent_system.config import config

from .mock_data import MOCK_SEARCH_DATA
from .sim_extraction import build_crm_data

class DemoOrchestrator:
    def __init__(self, fast: bool = False):
        self.state: Dict = {
            "crm_data": {},
            "validation_results": [],
            "iteration": 0,
        }
        self.fast = fast

    async def simulate_research(self, crm: str) -> CRMData:
        delay = 0 if self.fast else 0.4
        await asyncio.sleep(delay)
        blocks = MOCK_SEARCH_DATA.get(crm, {})
        return build_crm_data(crm, blocks)

    async def run(self):
        # Phase 1 research (dynamic pending list)
        pending = [c for c in config.crms if c not in self.state["crm_data"]]
        results = await asyncio.gather(*[self.simulate_research(c) for c in pending])
        for crm, data in zip(pending, results):
            self.state["crm_data"][crm] = data
        # Analysis using production scoring
        analysis = AnalysisAgent(llm=None)  # llm not needed for scoring logic reuse
        scores = analysis.calculate_scores(self.state["crm_data"])  # type: ignore
        # generate_recommendations only requires scores; prior extra arg caused mismatch
        recommendations = analysis.generate_recommendations(scores)  # type: ignore
        summary = f"Demo summary generated {datetime.now().isoformat()} (offline mode)"
        self.state["final_comparison"] = {
            "summary": summary,
            "scores": scores,
            "recommendations": recommendations,
            "detailed_data": {k: v.dict() for k, v in self.state["crm_data"].items()},
            "timestamp": datetime.now().isoformat(),
        }
        return self.state


def main():
    parser = argparse.ArgumentParser(description="Offline CRM multi-agent demo")
    parser.add_argument("--fast", action="store_true", help="Skip artificial delays")
    parser.add_argument("--seed", type=int, default=42, help="Random seed for reproducibility")
    args = parser.parse_args()

    random.seed(args.seed)

    print("""
    ╔══════════════════════════════════════════╗
    ║   Multi-Agent CRM Research System Demo   ║
    ║   (Offline Mock Mode)                    ║
    ╚══════════════════════════════════════════╝
    """)

    orchestrator = DemoOrchestrator(fast=args.fast)
    state = asyncio.run(orchestrator.run())
    comparison = state.get("final_comparison", {})
    if comparison:
        print("\n📊 COMPARISON TABLE:")
        print(format_comparison_table(comparison))
        print("\n💡 RECOMMENDATIONS:")
        for k, v in comparison.get("recommendations", {}).items():
            print(f"  • {k.replace('_', ' ').title()}: {v}")
    print("\n✅ Demo complete.")

if __name__ == "__main__":
    main()
