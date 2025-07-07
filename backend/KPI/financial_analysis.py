from fastapi import APIRouter
from API.financial_analysis_service import get_financial_analysis_data

router = APIRouter()

@router.get("/financial-analysis", summary="Get financial analysis data")
def financial_analysis():
    return get_financial_analysis_data()