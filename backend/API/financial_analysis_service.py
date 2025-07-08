from fastapi import APIRouter, Query
from datetime import date
from KPI.financial_analysis import get_financial_performance_data

router = APIRouter()

@router.get("/financial-performance")
def financial_performance(
    filter_type: str = Query(default="YTD", description="Filter type like Today, Daily, Weekly, MTD, etc."),
    start: date = Query(default=None),
    end: date = Query(default=None)
):
    custom = (start, end) if start and end else None
    return get_financial_performance_data(filter_type, custom)
