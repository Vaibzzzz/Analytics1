from fastapi import APIRouter, Query
from typing import List, Dict, Any
import tiktoken

from LLM.grok_client import generate_grok_insight
from KPI.dashboard import fetch_processing_partner, fetch_top5_acquirers,fetch_payment_method_distribution

router = APIRouter()

# ────────────────────────────────────────
# Utility: Token Estimator
# ────────────────────────────────────────
def count_tokens(prompt: str, model: str = "gpt-3.5-turbo") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(prompt))


# ────────────────────────────────────────
# Prompt Builders (including extra_metrics)
# ────────────────────────────────────────
def build_currency_revenue_prompt(
    data: List[Dict[str, Any]],
    yesterday: float,
    hist_avg: float,
    z_score: float,
    p_value: float
) -> str:
    lines = [f"{item['name']}: {item['value']}%" for item in data]
    return (
        "You're a senior payments strategist. Based on the revenue by currency data below, write a 60–80 word insight.\n\n"
        f"Yesterday’s total revenue: {yesterday:.2f}% of weekly average\n"
        f"7-day avg share: {hist_avg:.2f}%\n"
        f"Z-score: {z_score:.2f}, P-value: {p_value:.4f}\n\n"
        "Currency breakdown:\n" +
        "\n".join(lines) +
        "\n\nFocus on:\n"
        "- Dominant currencies\n"
        "- Currency concentration risks\n"
        "- Strategic FX optimisation."
    )


def build_acquirer_volume_prompt(
    x_axis: List[str],
    y_axis: List[int],
    yesterday: float,
    hist_avg: float,
    z_score: float,
    p_value: float
) -> str:
    lines = [f"{name}: {count} txns" for name, count in zip(x_axis, y_axis)]
    return (
        "You're a transaction operations analyst. Based on yesterday’s acquirer volume vs historical trend, write a 60–80 word insight.\n\n"
        f"Yesterday’s txn count: {yesterday:.0f}\n"
        f"7-day avg: {hist_avg:.0f}\n"
        f"Z-score: {z_score:.2f}, P-value: {p_value:.4f}\n\n"
        "Acquirer volume:\n" +
        "\n".join(lines) +
        "\n\nDiscuss:\n"
        "- Leading vs lagging partners\n"
        "- Consolidation or rebalancing\n"
        "- Tactical optimisation."
    )


def build_payment_method_prompt(
    x_axis: List[str],
    y_axis: List[int],
    yesterday: float,
    hist_avg: float,
    z_score: float,
    p_value: float
) -> str:
    lines = [f"{method}: {cnt} txns" for method, cnt in zip(x_axis, y_axis)]
    return (
        "You're a digital payments specialist. Write a 60–80 word insight on yesterday’s payment method distribution vs historical.\n\n"
        f"Yesterday’s total txns: {yesterday:.0f}\n"
        f"7-day avg: {hist_avg:.0f}\n"
        f"Z-score: {z_score:.2f}, P-value: {p_value:.4f}\n\n"
        "Distribution:\n" +
        "\n".join(lines) +
        "\n\nInclude:\n"
        "- Dominant card types\n"
        "- Trend shifts\n"
        "- Support strategy recommendations."
    )


# ────────────────────────────────────────
# Endpoint 1: KPI Dashboard Data
# ────────────────────────────────────────
@router.get("/dashboard")
def get_dashboard_data():
    """
    Returns the raw charts + metrics (including extra_metrics per chart).
    """
    return fetch_top5_acquirers(),fetch_payment_method_distribution(),fetch_processing_partner()


# ────────────────────────────────────────
# Endpoint 2: AI Insight for a Selected Chart
# ────────────────────────────────────────
@router.get("/dashboard/insights")
def dashboard_ai_insight(
    chart_id: str = Query(..., description="Title of the chart to analyze")
):
    result = fetch_dashboard_data()
    chart = next((c for c in result.get("charts", []) if c.get("title") == chart_id), None)
    if not chart:
        return {"error": f"Chart with title '{chart_id}' not found."}

    # pull out the 4 statistical metrics from extra_metrics
    extra = chart.get("extra_metrics", {})
    yesterday  = extra.get("value", 0)
    hist_avg   = extra.get("historical_avg", 0)
    z_score    = extra.get("z_score", 0)
    p_value    = extra.get("p_value", 0)

    # build the appropriate prompt
    prompt = ""
    if chart_id == "Revenue by Currency":
        prompt = build_currency_revenue_prompt(
            chart.get("data", []),
            yesterday, hist_avg, z_score, p_value
        )
    elif chart_id == "Top 5 Acquirers by Volume":
        prompt = build_acquirer_volume_prompt(
            chart.get("x", []),
            chart.get("y", []),
            yesterday, hist_avg, z_score, p_value
        )
    elif chart_id == "Payment Method Distribution":
        prompt = build_payment_method_prompt(
            chart.get("x", []),
            chart.get("y", []),
            yesterday, hist_avg, z_score, p_value
        )
    else:
        return {"error": f"No insight generator defined for '{chart_id}'."}

    # count tokens
    input_tokens = count_tokens(prompt)

    # call your LLM client
    try:
        resp = generate_grok_insight(prompt, return_usage=True)
        import json
        if isinstance(resp, dict):
            insight = resp["text"]
            usage   = resp["usage"]
        else:
            insight, usage = resp[0], resp[1]

        if isinstance(usage, str):
            try:
                usage = json.loads(usage)
            except Exception:
                usage = {}

        output_tokens = usage.get("completion_tokens")
        total_tokens  = usage.get("total_tokens")
    except Exception as e:
        insight = f"Insight generation failed: {str(e)}"
        output_tokens = total_tokens = None

    return {
        "chart_id":   chart_id,
        "insight":    insight,
        "token_usage": {
            "input_tokens":  input_tokens,
            "output_tokens": output_tokens,
            "total_tokens":  total_tokens
        }
    }
