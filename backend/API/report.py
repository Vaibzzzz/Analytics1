from fastapi import APIRouter, Query
from typing import Optional, List, Tuple
from datetime import date
import tiktoken

from KPI.report import get_gateway_fee_analysis
from LLM.grok_client import generate_grok_insight
from KPI.utils.time_utils import get_date_ranges

router = APIRouter()

# ────────────────────────────────────────
# Utility: Token Estimator
# ────────────────────────────────────────
def count_tokens(prompt: str, model: str = "gpt-3.5-turbo") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(prompt))

# ────────────────────────────────────────
# Utility: Prompt Builder
# ────────────────────────────────────────
def build_gateway_fee_prompt(acquirer_data: List[Tuple[str, float]], 
                             yesterday_val: float,
                             hist_avg: float,
                             z_score: float,
                             p_value: float) -> str:
    return (
        "You are a senior payments strategy analyst. Based on the data below, generate a 60–80 word actionable business insight with strategic recommendations.\n\n"
        f"Yesterday’s total gateway fee: ${yesterday_val:.2f}\n"
        f"7-day average: ${hist_avg:.2f}\n"
        "Acquirer-wise gateway fee distribution:\n" +
        "\n".join([f"{name}: ${fee:.2f}" for name, fee in acquirer_data]) +
        f"\n\nZ-score: {z_score:.2f}, P-value: {p_value:.4f}\n\n"
        "In your insight:\n"
        "- Highlight if the fee change is notable and why\n"
        "- Identify the most cost-efficient acquirers\n"
        "- Recommend a tactical action (e.g., volume shift or pilot test)\n"
        "- Mention any risks or what to monitor (e.g., if the trend is temporary)\n\n"
        "Avoid technical statistical terms in the final insight. Do not explain what a Z-score or P-value means. Just present a business-focused, high-level recommendation without repeating the numbers."
    )


# ────────────────────────────────────────
# Endpoint 1: Chart-Only KPI
# ────────────────────────────────────────
@router.get("/gateway-fee")
def gateway_fee_kpi(
    filter_type: str = Query("YTD", enum=["Daily", "Weekly", "MTD", "YTD", "Custom"]),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    custom_range = (start_date, end_date) if filter_type == "Custom" and start_date and end_date else None
    result = get_gateway_fee_analysis(filter_type, custom_range)
    print(result.get('metrics', []))

    return {
        "metrics": result.get('metrics', []),
        "charts": result.get('charts', [])
    }

# ────────────────────────────────────────
# Endpoint 2: Insight + Token Usage
# ────────────────────────────────────────
@router.get("/gateway-fee/insight")
def gateway_fee_insight(
    filter_type: str = Query("YTD", enum=["Daily", "Weekly", "MTD", "YTD", "Custom"]),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    custom_range = (start_date, end_date) if filter_type == "Custom" and start_date and end_date else None
    result = get_gateway_fee_analysis(filter_type, custom_range)

    chart = result['charts'][0] if result['charts'] else None
    if not chart:
        return {"insight": "No data available to generate insight."}

    # Prepare data for prompt
    acquirer_data = list(zip(chart['x'], chart['y']))[:10]
    # Fetch metrics for stat insight
    metric = result['metrics'][0] if result['metrics'] else {}
    yesterday_val = metric.get('value', 0)
    hist_avg = metric.get('historical_avg', 0)
    z_score = metric.get('z_score', 0)
    p_value = metric.get('p_value', 0)

    prompt = build_gateway_fee_prompt(acquirer_data, yesterday_val, hist_avg, z_score, p_value)
    print(f"Generated prompt: {prompt}")

    # Count input tokens
    input_tokens = count_tokens(prompt)

    try:
        # Assuming the LLM client supports returning usage
        response = generate_grok_insight(prompt, return_usage=True)
        insight = response['text']
        output_tokens = response['usage']['completion_tokens']
        total_tokens = response['usage']['total_tokens']
    except Exception as e:
        insight = f"Insight generation failed: {str(e)}"
        output_tokens = None
        total_tokens = None

    return {
        "insight": insight,
        "token_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        }
    }
