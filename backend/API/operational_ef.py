from fastapi import APIRouter, Query
from KPI.operational_efficiency import get_operational_efficiency_data
from datetime import date
from typing import Optional, Tuple

router = APIRouter()

@router.get("/operational-efficiency")
def operational_efficiency(
    filter_type: str = Query(default="YTD", description="Time range filter (e.g., today, yesterday, daily, weekly, mtd, ytd)"),
    start: date = Query(None),
    end:   date = Query(None)
):
    
    custom = (start, end) if start and end else None
    return get_operational_efficiency_data(filter_type, custom)