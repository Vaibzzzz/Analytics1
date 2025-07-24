from fastapi import APIRouter, Query
from datetime import date
from typing import Optional, Tuple, List

from KPI.DemoGraphic import get_demo_kpi_data
from LLM.grok_client import generate_grok_insight

router = APIRouter()

# ───────────────────────────
# 1. CHART-ONLY ENDPOINT
# ───────────────────────────
@router.get("/demographic")
def demographic_kpis(
    filter_type: str = Query(default="YTD", description="Filter type like Daily, Weekly, MTD, etc."),
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None)
):
    custom = (start, end) if start and end else None
    return get_demo_kpi_data(filter_type, custom)


# ───────────────────────────
# 2. INSIGHT-ONLY ENDPOINT
# ───────────────────────────
@router.get("/demographic/insight")
def demographic_insight(
    filter_type: str = Query(default="YTD", description="Filter type like Daily, Weekly, MTD, etc."),
    start: Optional[date] = Query(default=None),
    end: Optional[date] = Query(default=None)
):
    custom = (start, end) if start and end else None
    result = get_demo_kpi_data(filter_type, custom)

    chart = result.get("charts", [])[0] if result.get("charts") else None
    if not chart:
        return {"insight": "No data available to generate insight."}

    # Unpack values from metrics for prompt generation
    metrics = {m["title"]: m["value"] for m in result.get("metrics", [])}
    country_count = metrics.get("Operational Countries", "N/A")
    state_count = metrics.get("Operational States", "N/A")
    us_sales = metrics.get("US Sales", "N/A")
    gb_sales = metrics.get("GB Sales", "N/A")
    us_success_rate = metrics.get("US Success Rate", "N/A")
    gb_success_rate = metrics.get("GB Success Rate", "N/A")
    top_issuer_country = metrics.get("Top Issuer Country", "N/A")
    top_issuer_percent = metrics.get("Top Issuer Share", "N/A")
    top_us_state = metrics.get("Top US State", "N/A")
    us_txn_count = metrics.get("Top US State Txns", "N/A")
    top_uk_state = metrics.get("Top UK State", "N/A")
    gb_txn_count = metrics.get("Top UK State Txns", "N/A")

    def build_demo_prompt() -> str:
        return f"""
You are a data analyst reviewing performance metrics from a payments platform. Below is demographic KPI data:

- Operational Countries Count: {country_count}
- Operational States Count: {state_count}

- Sales by Region (US/GB):
  - US: ${us_sales}
  - GB: ${gb_sales}

- Success Rate by Country (in %):
  - US: {us_success_rate}%
  - GB: {gb_success_rate}%

- Card Issuing Country Distribution (Top % share):
  - {top_issuer_country}: {top_issuer_percent}%

- Top States/Provinces by Transaction Count (US & GB):
  - US: {top_us_state} ({us_txn_count} txns)
  - GB: {top_uk_state} ({gb_txn_count} txns)

⚡ Write a concise, 4–6 bullet summary highlighting:
- Notable high/low performers across regions
- Unusual patterns or outliers
- Regions where user adoption appears strongest
- Any insight the business team should know based on distribution

Keep it tight, sharp, and focused on business relevance.
        """

    try:
        prompt = build_demo_prompt()
        insight = generate_grok_insight(prompt)
    except Exception as e:
        insight = f"Insight generation failed: {str(e)}"

    return {"insight": insight}
