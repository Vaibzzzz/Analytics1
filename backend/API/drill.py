# in app/routes/drill.py

from fastapi import APIRouter, Query, HTTPException
from enum import Enum
from datetime import date
from typing import Optional, Tuple
from KPI.drill_service import fetch_drill_data

class DrillLevel(str, Enum):
    DRILL_LVL1 = "DRILL_LVL1"
    DRILL_LVL2 = "DRILL_LVL2"

router = APIRouter()

@router.get("/drill", summary="Get chart drill-down data")
def drill(
    chartKey:       str,
    level:          DrillLevel,
    dimension:      str,
    dimension1:    Optional[str] = Query(
                    None,
                    description="Dimension from first-level drill (needed for DRILL_LVL2)"
    ),
    # this is the new filter for your second-level grouping 
    parentValue:    Optional[str] = Query(
                        None,
                        description="Value from first-level drill (needed for DRILL_LVL2)"
                    ),
    baseValue:      str = Query(
                        ...,
                        description="Value for the chart's base dimension (e.g. currency or acquirer name)"
                    ),
    filterType:     str = 'YTD',
    custom_start:   Optional[date] = None,
    custom_end:     Optional[date] = None,
):
    custom: Optional[Tuple[date, date]] = (
        (custom_start, custom_end) if custom_start and custom_end else None
    )

    # level-2 _must_ have a parentValue
    if level == DrillLevel.DRILL_LVL2 and parentValue is None:
        raise HTTPException(
            status_code=400,
            detail="parentValue query-param is required for DRILL_LVL2"
        )

    try:
        return fetch_drill_data(
            chartKey,
            level.value,
            dimension,
            dimension1,
            baseValue,     # use this to filter the *base* dimension
            parentValue,   # None for L1, required for L2
            filter_type=filterType,
            custom=custom
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
