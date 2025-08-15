"""Simulation helpers to convert mock search data into structured CRMData objects."""
from typing import List, Dict
from crm_agent_system.models import CRMData, PricingTier, CRMFeatures, Integration


def extract_pricing(crm: str, raw: List[Dict]) -> List[PricingTier]:
    tiers: List[PricingTier] = []
    for item in raw:
        content = item.get("content", "")
        if "Free" in content:
            tiers.append(PricingTier(name="Free", monthly_price=0, annual_price=None, user_limit=None, features=["Basic CRM"]))
        if any(k in content for k in ["Starter", "Standard", "Essentials"]):
            price = 20 if "HubSpot" in content else 14 if "Zoho" in content else 25
            tiers.append(PricingTier(name="Starter", monthly_price=price, annual_price=None, user_limit=None, features=["Core features"]))
        if "Professional" in content:
            price = 890 if "HubSpot" in content else 23 if "Zoho" in content else 80
            tiers.append(PricingTier(name="Professional", monthly_price=price, annual_price=None, user_limit=None, features=["Advanced features"]))
    return tiers


def extract_features(raw: List[Dict]) -> CRMFeatures:
    return CRMFeatures(
        core_features=["Contact Management", "Deal Tracking", "Email Integration"],
        automation=["Workflow Automation", "Email Sequences"],
        analytics=["Reporting Dashboard", "Custom Reports"],
        customization=["Custom Fields", "Custom Modules"],
    )


def extract_integrations(raw: List[Dict]) -> List[Integration]:
    integrations: List[Integration] = []
    for item in raw:
        content = item.get("content", "")
        if "Slack" in content:
            integrations.append(Integration(name="Slack", category="Communication", native=True))
        if any(k in content for k in ["Gmail", "Office"]):
            integrations.append(Integration(name="Email", category="Productivity", native=True))
        if any(k in content.lower() for k in ["marketplace", "apps"]):
            if "HubSpot" in content:
                integrations.append(Integration(name="1000+ Apps", category="Marketplace", native=False))
            elif "Zoho" in content:
                integrations.append(Integration(name="300+ Apps", category="Marketplace", native=False))
            else:
                integrations.append(Integration(name="4000+ Apps", category="Marketplace", native=False))
    return integrations


def extract_limitations(raw: List[Dict]) -> List[str]:
    limitations: List[str] = []
    for item in raw:
        content = item.get("content", "")
        if "limited" in content.lower():
            limitations.append(content.split(".")[0])
    return limitations or ["Some limitations apply"]


def build_crm_data(name: str, blocks: Dict) -> CRMData:
    return CRMData(
        name=name,
        pricing_tiers=extract_pricing(name, blocks.get("pricing", [])),
        features=extract_features(blocks.get("features", [])),
        integrations=extract_integrations(blocks.get("integrations", [])),
        limitations=extract_limitations(blocks.get("limitations", [])),
        best_for=["SMB", "B2B"],
        confidence_score=0.9,
    )
