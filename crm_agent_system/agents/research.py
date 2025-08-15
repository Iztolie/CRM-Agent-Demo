import json
import logging
import asyncio
from datetime import datetime
from typing import List, Optional, Set
from ..config import config
from ..models import AgentState, CRMData

logger = logging.getLogger(__name__)

STRUCTURE_GUIDE = (
    "Return ONLY a single JSON object with keys: name, pricing_tiers (list of objects with name, monthly_price, annual_price, user_limit, notes), "
    "features (object with core_features, automation, analytics, customization), integrations (list with name, category, notes), "
    "limitations (list of strings), best_for (list of strings), confidence_score (float 0-1). LIST every distinct integration/product/tool explicitly mentioned."
)

INTEGRATION_KEYWORDS = [
    "Slack","Zapier","Mailchimp","Stripe","Segment","Shopify","QuickBooks","Gmail","Outlook","Intercom","Twilio","Pabbly","Calendly","Typeform","Salesforce","Google Sheets","Google Analytics","Paddle","Recurly","Chargebee","SyncSpider","ThriveCart"
]

def _extract_json_fragment(text: str) -> Optional[str]:
    """Attempt to extract a JSON object substring from arbitrary LLM output.

    Strategy: find first '{' and last '}' ensuring braces balance. Falls back to None if cannot reconstruct.
    """
    if not text:
        return None
    start = text.find('{')
    end = text.rfind('}')
    if start == -1 or end == -1 or end <= start:
        return None
    fragment = text[start : end + 1]
    # Quick balance heuristic
    if fragment.count('{') == fragment.count('}'):
        return fragment
    return None

