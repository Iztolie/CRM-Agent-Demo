import logging
from typing import List, Dict
from ..models import AgentState, CRMData
from ..config import config

logger = logging.getLogger(__name__)

class ValidatorAgent:
    def __init__(self, llm, validation_tool):
        self.llm = llm
        self.validate = validation_tool

    async def semantic_validation(self, crm_data: Dict[str, CRMData]) -> List[str]:
        issues: List[str] = []
        feature_sets: Dict[str, set] = {}
        for name, data in crm_data.items():
            if isinstance(data, CRMData):
                feats = set(data.features.core_features)
                for other, other_feats in feature_sets.items():
                    overlap = feats & other_feats
                    if overlap and len(overlap) > 0.8 * len(feats):
                        issues.append(f"Suspicious feature overlap between {name} and {other}")
                feature_sets[name] = feats
        for name, data in crm_data.items():
            if isinstance(data, CRMData):
                for tier in data.pricing_tiers:
                    if tier.monthly_price and tier.monthly_price < 0:
                        issues.append(f"Invalid negative pricing for {name}")
        return issues

    async def __call__(self, state: AgentState) -> AgentState:
        crm_data = state.get("crm_data", {})
        validation_report = self.validate.invoke({"crm_data": crm_data})
        semantic_issues = await self.semantic_validation(crm_data)
        state.setdefault("validation_results", []).append(validation_report)
        avg = 0.0
        if validation_report:
            avg = sum(v.get("score", 0) for v in validation_report.values()) / max(len(validation_report), 1)
        if avg < config.validation_threshold:
            for crm, report in validation_report.items():
                if report.get("score", 0) < config.validation_threshold:
                    state.setdefault("research_status", {})[crm] = False
            state["current_task"] = "research"
        return state
