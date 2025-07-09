from fastapi import APIRouter
from KPI.DemoGraphic import get_demo_kpi_data

router = APIRouter()

@router.get("/demographic")
def demographic_kpis():
    return get_demo_kpi_data()
