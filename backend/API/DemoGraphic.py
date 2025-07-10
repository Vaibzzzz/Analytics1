from fastapi import APIRouter
from KPI.DemoGraphic import get_demo_kpi_data
from fastapi import Query
from datetime import date
from typing import Optional, Tuple

router = APIRouter()

@router.get("/demographic")
def demographic_kpis(filter_type: str = Query(default="YTD", description="Filter type like Today, Daily, Weekly, MTD, etc."),
    start: date = Query(default=None),
    end: date = Query(default=None)
):
    custom = (start, end) if start and end else None
    return get_demo_kpi_data(filter_type, custom)