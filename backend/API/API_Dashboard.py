from fastapi import APIRouter
from KPI.KPI_Dashboard import fetch_dashboard_data

router = APIRouter()

@router.get("/dashboard", summary="Get all dashboard metrics & charts")
def dashboard():
    """
    Retrieves the combined metrics and charts for the main dashboard.
    This endpoint does not accept any time-filter parameters.
    """
    return fetch_dashboard_data()