class ResearchAgent:
    """Collects raw aspect data via search tool then produces structured CRMData via LLM."""

    def __init__(self, llm, search_tool):
        self.llm = llm
        self.search = search_tool
        # Attempt to prepare a structured-output capable LLM for direct CRMData parsing
        self._structured = None
        try:  # pragma: no cover - depends on provider capabilities
            if hasattr(llm, "with_structured_output"):
                self._structured = llm.with_structured_output(CRMData)
        except Exception:  # fallback silently
            self._structured = None

    def _harvest_integration_candidates(self, raw_text: str) -> Set[str]:
        found: Set[str] = set()
        lower = raw_text.lower()
        for kw in INTEGRATION_KEYWORDS:
            if kw.lower() in lower:
                found.add(kw)
        if found:
            logger.debug(f"Harvested integration candidates for {raw_text[:20]}... -> {found}")
        return found

    async def extract_structured_data(self, crm_name: str, raw_data: str, harvested: Set[str]) -> CRMData:
        if self._structured:
            try:
                prompt = (
                    f"Extract structured CRM data for '{crm_name}'. If information is missing, leave lists empty and set confidence_score <= 0.3.\n"
                    f"List each distinct integration/product/tool explicitly; do NOT hallucinate beyond snippets.\n"
                    f"Snippets: {raw_data}"
                )
                return await self._structured.ainvoke(prompt)
            except Exception as e:  # pragma: no cover
                logger.warning(f"Structured extraction fallback for {crm_name}: {e}")
        # Fallback manual JSON extraction path
        prompt = (
            f"You are a data extraction tool. Using ONLY the provided raw snippets, build a structured JSON object for CRM '{crm_name}'.\n"
            f"If a field is unknown, use an empty list or sensible default (confidence_score <= 0.3).\n"
            f"LIST EVERY DISTINCT INTEGRATION NAME (tools, platforms, apps) mentioned.\n"
            f"RAW_SNIPPETS: {raw_data}\n{STRUCTURE_GUIDE}\nSTRICT: Output ONLY JSON with no commentary."
        )
        response = await self.llm.ainvoke([{ "role": "system", "content": prompt }])
        content = response.content if hasattr(response, 'content') else str(response)
        for attempt in ("direct", "fragment"):
            try:
                candidate = content if attempt == "direct" else _extract_json_fragment(content)
                if not candidate:
                    continue
                data = json.loads(candidate)
                obj = CRMData(**data)
                # Merge harvested integrations if missing
                harvested_existing = {i.name for i in obj.integrations}
                to_add = [kw for kw in harvested if kw not in harvested_existing]
                if to_add:
                    from ..models import Integration
                    for kw in to_add:
                        obj.integrations.append(Integration(name=kw, category="third-party"))
                    # Slight confidence bump if we enriched integrations
                    obj.confidence_score = min(1.0, (obj.confidence_score or 0.3) + 0.1)
                return obj
            except Exception:
                continue
        logger.error(f"Parse failure for {crm_name}: could not extract valid JSON")
        return CRMData(name=crm_name, confidence_score=0.2)

    async def research_crm(self, crm_name: str) -> CRMData:
        calls = [self.search.ainvoke({"crm_name": crm_name, "aspect": aspect}) for aspect in config.aspects]
        results = await asyncio.gather(*calls, return_exceptions=True)
        collected: List[str] = []
        for aspect, result in zip(config.aspects, results):
            if isinstance(result, Exception):
                logger.error(f"Search error {crm_name} {aspect}: {result}")
            else:
                collected.append(str(result))
        # If we have zero snippets, short-circuit without LLM call for efficiency.
        if not collected:
            return CRMData(name=crm_name, confidence_score=0.1)
        raw_text = "\n".join(collected)
        harvested = self._harvest_integration_candidates(raw_text)
        data = await self.extract_structured_data(crm_name, json.dumps(collected), harvested)
        # Second pass enrichment if integrations remain sparse but harvest larger
        if len(data.integrations) < 3 and len(harvested) >= 3:
            from ..models import Integration
            existing = {i.name for i in data.integrations}
            added = 0
            for kw in harvested:
                if kw not in existing:
                    data.integrations.append(Integration(name=kw, category="third-party"))
                    added += 1
                if len(data.integrations) >= 5:
                    break
            if added:
                logger.debug(f"Post-pass added {added} integrations for {crm_name}")
                data.confidence_score = min(1.0, (data.confidence_score or 0.3) + 0.05)
        # Normalize & dedupe integrations (case-insensitive)
        if data.integrations:
            seen = {}
            normalized = []
            for integ in data.integrations:
                key = integ.name.strip().lower()
                if key in seen:
                    continue
                # Canonical capitalization
                integ.name = seen[key] = integ.name.strip().replace("mailchimp", "Mailchimp").replace("quickbooks", "QuickBooks")
                normalized.append(integ)
            if len(normalized) != len(data.integrations):
                logger.debug(f"Deduped integrations for {crm_name}: {len(data.integrations)} -> {len(normalized)}")
            data.integrations = normalized
            # Log normalized integration snapshot (capped list for brevity)
            try:
                integ_names = sorted(i.name for i in data.integrations)
                logger.debug(
                    "Normalized integrations crm=%s count=%d sample=%s", 
                    crm_name, len(integ_names), integ_names[:12]
                )
            except Exception:  # pragma: no cover
                pass
        # Confidence heuristic (evidence-based)
        try:
            pricing_ok = 1 if data.pricing_tiers else 0
            feature_cats = sum(bool(getattr(data.features, cat)) and len(getattr(data.features, cat)) > 0 for cat in ["core_features","automation","analytics","customization"])
            feature_cov = feature_cats / 4
            integ_cov = min(len(data.integrations) / 15, 1.0)
            limitations_ok = 1 if data.limitations else 0
            base = 0.15
            confidence = base + 0.15*pricing_ok + 0.35*feature_cov + 0.25*integ_cov + 0.10*limitations_ok
            data.confidence_score = round(min(confidence, 0.95), 3)
            logger.debug(
                "Confidence components crm=%s pricing=%d feature_cov=%.2f integ_cov=%.2f limitations=%d final=%.3f",
                crm_name, pricing_ok, feature_cov, integ_cov, limitations_ok, data.confidence_score
            )
        except Exception as e:  # pragma: no cover
            logger.debug(f"Confidence heuristic failed for {crm_name}: {e}")
        return data

    async def __call__(self, state: AgentState) -> AgentState:
        crm_data = state.get("crm_data", {})
        research_status = state.get("research_status", {})
        pending = [c for c in config.crms if not research_status.get(c)]
        if pending:
            results = await asyncio.gather(*[self.research_crm(c) for c in pending], return_exceptions=True)
            for crm, result in zip(pending, results):
                if isinstance(result, Exception):
                    state.setdefault("error_log", []).append({
                        "timestamp": datetime.now().isoformat(),
                        "agent": "research",
                        "error": str(result),
                        "crm": crm
                    })
                    logger.error(f"Research failed for {crm}: {result}")
                else:
                    if isinstance(result, CRMData):
                        crm_data[crm] = result
                        research_status[crm] = True
        state["crm_data"] = crm_data
        state["research_status"] = research_status
        logger.info(f"Research complete for {len(crm_data)} CRMs")
        return state
