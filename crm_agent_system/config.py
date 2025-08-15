from dataclasses import dataclass, field
from typing import List
import os
from pathlib import Path
from dotenv import load_dotenv

# Explicitly resolve project root .env so running from any CWD still loads keys
_ENV_PATH = Path(__file__).resolve().parent.parent / ".env"
if _ENV_PATH.exists():
    load_dotenv(_ENV_PATH)
else:  # fallback (original search behavior)
    load_dotenv()

@dataclass
class Config:
    """Centralized configuration object."""
    crms: List[str] = field(default_factory=lambda: ["HubSpot", "Zoho", "Salesforce"])
    aspects: List[str] = field(default_factory=lambda: ["pricing", "features", "integrations", "limitations"])
    llm_provider: str = "openai"
    llm_model: str = "gpt-4o-mini"
    llm_temperature: float = 0.3
    search_provider: str = "tavily"
    max_search_results: int = 8
    # Optional per-aspect query suffixes to enrich specificity
    aspect_query_templates: dict = field(default_factory=lambda: {
        "pricing": "pricing tiers 2025",
        "features": "key features 2025",
        "integrations": "integrations app marketplace 2025 Zapier Slack",
        "limitations": "limitations drawbacks cons 2025",
    })
    max_iterations: int = 10
    validation_threshold: float = 0.8
    convergence_window: int = 2
    max_retries: int = 3
    retry_delay: float = 1.0
    exponential_backoff: bool = True

config = Config()
