import json
import logging
from datetime import datetime
from typing import Dict
from ..models import AgentState, CRMData
from ..utils import retry_with_backoff

logger = logging.getLogger(__name__)

class AnalysisAgent:
    def __init__(self, llm):
        self.llm = llm

    def calculate_scores(self, crm_data: Dict[str, CRMData]):
        scores = {}
        for name, data in crm_data.items():
            if not isinstance(data, CRMData):
                continue
            pricing_score = 0
            if data.pricing_tiers:
                min_price = min((t.monthly_price or float('inf') for t in data.pricing_tiers), default=100)
                pricing_score = max(0, 100 - min_price) / 100
            feature_count = len(data.features.core_features) + len(data.features.automation) + len(data.features.analytics)
            feature_score = min(feature_count / 20, 1.0)
            # Adjusted integration scoring: denser weighting (assume 15 distinct integrations ~ full score)
            integration_score = min(len(data.integrations) / 15, 1.0)
            overall = pricing_score * 0.3 + feature_score * 0.4 + integration_score * 0.3
            scores[name] = {
                "pricing": pricing_score,
                "features": feature_score,
                "integrations": integration_score,
                "overall": overall,
            }
        return scores

    def generate_recommendations(self, scores: Dict[str, Dict[str, float]]):
        recs = {}
        if not scores:
            return recs
        recs["best_overall"] = max(scores.items(), key=lambda x: x[1]["overall"])[0]
        recs["best_value"] = max(scores.items(), key=lambda x: x[1]["pricing"])[0]
        recs["most_features"] = max(scores.items(), key=lambda x: x[1]["features"])[0]
        recs["best_integrations"] = max(scores.items(), key=lambda x: x[1]["integrations"])[0]
        return recs

    @retry_with_backoff()
    async def __call__(self, state: AgentState) -> AgentState:
        crm_data = state.get("crm_data", {})
        # Log integration counts for transparency
        for n, d in crm_data.items():
            if isinstance(d, CRMData):
                logger.debug(f"Integration count {n} = {len(d.integrations)} (confidence={d.confidence_score})")
        scores = self.calculate_scores(crm_data)
        recs = self.generate_recommendations(scores)
        prompt = f"""
        Create a concise executive summary comparing these CRMs for small B2B businesses:
        Scores: {json.dumps(scores, indent=2)}
        Data: {json.dumps({k: v.dict() if isinstance(v, CRMData) else {} for k, v in crm_data.items()}, indent=2)}
        Focus on key differentiators and practical recommendations. Keep under 300 words.
        """
        response = await self.llm.ainvoke([{"role": "system", "content": prompt}])
        # Disclaimer if any confidence below threshold (e.g., 0.4)
        low_conf = [n for n,d in crm_data.items() if isinstance(d, CRMData) and d.confidence_score < 0.4]
        disclaimer = ""
        if low_conf:
            disclaimer = f"\n\nDisclaimer: Data for {', '.join(low_conf)} may be incomplete; treat related comparisons cautiously."
        state["final_comparison"] = {
            "summary": (response.content or "") + disclaimer,
            "scores": scores,
            "recommendations": recs,
            "detailed_data": {k: v.dict() if isinstance(v, CRMData) else {} for k, v in crm_data.items()},
            "timestamp": datetime.now().isoformat(),
        }
        logger.info("Analysis complete")
        return state
