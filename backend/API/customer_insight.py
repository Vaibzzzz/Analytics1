from fastapi import APIRouter, Query
from datetime import date
from typing import Optional, Tuple

from KPI.customer_insight import get_customer_insights_data

router = APIRouter()

@router.get(
    "/customer-insights",
    summary="Get Customer Insights metrics and charts",
    description=(
        "Returns customer insights KPIs and chart data for the given time filter. "
        "Supported filters: Today, Yesterday, Daily, Weekly, MTD, Monthly, YTD, custom. "
        "For custom, also supply start and end dates in YYYY-MM-DD format."
    )
)
def customer_insights(
    filter_type: str = Query(
        "YTD",
        regex="^(Today|Yesterday|Daily|Weekly|MTD|Monthly|YTD|custom)$",
        description="Predefined time filter"
    ),
    start: date = Query(
        None,
        description="Start date for custom range (YYYY-MM-DD)"
    ),
    end: date = Query(
        None,
        description="End date for custom range (YYYY-MM-DD)"
    )
):
    """
    Fetches:
      - Unique Payment Methods (with % change vs. previous period)
      - Transactions by Acquirer (bar chart)
      - Transaction Type Distribution (bar chart)
      - Payment Creation Patterns (bar chart)
    """
    custom_range: Optional[Tuple[date, date]] = (start, end) if start and end else None
    return get_customer_insights_data(filter_type, custom_range)

