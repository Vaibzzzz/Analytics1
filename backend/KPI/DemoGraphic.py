from datetime import date
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges, fetch_one
from typing import Optional, Tuple

engine = get_engine()
MERCHANT_ID = 26  # Hardcoded merchant ID

def get_demo_kpi_data(
    filter_type: str = "YTD",
    custom: Optional[Tuple[date, date]] = None
) -> dict:
    """
    Returns demographic KPI metrics and chart data based on the selected date range filter.
    Uses live_transactions table for all lookups.
    """
    # Determine the current and comparison windows
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)
    metrics, charts = [], []

    with engine.connect() as conn:
        # ─── Metric: Unique countries where merchant operates ─────────────
        country_count = fetch_one(
            conn,
            """
            SELECT COUNT(DISTINCT t.country_code)
              FROM live_transactions t
             WHERE t.merchant_id = :m_id
               AND t.created_at::date BETWEEN :s AND :e
            """,
            {"m_id": MERCHANT_ID, "s": start, "e": end}
        )
        metrics.append({
            "title": "Countries Operational",
            "value": int(country_count)
        })

        # ─── Metric: Unique US states/provinces ──────────────────────────
        state_count = fetch_one(
            conn,
            """
            SELECT COUNT(DISTINCT t.state_or_province)
              FROM live_transactions t
             WHERE t.merchant_id = :m_id
               AND t.created_at::date BETWEEN :s AND :e
            """,
            {"m_id": MERCHANT_ID, "s": start, "e": end}
        )
        metrics.append({
            "title": "States Operational",
            "value": int(state_count)
        })

        # ─── Chart 1: Sales by Region (US/UK only) ───────────────────────
        region_rows = conn.execute(text("""
            SELECT t.country_code, SUM(t.usd_value) AS total_sales
              FROM live_transactions t
             WHERE t.merchant_id = :m_id
               AND t.created_at::date BETWEEN :s AND :e
               AND t.country_code IN ('US','GB')
             GROUP BY t.country_code
             ORDER BY total_sales DESC
        """), {"m_id": MERCHANT_ID, "s": start, "e": end}).mappings().all()

        charts.append({
            "title": "Sales by Region",
            "type":  "bar",
            "x":     [r["country_code"] for r in region_rows],
            "y":     [round(r["total_sales"], 2) for r in region_rows]
        })

        # ─── Chart 2: Success Rate by Country ────────────────────────────
        perf_rows = conn.execute(text("""
            SELECT
              t.country_code,
              COUNT(*) FILTER (WHERE t.payment_successful = true)::float
                / NULLIF(COUNT(*),0) * 100 AS success_rate
            FROM live_transactions t
           WHERE t.merchant_id = :m_id
             AND t.created_at::date BETWEEN :s AND :e
           GROUP BY t.country_code
           ORDER BY success_rate DESC
        """), {"m_id": MERCHANT_ID, "s": start, "e": end}).mappings().all()

        charts.append({
            "title": "Success Rate by Country",
            "type":  "bar",
            "x":     [r["country_code"] for r in perf_rows],
            "y":     [round(r["success_rate"], 2) for r in perf_rows]
        })

        # ─── Chart 3: Transactions by Card Issuing Country (Pie) ────────
        pie_rows = conn.execute(text("""
            SELECT
              t.issuer_country_code AS name,
              COUNT(*)                   AS txn_count
            FROM live_transactions t
           WHERE t.merchant_id = :m_id
             AND t.created_at::date BETWEEN :s AND :e
             AND t.issuer_country_code IS NOT NULL
           GROUP BY t.issuer_country_code
        """), {"m_id": MERCHANT_ID, "s": start, "e": end}).mappings().all()

        total_txns = sum(r["txn_count"] for r in pie_rows) or 1
        charts.append({
            "title": "Transactions by Card Issuing Country",
            "type":  "pie",
            "data": [
                {
                    "name":  r["name"],
                    "value": round(r["txn_count"] / total_txns * 100, 1)
                }
                for r in pie_rows
            ]
        })

        # ─── Chart 4: Transactions by US State ──────────────────────────
        map_rows = conn.execute(text("""
            SELECT
              t.state_or_province,
              COUNT(*) AS txn_count
            FROM live_transactions t
           WHERE t.merchant_id = :m_id
             AND t.created_at::date BETWEEN :s AND :e
             AND t.country_code = 'US'
           GROUP BY t.state_or_province
           ORDER BY txn_count DESC
        """), {"m_id": MERCHANT_ID, "s": start, "e": end}).mappings().all()

        charts.append({
            "title": "Transactions by State or Province",
            "type":  "horizontal_bar",
            "x":     [r["txn_count"]           for r in map_rows],
            "y":     [r["state_or_province"]   for r in map_rows],
            "series": [{
                "name": "Transactions",
                "data": [r["txn_count"] for r in map_rows]
            }]
        })

    return {
        "metrics": metrics,
        "charts":  charts
    }
