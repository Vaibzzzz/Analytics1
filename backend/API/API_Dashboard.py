from fastapi import APIRouter
from KPI.KPI_Dashboard import get_transaction_performance_data

router = APIRouter()

@router.get("/generate_kpis")
def generate_kpis():
    """
    Returns pre-defined KPIs and charts for transaction analysis.
    """
    result = get_transaction_performance_data()
    return result
