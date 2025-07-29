from fastapi import APIRouter, Query
from typing import Optional, List, Tuple, Dict, Any
from datetime import date
import tiktoken

from KPI.financial_analysis import get_financial_performance_data
from LLM.grok_client import generate_grok_insight
from KPI.utils.stat_tests import compare_to_historical_single_point

router = APIRouter()


# ────────────────────────────────────────
# Utility: Token Estimator
# ────────────────────────────────────────
def count_tokens(prompt: str, model: str = "gpt-3.5-turbo") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(prompt))


# ────────────────────────────────────────
# Prompt Builders (now include stats)
# ────────────────────────────────────────
def build_sales_by_currency_prompt(
    data: List[Dict[str, Any]],
    yesterday: float,
    hist_avg: float,
    z_score: float,
    p_value: float
) -> str:
    lines = [f"{row['name']}: ${row['value']:.2f}" for row in data]
    return (
        "You are a senior payments analyst. Based on the currency‑wise sales data below, write a 60–80 word strategic insight.\n\n"
        f"Yesterday’s total sales: ${yesterday:.2f}\n"
        f"7‑day average: ${hist_avg:.2f}\n"
        f"Z‑score: {z_score:.2f}, P‑value: {p_value:.4f}\n\n"
        "Sales breakdown:\n" + "\n".join(lines) +
        "\n\nInclude insights such as:\n"
        "- Dominant currencies and their share\n"
        "- Currency performance shift if visible\n"
        "- Strategic advice on currency risk exposure or optimization."
    )


def build_processing_fee_prompt(
    acquirer_data: List[Tuple[str, float]],
    yesterday: float,
    hist_avg: float,
    z_score: float,
    p_value: float
) -> str:
    lines = [f"{name}: {fee:.2f}%" for name, fee in acquirer_data]
    return (
        "You are a payments cost optimization specialist. Analyze the acquirer‑wise processing fee data and provide a concise 60–80 word business insight.\n\n"
        f"Yesterday’s avg fee %: {yesterday:.2f}\n"
        f"7‑day avg: {hist_avg:.2f}\n"
        f"Z‑score: {z_score:.2f}, P‑value: {p_value:.4f}\n\n"
        "Fee distribution:\n" + "\n".join(lines) +
        "\n\nIn your insight:\n"
        "- Highlight cost leaders and laggards\n"
        "- Recommend tactical optimizations\n"
        "- Mention risks (volatility, volume sensitivity, etc.)"
    )


# ────────────────────────────────────────
# Endpoint 1: Financial KPIs + Charts
# ────────────────────────────────────────
@router.get("/financial-performance")
def financial_kpis(
    filter_type: str = Query("YTD", enum=["Daily", "Weekly", "MTD", "YTD", "Custom"]),
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    custom_range = (
        (start_date, end_date)
        if filter_type == "Custom" and start_date and end_date
        else None
    )
    result = get_financial_performance_data(filter_type, custom_range)
    return {
        "metrics": result.get("metrics", []),
        "charts":  result.get("charts",  []),
    }


# ────────────────────────────────────────
# Endpoint 2: AI Insight for a Selected Chart
# ────────────────────────────────────────
@router.get("/financial-performance/insights")
def financial_kpi_insight(
    chart_id:   str = Query(..., description="Title of the chart to generate insight for"),
    filter_type: str = Query("YTD", enum=["Daily", "Weekly", "MTD", "YTD", "Custom"]),
    start_date: Optional[date] = Query(None),
    end_date:   Optional[date] = Query(None),
):
    custom_range = (
        (start_date, end_date)
        if filter_type == "Custom" and start_date and end_date
        else None
    )
    result = get_financial_performance_data(filter_type, custom_range)

    # Find the requested chart
    chart = next((c for c in result.get("charts", []) if c.get("title") == chart_id), None)
    if not chart:
        return {"error": f"Chart with title '{chart_id}' not found."}

    # Pull out the insight_data series
    insight_data = result.get("insight_data", {})
    trace = {}
    if chart_id == "Sales by Currency":
        trace = insight_data.get("sales_by_currency", {})
    elif chart_id == "Processing Fee Analysis":
        trace = insight_data.get("processing_fee_pct", {})
    else:
        return {"error": f"No insight builder defined for '{chart_id}'."}

    # Compute stats from the series
    yesterday = trace.get("yesterday", 0.0)
    hist      = trace.get("historical", [])
    hist_avg  = sum(hist) / len(hist) if hist else 0.0
    comp      = compare_to_historical_single_point(yesterday, hist)
    z_score   = comp["z_score"]
    p_value   = comp["p_value"]

    # Build the prompt
    if chart_id == "Sales by Currency":
        prompt = build_sales_by_currency_prompt(
            chart.get("data", []),
            yesterday, hist_avg, z_score, p_value
        )
    else:  # Processing Fee Analysis
        x = chart.get("x", [])
        # Depending on how you named it, your data might live in chart['series'][0]['data']
        y = chart.get("series", [{}])[0].get("data", [])
        acquirer_data = list(zip(x, y))
        prompt = build_processing_fee_prompt(
            acquirer_data,
            yesterday, hist_avg, z_score, p_value
        )

    # Count input tokens
    input_tokens = count_tokens(prompt)

    # Generate the insight
    try:
        resp = generate_grok_insight(prompt, return_usage=True)
        if isinstance(resp, dict):
            insight       = resp.get("text")
            usage         = resp.get("usage", {})
            output_tokens = usage.get("completion_tokens")
            total_tokens  = usage.get("total_tokens")
        else:
            # Assuming tuple/list: [text, {usage}]
            insight       = resp[0]
            output_tokens = resp[1].get("completion_tokens")
            total_tokens  = resp[1].get("total_tokens")
    except Exception as e:
        return {
            "chart_id": chart_id,
            "insight":  f"Insight generation failed: {str(e)}"
        }

    return {
        "chart_id": chart_id,
        "insight":  insight,
        "token_usage": {
            "input_tokens":  input_tokens,
            "output_tokens": output_tokens,
            "total_tokens":  total_tokens,
        }
    }
