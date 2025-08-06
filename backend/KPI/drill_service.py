from datetime import date
from typing import Optional, Tuple, Dict, Any

from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges
from KPI.chart_configs import (
    CHART_BASE_DIMENSION,
    CHART_METRICS,
    drill_configs,
)

# Track last drill context (if multi-step session needed)
_last_drill_dimension1: Optional[str] = None
_last_drill_base_value: Optional[str] = None


# in app/services/drill_service.py

def fetch_drill_data(
    chart_key: str,
    level: str,
    dimension: str,
    dimension1: str,
    base_value: str,
    parent_value: Optional[str] = None,
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None,
) -> Dict[str, Any]:
    # 1) time window
    start, end, _, _ = get_date_ranges(filter_type, custom)

    # 2) config lookup
    cfg = drill_configs.get(level)
    if not cfg:
        raise ValueError(f"Unknown drill level {level}")

    base_dim   = CHART_BASE_DIMENSION[chart_key]
    metric_sql = CHART_METRICS[chart_key]
    joins = []
    if base_dim.startswith("a.") or dimension == "acquirer_name":
        joins.append("JOIN acquirer a ON t.acquirer_id = a.id")
    join_sql = "\n".join(joins)

    # 3) build SQL + params
    if level == "DRILL_LVL1":
        # single filter: base_dim = base_value
        sql = f"""
            SELECT {metric_sql}       AS value,
                   {dimension}         AS name
              FROM live_transactions t
             {join_sql}
             WHERE t.created_at::date BETWEEN :s AND :e
               AND {base_dim} = :base_value
             GROUP BY {dimension}
        """
        params = {"s": start, "e": end, "base_value": base_value}

    else:  # DRILL_LVL2
        # must have a parent_value to filter the first drill
        if parent_value is None:
            raise ValueError("parent_value is required for level 2")
        sql = f"""
            SELECT {metric_sql}       AS value,
                   {dimension}         AS name
              FROM live_transactions t
             {join_sql}
             WHERE t.created_at::date BETWEEN :s AND :e
               AND {base_dim}      = :base_value
               AND {dimension1}     = :parent_value
             GROUP BY {dimension}
        """
        params = {
            "s":           start,
            "e":           end,
            "base_value":  base_value,
            "parent_value": parent_value,
        }

    # 4) execute + format
    with get_engine().connect() as conn:
        rows = conn.execute(text(sql), params).mappings().all()

    data = [{"name": r["name"], "value": float(r["value"])} for r in rows]
    title = cfg["title"].format(
        dimension_label  = dimension.replace("_"," ").title(),
        base_value       = base_value,
        lvl1_value       = parent_value or "",
        lvl1_field_label = dimension.replace("_"," ").title(),
    )

    return {
        "chartKey":           chart_key,
        "title":              title,
        "type":               cfg["type"].value,
        "data":               data,
        "drillable":          cfg["drillable"],
        "nextChart":          cfg["next_chart"],
        "start":              start,
        "end":                end,
        "baseFilteredField":  base_dim,
        "baseFilteredValue":  base_value,
    }
