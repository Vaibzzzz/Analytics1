from datetime import date
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges, pct_diff, fetch_one
from typing import Optional, Tuple

engine = get_engine()

def get_operational_efficiency_data(
    filter_type: str = "YTD",
    custom: Optional[Tuple[date, date]] = None
) -> dict:
    """
    Returns operational efficiency KPI metrics and chart data based on the selected date range filter.
    Uses live_transactions table for all lookups.
    """
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)
    metrics, charts = [], []

    with engine.connect() as conn:
        # ─── 1. Transaction Success Rate (%) ──────────────────────────
        total_sql = """
            SELECT COUNT(*)::float
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
        """
        success_sql = """
            SELECT COUNT(*)::float
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
               AND t.payment_successful = true
        """

        curr_total   = fetch_one(conn, total_sql,   {"s": start, "e": end}) or 1
        prev_total   = fetch_one(conn, total_sql,   {"s": comp_start, "e": comp_end}) or 1
        curr_success = fetch_one(conn, success_sql, {"s": start, "e": end})
        prev_success = fetch_one(conn, success_sql, {"s": comp_start, "e": comp_end})

        curr_rate = round(curr_success / curr_total * 100, 2)
        prev_rate = round(prev_success / prev_total * 100, 2)
        metrics.append({
            "title": "Transaction Success Rate (%)",
            "value": curr_rate,
            "diff":  pct_diff(curr_rate, prev_rate)
        })

        # ─── 2. Processing Partner Efficiency ─────────────────────────
        rows = conn.execute(text("""
            SELECT
              a.name AS acquirer_name,
              COUNT(*) FILTER (WHERE t.payment_successful = true)::float AS success_count,
              COUNT(*)::float                               AS total_txns,
              ROUND(COUNT(*) FILTER (WHERE t.payment_successful = true) * 100.0
                    / NULLIF(COUNT(*), 0), 2)               AS success_rate
            FROM live_transactions t
            JOIN acquirer a ON t.acquirer_id = a.id
            WHERE t.created_at::date BETWEEN :s AND :e
            GROUP BY a.name
        """), {"s": start, "e": end}).mappings().all()

        charts.append({
            "title": "Processing Partner Efficiency",
            "type": "double_bar_dual_axis",
            "x": [r["acquirer_name"] for r in rows],
            "yAxis": [
                {"name": "Success Rate (%)", "type": "value", "min": 0,   "max": 100,     "position": "left"},
                {"name": "Total Transactions", "type": "value",            "position": "right"},
            ],
            "series": [
                {
                  "name": "Success Rate (%)",
                  "type": "bar",
                  "data": [r["success_rate"] for r in rows],
                  "yAxisIndex": 0
                },
                {
                  "name": "Total Transactions",
                  "type": "bar",
                  "data": [r["total_txns"] for r in rows],
                  "yAxisIndex": 1
                }
            ]
        })

        # ─── 3. Payment Method Distribution ───────────────────────────
        rows = conn.execute(text("""
            SELECT
              t.credit_card_type AS credit_card_type,
              COUNT(*) FILTER (WHERE t.funding_source = 'CREDIT')::float  AS credit_count,
              COUNT(*) FILTER (WHERE t.funding_source = 'DEBIT')::float   AS debit_count,
              COUNT(*) FILTER (WHERE t.funding_source = 'PREPAID')::float AS prepaid_count
            FROM live_transactions t
            WHERE t.created_at::date BETWEEN :s AND :e
            GROUP BY t.credit_card_type
        """), {"s": start, "e": end}).mappings().all()

        charts.append({
            "title": "Payment Method Distribution",
            "type": "stacked_bar",
            "x": [r["credit_card_type"] for r in rows],
            "series": [
                {"name": "Credit Funded", "data": [r["credit_count"]  for r in rows]},
                {"name": "Debit Funded",  "data": [r["debit_count"]   for r in rows]},
                {"name": "Prepaid Funded","data": [r["prepaid_count"] for r in rows]},
            ]
        })

    return {
        "metrics": metrics,
        "charts":  charts
    }
