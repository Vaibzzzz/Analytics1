from fastapi import APIRouter, Query
from datetime import date
from KPI.risk_and_fraud_management import get_risk_and_fraud_data

router = APIRouter()

@router.get("/risk-and-fraud")
def risk_and_fraud_management(
    filter_type: str = Query(default="YTD", description="Filter type like Today, Daily, Weekly, MTD, etc."),
    start: date = Query(default=None),
    end: date = Query(default=None)
):
    custom = (start, end) if start and end else None
    return get_risk_and_fraud_data(filter_type, custom)