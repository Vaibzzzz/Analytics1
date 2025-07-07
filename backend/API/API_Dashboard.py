from fastapi import APIRouter
from KPI.KPI_Dashboard import get_dashboard_data

router = APIRouter()

@router.get("/dashboard", summary="Get all dashboard metrics & charts")
def dashboard():
    return get_dashboard_data()