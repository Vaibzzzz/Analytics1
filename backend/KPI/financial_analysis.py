from datetime import date
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges, pct_diff, fetch_one
from typing import Optional

# Create a connection to the database
engine = get_engine()

def get_financial_performance_data(filter_type: str = 'YTD',
                                   custom: Optional[tuple[date, date]] = None) -> dict:
    """
    Main function to gather KPI metrics and chart data.
    Returns a dict with:
      - metrics: list of {title, value, diff}
      - charts:  list of chart definitions
    """
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)
    metrics, charts = [], []

    with engine.connect() as conn:
        # Common SQL fragments to get sums, counts, averages
        sql_sum   = "SELECT COALESCE(SUM(usd_value),0)  FROM transaction WHERE date_time::date BETWEEN :s AND :e"
        sql_count = "SELECT COUNT(*)::float               FROM transaction WHERE date_time::date BETWEEN :s AND :e"
        sql_avg   = "SELECT COALESCE(AVG(usd_value),0) FROM transaction WHERE date_time::date BETWEEN :s AND :e"

        # ─── Total Transaction Volume ────────────────────────────────
        curr_vol = fetch_one(conn, sql_sum,   {'s': start, 'e': end})
        prev_vol = fetch_one(conn, sql_sum,   {'s': comp_start, 'e': comp_end})
        # For Daily and Weekly, compare against averaged past data
        if filter_type == 'Daily':   prev_vol /= 7
        if filter_type == 'Weekly':  prev_vol /= 4
        metrics.append({
            'title': 'Total Transaction Volume',
            'value': round(curr_vol, 2),
            'diff': pct_diff(curr_vol, prev_vol)
        })

        # ─── Total Transactions ──────────────────────────────────────
        curr_cnt = fetch_one(conn, sql_count, {'s': start, 'e': end})
        prev_cnt = fetch_one(conn, sql_count, {'s': comp_start, 'e': comp_end})
        if filter_type == 'Daily':   prev_cnt /= 7
        if filter_type == 'Weekly':  prev_cnt /= 4
        metrics.append({
            'title': 'Total Transactions',
            'value': int(curr_cnt),
            'diff': pct_diff(curr_cnt, prev_cnt)
        })

        # ─── Average Transaction Value ───────────────────────────────
        if filter_type == 'Daily':
            # Yesterday's average vs. prior week average
            curr_avg = fetch_one(conn,
                                 "SELECT COALESCE(AVG(usd_value),0) "
                                 "FROM transaction WHERE date_time::date = :d",
                                 {'d': start})
            prev_avg = fetch_one(conn, sql_avg, {'s': comp_start, 'e': comp_end})
        else:
            curr_avg = fetch_one(conn, sql_avg,   {'s': start, 'e': end})
            prev_avg = fetch_one(conn, sql_avg,   {'s': comp_start, 'e': comp_end})
        metrics.append({
            'title': 'Average Transaction Value',
            'value': round(curr_avg, 2),
            'diff': pct_diff(curr_avg, prev_avg)
        })

        # ─── Sales By Currency (Pie Chart Data) ──────────────────────
        rows = conn.execute(text(
            "SELECT transaction_currency AS name, SUM(usd_value) AS total_usd "
            "FROM transaction "
            "WHERE date_time::date BETWEEN :s AND :e "
            "GROUP BY transaction_currency"
        ), {'s': start, 'e': end}).mappings().all()

        total_usd = sum(r['total_usd'] for r in rows) or 1
        charts.append({
            'title': 'Sales by Currency',
            'type':  'pie',
            'data': [
                {
                    'name':  r['name'],
                    'value': round(r['total_usd'] / total_usd * 100, 1)
                } for r in rows
            ]
        })

        # ─── Processing Fee Analysis (Bar Chart Data) ───────────────
        rows = conn.execute(text("""
            SELECT
                a.name AS acquirer,
                SUM((t.pricing_ic/100.0) * t.usd_value + t.gateway_fee) AS total_fees,
                SUM(t.usd_value)                             AS total_amt
            FROM transaction t
            JOIN acquirer a ON t.acquirer_id = a.id
            WHERE date_time::date BETWEEN :s AND :e
            GROUP BY a.name
            ORDER BY
                SUM((t.pricing_ic/100.0) * t.usd_value + t.gateway_fee)
                / NULLIF(SUM(t.usd_value),0)
                DESC
        """), {'s': start, 'e': end}).mappings().all()

        charts.append({
            'title': 'Processing Fee Analysis',
            'type':  'bar',
            'x':     [r['acquirer'] for r in rows],
            'y':     [
                round((r['total_fees'] / r['total_amt']) * 100, 2) if r['total_amt'] else 0
                for r in rows
            ]
        })

    # Return the assembled metrics and chart configurations
    return {'metrics': metrics, 'charts': charts}
