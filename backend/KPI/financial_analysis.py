from datetime import date
from typing import Optional, Tuple
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges, pct_diff, fetch_one
import statistics

engine = get_engine()

def get_financial_performance_data(filter_type: str = 'YTD',
                                   custom: Optional[Tuple[date, date]] = None) -> dict:
    """
    Returns financial KPI metrics, chart data, and statistical insight data 
    for AI-based insight generation.
    """
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)
    metrics, charts = [], []
    insight_data = {}

    with engine.connect() as conn:
        # ─── SQL Templates ───────────────────────────────────────────────────────
        sql_sum = """
            SELECT COALESCE(SUM(usd_value), 0)
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
        """
        sql_count = """
            SELECT COUNT(*)::float
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
        """
        sql_avg = """
            SELECT COALESCE(AVG(usd_value), 0)
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
        """

        # ─── Total Transaction Volume ────────────────────────────────────────────
        curr_vol = fetch_one(conn, sql_sum, {'s': start, 'e': end})
        prev_vol = fetch_one(conn, sql_sum, {'s': comp_start, 'e': comp_end})
        if filter_type == 'Daily':  prev_vol /= 7
        if filter_type == 'Weekly': prev_vol /= 4
        metrics.append({
            'title': 'Total Transaction Volume',
            'value': round(curr_vol, 2),
            'diff': pct_diff(curr_vol, prev_vol)
        })

        # ─── Total Transactions ──────────────────────────────────────────────────
        curr_cnt = fetch_one(conn, sql_count, {'s': start, 'e': end})
        prev_cnt = fetch_one(conn, sql_count, {'s': comp_start, 'e': comp_end})
        if filter_type == 'Daily':  prev_cnt /= 7
        if filter_type == 'Weekly': prev_cnt /= 4
        metrics.append({
            'title': 'Total Transactions',
            'value': int(curr_cnt),
            'diff': pct_diff(curr_cnt, prev_cnt)
        })

        # ─── Average Transaction Value ───────────────────────────────────────────
        if filter_type == 'Daily':
            curr_avg = fetch_one(conn, """
                SELECT COALESCE(AVG(usd_value), 0)
                  FROM live_transactions t
                 WHERE t.created_at::date = :d
            """, {'d': start})
            prev_avg = fetch_one(conn, sql_avg, {'s': comp_start, 'e': comp_end})
        else:
            curr_avg = fetch_one(conn, sql_avg, {'s': start, 'e': end})
            prev_avg = fetch_one(conn, sql_avg, {'s': comp_start, 'e': comp_end})

        metrics.append({
            'title': 'Average Transaction Value',
            'value': round(curr_avg, 2),
            'diff': pct_diff(curr_avg, prev_avg)
        })

        # ─── Sales by Currency (Pie Chart + Historical) ──────────────────────────
        current_rows = conn.execute(text("""
            SELECT t.transaction_currency AS name,
                   SUM(t.usd_value) AS total_usd
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
             GROUP BY t.transaction_currency
        """), {'s': start, 'e': end}).mappings().all()

        prev_rows = conn.execute(text("""
            SELECT t.transaction_currency AS name,
                   SUM(t.usd_value) AS total_usd
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
             GROUP BY t.transaction_currency
        """), {'s': comp_start, 'e': comp_end}).mappings().all()

        total_usd_current = sum(r['total_usd'] for r in current_rows) or 1
        total_usd_prev = sum(r['total_usd'] for r in prev_rows) or 1

        sales_pie = {
            'title': 'Sales by Currency',
            'type': 'pie',
            'value': total_usd_current,
            'hist_value': total_usd_prev,
            'pct_change': pct_diff(total_usd_current, total_usd_prev),
            'change_direction': 'increased' if total_usd_current >= total_usd_prev else 'decreased',
            'data': [
                {
                    'name': r['name'],
                    'value': round(r['total_usd'] / total_usd_current * 100, 1)
                }
                for r in current_rows
            ]
        }
        charts.append(sales_pie)

        # ─── Processing Fee Analysis (Bar + Historical + Z-Score) ────────────────
        current_proc_rows = conn.execute(text("""
            SELECT a.name AS acquirer,
                   SUM((t.pricing_ic/100.0)*t.usd_value + t.gateway_fee) AS total_fees,
                   SUM(t.usd_value) AS total_amt
              FROM live_transactions t
              JOIN acquirer a ON t.acquirer_id = a.id
             WHERE t.created_at::date BETWEEN :s AND :e
             GROUP BY a.name
        """), {'s': start, 'e': end}).mappings().all()

        prev_proc_rows = conn.execute(text("""
            SELECT a.name AS acquirer,
                   SUM((t.pricing_ic/100.0)*t.usd_value + t.gateway_fee) AS total_fees,
                   SUM(t.usd_value) AS total_amt
              FROM live_transactions t
              JOIN acquirer a ON t.acquirer_id = a.id
             WHERE t.created_at::date BETWEEN :s AND :e
             GROUP BY a.name
        """), {'s': comp_start, 'e': comp_end}).mappings().all()

        current_fees = [
            (r['total_fees'] / r['total_amt']) * 100 for r in current_proc_rows if r['total_amt']
        ]
        prev_fees = [
            (r['total_fees'] / r['total_amt']) * 100 for r in prev_proc_rows if r['total_amt']
        ]

        curr_mean = round(statistics.mean(current_fees), 4) if current_fees else 0
        prev_mean = round(statistics.mean(prev_fees), 4) if prev_fees else 0
        z_score = (
            round((curr_mean - statistics.mean(prev_fees)) / statistics.stdev(prev_fees), 2)
            if len(prev_fees) > 1 and statistics.stdev(prev_fees) != 0 else None
        )

        proc_chart = {
            'title': 'Processing Fee Analysis',
            'type': 'horizontal_bar',
            'value': curr_mean,
            'hist_value': prev_mean,
            'pct_change': pct_diff(curr_mean, prev_mean),
            'change_direction': 'increased' if curr_mean >= prev_mean else 'decreased',
            'z_score': z_score,
            'x': current_fees,
            'y': [r['acquirer'] for r in current_proc_rows],
            'series': [{
                'name': 'Fee % of Volume',
                'data': current_fees
            }]
        }
        charts.append(proc_chart)

        # ─── Gateway Fee % Insight Data ──────────────────────────────────────────
        hist_rows = conn.execute(text("""
            SELECT created_at::date AS day,
                   SUM(gateway_fee) AS total_fee,
                   SUM(usd_value) AS total_amt
              FROM live_transactions
             WHERE created_at::date BETWEEN CURRENT_DATE - INTERVAL '8 days' AND CURRENT_DATE - INTERVAL '1 day'
             GROUP BY created_at::date
             ORDER BY day
        """)).mappings().all()

        gateway_hist_values = [
            (r['total_fee'] / r['total_amt']) * 100
            for r in hist_rows if r['total_amt']
        ]

        yesterday_val = conn.execute(text("""
            SELECT SUM(gateway_fee) AS total_fee,
                   SUM(usd_value) AS total_amt
              FROM live_transactions
             WHERE created_at::date = CURRENT_DATE - INTERVAL '1 day'
        """)).mappings().first()

        gateway_yesterday_pct = (
            (yesterday_val['total_fee'] / yesterday_val['total_amt']) * 100
            if yesterday_val and yesterday_val['total_amt']
            else 0
        )

        insight_data['gateway_fee_pct'] = {
            'yesterday': round(gateway_yesterday_pct, 4),
            'historical': [round(v, 4) for v in gateway_hist_values]
        }

        # ─── Processing Fee % Insight Data ───────────────────────────────────────
        hist_rows = conn.execute(text("""
            SELECT created_at::date AS day,
                   SUM((pricing_ic / 100.0) * usd_value + gateway_fee) AS total_fee,
                   SUM(usd_value) AS total_amt
              FROM live_transactions
             WHERE created_at::date BETWEEN CURRENT_DATE - INTERVAL '8 days' AND CURRENT_DATE - INTERVAL '1 day'
             GROUP BY created_at::date
             ORDER BY day
        """)).mappings().all()

        processing_hist_values = [
            (r['total_fee'] / r['total_amt']) * 100
            for r in hist_rows if r['total_amt']
        ]

        yesterday_val = conn.execute(text("""
            SELECT SUM((pricing_ic / 100.0) * usd_value + gateway_fee) AS total_fee,
                   SUM(usd_value) AS total_amt
              FROM live_transactions
             WHERE created_at::date = CURRENT_DATE - INTERVAL '1 day'
        """)).mappings().first()

        processing_yesterday_pct = (
            (yesterday_val['total_fee'] / yesterday_val['total_amt']) * 100
            if yesterday_val and yesterday_val['total_amt']
            else 0
        )

        insight_data['processing_fee_pct'] = {
            'yesterday': round(processing_yesterday_pct, 4),
            'historical': [round(v, 4) for v in processing_hist_values]
        }

    return {
        'metrics': metrics,
        'charts': charts,
        'insight_data': insight_data
    }
