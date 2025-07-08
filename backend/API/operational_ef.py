from fastapi import APIRouter, Query
from KPI.operational_efficiency import get_operational_efficiency_data

router = APIRouter()

@router.get("/operational-efficiency")
def operational_efficiency(
    range: str = Query(default="YTD", description="Time range filter (e.g., today, yesterday, daily, weekly, mtd, ytd)"),
    chart_index: int = Query(default=None, description="Optional index of chart to return")
):
    # Normalize input to uppercase to match what's expected in get_date_ranges
    filter_type = range.strip().upper()

    try:
        data = get_operational_efficiency_data(filter_type=filter_type)
    except ValueError as e:
        return {"error": str(e)}

    if chart_index is not None:
        charts = data.get("charts", [])
        if 0 <= chart_index < len(charts):
            return {"chart": charts[chart_index]}
        return {"error": "Chart index out of range"}

    return data
