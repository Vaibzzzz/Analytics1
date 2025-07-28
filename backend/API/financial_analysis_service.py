from fastapi import APIRouter, Query
from typing import Optional, List, Tuple
from datetime import date
import tiktoken

from KPI.financial_analysis import get_financial_performance_data
from LLM.grok_client import generate_grok_insight
from KPI.utils.time_utils import get_date_ranges

router = APIRouter()

def count_tokens(prompt: str, model: str = "gpt-3.5-turbo") -> int:
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(prompt))

def build_sales_by_currency_prompt(data: List[dict]) -> str:
    return (
        "You are a senior payments analyst. Based on the currency-wise sales data below, write a 60–80 word strategic insight.\n\n"
        + "\n".join([f"{row['name']}: ${row['value']:.2f}" for row in data]) +
        "\n\nInclude insights such as:\n"
        "- Dominant currencies and their share\n"
        "- Currency performance shift if visible\n"
        "- Strategic advice on currency risk exposure or optimization."
    )

def build_processing_fee_prompt(acquirer_data: List[Tuple[str, float]]) -> str:
    return (
        "You are a payments cost optimization specialist. Analyze the acquirer-wise processing fee data and provide a concise 60–80 word business insight.\n\n"
        + "\n".join([f"{name}: ${fee:.2f}" for name, fee in acquirer_data]) +
        "\n\nIn your insight:\n"
        "- Highlight cost leaders and laggards\n"
        "- Recommend tactical optimizations\n"
        "- Mention risks (volatility, volume sensitivity, etc.)"
    )

@router.get("/financial-performance")
def financial_kpis(
    filter_type: str = Query("YTD", enum=["Daily", "Weekly", "MTD", "YTD", "Custom"]),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    custom_range = (start_date, end_date) if filter_type == "Custom" and start_date and end_date else None
    result = get_financial_performance_data(filter_type, custom_range)
    return {
        "metrics": result.get("metrics", []),
        "charts": result.get("charts", [])
    }

@router.get("/financial-performance/insights")
def financial_kpi_insight(
    chart_id: str = Query(..., description="Title of the chart to generate insight for"),
    filter_type: str = Query("YTD", enum=["Daily", "Weekly", "MTD", "YTD", "Custom"]),
    start_date: Optional[date] = Query(None),
    end_date: Optional[date] = Query(None),
):
    custom_range = (start_date, end_date) if filter_type == "Custom" and start_date and end_date else None
    result = get_financial_performance_data(filter_type, custom_range)

    chart = next((c for c in result.get("charts", []) if c.get("title") == chart_id), None)
    if not chart:
        return {"error": f"Chart with title '{chart_id}' not found."}

    prompt = ""
    if chart_id == "Sales by Currency":
        prompt = build_sales_by_currency_prompt(chart.get("data", []))
    elif chart_id == "Processing Fee Analysis":
        x = chart.get("x_axis", [])
        y = chart.get("series", [{}])[0].get("data", [])
        acquirer_data = list(zip(x, y))[:10]
        prompt = build_processing_fee_prompt(acquirer_data)

    if not prompt:
        return {"error": f"No prompt builder defined for chart title '{chart_id}'."}

    input_tokens = count_tokens(prompt)
    try:
        response = generate_grok_insight(prompt, return_usage=True)
        insight = response['text']
        output_tokens = response['usage']['completion_tokens']
        total_tokens = response['usage']['total_tokens']
    except Exception as e:
        return {
            "chart_id": chart_id,
            "insight": f"Insight generation failed: {str(e)}"
        }

    return {
        "chart_id": chart_id,
        "insight": insight,
        "token_usage": {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens
        }
    }
