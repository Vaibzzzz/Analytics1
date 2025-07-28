from fastapi import APIRouter, Query
from typing import Optional
from KPI.KPI_Dashboard import fetch_dashboard_data
from LLM.grok_client import generate_grok_insight
import tiktoken

router = APIRouter()

# --- Token counter for debugging usage ---
def count_tokens(prompt: str, model: str = "gpt-3.5-turbo") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(prompt))

# --- Prompt builders for each chart ---
def build_currency_revenue_prompt(data: list) -> str:
    return (
        "You're a senior payments strategist. Based on the revenue by currency data below, write a 60–80 word insight.\n\n"
        + "\n".join([f"{item['name']}: {item['value']}%" for item in data]) +
        "\n\nFocus on:\n"
        "- Dominant currencies\n- Currency concentration risks\n- Strategic exposure or FX optimization."
    )

def build_acquirer_volume_prompt(x_axis: list, y_axis: list) -> str:
    return (
        "You're a transaction operations analyst. Based on the acquirer-wise transaction volume below, provide a 60–80 word insight.\n\n"
        + "\n".join([f"{name}: {count} txns" for name, count in zip(x_axis, y_axis)]) +
        "\n\nDiscuss:\n"
        "- Leading vs lagging acquirers\n- Consolidation opportunities\n- Partner optimization."
    )

def build_payment_method_prompt(x_axis: list, y_axis: list) -> str:
    return (
        "You're a digital payments specialist. Based on the distribution of payment methods below, generate a 60–80 word insight.\n\n"
        + "\n".join([f"{method}: {count} txns" for method, count in zip(x_axis, y_axis)]) +
        "\n\nInclude:\n"
        "- Dominant card types\n- Usage trends\n- Strategy for supporting preferred methods."
    )

# --- Endpoint 1: KPI dashboard data (charts + metrics) ---
@router.get("/dashboard")
def get_dashboard_data():
    return fetch_dashboard_data()


# --- Endpoint 2: AI Insight for a selected chart ---
@router.get("/dashboard/insights")
def dashboard_ai_insight(chart_id: str = Query(..., description="Title of the chart")):
    result = fetch_dashboard_data()
    chart = next((c for c in result.get("charts", []) if c.get("title") == chart_id), None)
    if not chart:
        return {"error": f"Chart with title '{chart_id}' not found."}

    # Match chart title and generate the appropriate prompt
    prompt = ""
    if chart_id == "Revenue by Currency":
        prompt = build_currency_revenue_prompt(chart.get("data", []))
    elif chart_id == "Top 5 Acquirers by Volume":
        prompt = build_acquirer_volume_prompt(chart.get("x", []), chart.get("y", []))
    elif chart_id == "Payment Method Distribution":
        prompt = build_payment_method_prompt(chart.get("x", []), chart.get("y", []))

    if not prompt:
        return {"error": f"No insight generator defined for chart '{chart_id}'."}

    input_tokens = count_tokens(prompt)

    try:
        response = generate_grok_insight(prompt, return_usage=True)
        insight = response['text']
        output_tokens = response['usage']['completion_tokens']
        total_tokens = response['usage']['total_tokens']
    except Exception as e:
        return {"chart_id": chart_id, "insight": f"Insight generation failed: {str(e)}"}

    return {
        "chart_id": chart_id,
        "insight": insight,
        "token_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        }
    }
