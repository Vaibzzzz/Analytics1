from fastapi import APIRouter, Query
from datetime import date
from typing import Optional, Tuple
from KPI.customer_insight import get_customer_insights_data
from LLM.grok_client import generate_grok_insight  # Correct import
import asyncio

router = APIRouter()

# ───────────────────────────────────────────────────────────────
@router.get(
    "/customer-insights",
    summary="Get Customer Insights metrics and charts",
    description=(
        "Returns customer insights KPIs and chart data for the given time filter. "
        "Supported filters: Today, Yesterday, Daily, Weekly, MTD, Monthly, YTD, custom. "
        "For custom, also supply start and end dates in YYYY-MM-DD format."
    )
)
def customer_insights(
    filter_type: str = Query(
        "YTD",
        regex="^(Today|Yesterday|Daily|Weekly|MTD|Monthly|YTD|custom)$",
        description="Predefined time filter"
    ),
    start: Optional[date] = Query(None, description="Start date for custom range (YYYY-MM-DD)"),
    end: Optional[date] = Query(None, description="End date for custom range (YYYY-MM-DD)")
):
    custom_range: Optional[Tuple[date, date]] = (start, end) if start and end else None
    return get_customer_insights_data(filter_type, custom_range)

# ───────────────────────────────────────────────────────────────
@router.get("/customer-insights/insight")
def customer_insights_ai_insight(
    chart_id: Optional[str] = Query(None, description="Chart title to identify which chart insight to generate"),
    filter_type: str = Query("YTD"),
    start: Optional[date] = Query(None),
    end: Optional[date] = Query(None)
):
    custom_range = (start, end) if start and end else None
    dashboard_data = get_customer_insights_data(filter_type, custom_range)

    # Match the chart by its title
    chart_data = next((chart for chart in dashboard_data["charts"] if chart["title"] == chart_id), None)

    if chart_data is None:
        return {"error": "Please provide a valid chart_id."}

    prompt = (
        "You are an analytics assistant. Based on the following chart data, "
        "generate a short and actionable business insight. "
        "Keep it concise, relevant, and insightful.\n\n"
        f"{chart_data}"
    )

    insight = generate_grok_insight(prompt=prompt)
    return {"insight": insight}
