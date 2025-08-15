from typing import Dict
from .config import config

def format_comparison_table(comparison: Dict) -> str:
    scores = comparison.get("scores", {})
    data = comparison.get("detailed_data", {})
    table = "| CRM | Pricing | Features | Integrations | Overall | Best For |\n"
    table += "|-----|---------|----------|-------------|---------|----------|\n"
    for crm in config.crms:
        if crm in scores:
            s = scores[crm]
            best_for = ", ".join(data.get(crm, {}).get("best_for", [])[:2]) if isinstance(data.get(crm), dict) else ""
            table += f"| {crm} | {s['pricing']:.2f} | {s['features']:.2f} | {s['integrations']:.2f} | {s['overall']:.2f} | {best_for} |\n"
    return table
