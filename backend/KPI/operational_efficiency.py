from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import text
from DB.connector import get_engine

engine = get_engine()


def get_date_ranges(filter_type: str, custom: tuple[date, date] = None):
    base = datetime(2023, 12, 30, 23, 56, 0)  # your fixed base date
    today_date = base.date()

    if filter_type == 'TODAY':
        start = end = today_date
        comp_end = today_date - timedelta(days=1)
        comp_start = comp_end

    elif filter_type == 'YESTERDAY':
        start = end = today_date - timedelta(days=1)
        comp_end = start - timedelta(days=1)
        comp_start = comp_end

    elif filter_type == 'DAILY':
        end = today_date - timedelta(days=1)
        start = end
        comp_end = end - timedelta(days=1)
        comp_start = comp_end - timedelta(days=6)

    elif filter_type == 'WEEKLY':
        end = today_date - timedelta(days=1)
        start = end - timedelta(days=6)
        comp_end = start - timedelta(days=1)
        comp_start = comp_end - timedelta(days=27)

    elif filter_type == 'MTD':
        start = today_date.replace(day=1)
        end = today_date
        prev_month_end = start - timedelta(days=1)
        comp_start = prev_month_end.replace(day=1)
        comp_end = prev_month_end

    elif filter_type == 'MONTHLY':
        end = today_date
        start = (base - relativedelta(months=3) + timedelta(days=1)).date()
        comp_end = (base - relativedelta(months=3)).date()
        comp_start = (base - relativedelta(months=6) + timedelta(days=1)).date()

    elif filter_type == 'YTD':
        start = today_date.replace(month=1, day=1)
        end = today_date
        comp_start = start.replace(year=start.year - 1)
        comp_end = comp_start + (end - start)


    elif filter_type == 'custom' and custom:
        start, end = custom
        length = end - start
        comp_end = start - timedelta(days=1)
        comp_start = comp_end - length

    else:
        raise ValueError(f"Unsupported filter type: {filter_type}")

    return start, end, comp_start, comp_end



def fetch_one(conn, query: str, params: dict):
    return float(conn.execute(text(query), params).scalar() or 0.0)


def pct_diff(current: float, previous: float) -> float:
    if previous:
        return round((current - previous) / previous * 100, 2)
    return 0.0


def get_operational_efficiency_data(filter_type: str = "YTD", custom: tuple[date, date] = None):
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)
    metrics, charts = [], []

    with engine.connect() as conn:
        # ─── 1. Transaction Success Rate ──────────────────────
        total_sql = "SELECT COUNT(*) FROM transaction WHERE date_time::date BETWEEN :s AND :e"
        success_sql = "SELECT COUNT(*) FROM transaction WHERE date_time::date BETWEEN :s AND :e AND payment_successful = 'true'"

        curr_total = fetch_one(conn, total_sql, {"s": start, "e": end}) or 1
        prev_total = fetch_one(conn, total_sql, {"s": comp_start, "e": comp_end}) or 1

        curr_success = fetch_one(conn, success_sql, {"s": start, "e": end})
        prev_success = fetch_one(conn, success_sql, {"s": comp_start, "e": comp_end})

        curr_rate = round(curr_success / curr_total * 100, 2)
        prev_rate = round(prev_success / prev_total * 100, 2)

        metrics.append({
            "title": "Transaction Success Rate (%)",
            "value": curr_rate,
            "diff": pct_diff(curr_rate, prev_rate)
        })


        # ─── 2. Processing Partner Efficiency ─────────────────
        rows = conn.execute(text("""
            SELECT 
                a.name AS acquirer_name,
                COUNT(*) FILTER (WHERE t.payment_successful = 'true') AS success_count,
                COUNT(*) AS total_txns,
                ROUND(COUNT(*) FILTER (WHERE t.payment_successful = 'true') * 100.0 / NULLIF(COUNT(*), 0), 2) AS success_rate
            FROM transaction t
            JOIN acquirer a ON t.acquirer_id = a.id
            WHERE t.date_time::date BETWEEN :s AND :e
            GROUP BY a.name
        """), {"s": start, "e": end}).mappings().all()

        charts.append({
            "title": "Processing Partner Efficiency",
            "type": "double_bar_dual_axis",
            "x": [r["acquirer_name"] for r in rows],
            "yAxis": [
                {"name": "Success Rate (%)", "type": "value", "min": 0, "max": 100, "position": "left"},
                {"name": "Total Transactions", "type": "value", "position": "right"},
            ],
            "series": [
                {"name": "Success Rate (%)", "type": "bar", "data": [r["success_rate"] for r in rows], "yAxisIndex": 0},
                {"name": "Total Transactions", "type": "bar", "data": [r["total_txns"] for r in rows], "yAxisIndex": 1},
            ]
        })

        # ─── 3. Payment Method Distribution ───────────────────
        rows = conn.execute(text("""
            SELECT credit_card_type,
                   COUNT(*) FILTER (WHERE funding_source = 'CREDIT') AS credit_count,
                   COUNT(*) FILTER (WHERE funding_source = 'DEBIT') AS debit_count,
                   COUNT(*) FILTER (WHERE funding_source = 'PREPAID') AS prepaid_count
            FROM transaction
            WHERE date_time::date BETWEEN :s AND :e
            GROUP BY credit_card_type
        """), {"s": start, "e": end}).mappings().all()

        charts.append({
            "title": "Payment Method Distribution",
            "type": "stacked_bar",
            "x": [r["credit_card_type"] for r in rows],
            "series": [
                {"name": "Credit Funded", "data": [r["credit_count"] for r in rows]},
                {"name": "Debit Funded", "data": [r["debit_count"] for r in rows]},
                {"name": "Prepaid Funded", "data": [r["prepaid_count"] for r in rows]},
            ]
        })

    return {"metrics": metrics, "charts": charts}
