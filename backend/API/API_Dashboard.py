from fastapi import APIRouter
from KPI.KPI_Dashboard import fetch_dashboard_data

router = APIRouter()

@router.get("/dashboard", summary="Get all dashboard metrics & charts")
def dashboard():
    return fetch_dashboard_data()