from datetime import date, datetime, timedelta
from typing import Optional, Tuple
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges, pct_diff, fetch_one
from KPI.utils.stat_tests import compare_to_historical_single_point

import statistics

engine = get_engine()

def get_financial_performance_data(
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None
) -> dict:
    """
    Returns financial KPI metrics, chart data, and insight_data
    (yesterday + historical series) for gateway & processing fees.
    """
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)
    metrics, charts, insight_data = [], [], {}

    # Common SQL templates
    SQL = {
        'sum':   """
            SELECT COALESCE(SUM(usd_value), 0)::float AS val
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
        """,
        'count': """
            SELECT COUNT(*)::float AS val
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
        """,
        'avg':   """
            SELECT COALESCE(AVG(usd_value), 0)::float AS val
              FROM live_transactions t
             WHERE t.created_at::date BETWEEN :s AND :e
        """
    }

    with engine.connect() as conn:
        # ─── Helpers ───────────────────────────────────────────
        def run_agg(sql_key: str, s: date, e: date) -> float:
            return fetch_one(conn, SQL[sql_key], {'s': s, 'e': e})

        def make_pct_trace(
            agg_expr: str,
            hist_days: int = 8
        ) -> dict:
            """
            Builds insight_data with:
              - 'yesterday': SUM(agg_expr) for yesterday
              - 'historical': list of last hist_days days of SUM(agg_expr)
            """
            # 1) historical series
            hist_rows = conn.execute(text(f"""
                SELECT created_at::date AS day,
                       SUM({agg_expr})::float AS val
                  FROM live_transactions
                 WHERE created_at::date
                   BETWEEN CURRENT_DATE - INTERVAL '{hist_days} days'
                       AND CURRENT_DATE - INTERVAL '1 day'
                 GROUP BY created_at::date
                 ORDER BY day
            """)).mappings().all()
            hist_vals = [float(r['val']) for r in hist_rows]

            # 2) yesterday
            yd_row = conn.execute(text(f"""
                SELECT SUM({agg_expr})::float AS val
                  FROM live_transactions
                 WHERE created_at::date = CURRENT_DATE - INTERVAL '1 day'
            """)).mappings().first()
            yd = float(yd_row['val']) if yd_row and yd_row['val'] is not None else 0.0

            return {
                'yesterday':  round(yd, 4),
                'historical': [round(v, 4) for v in hist_vals]
            }

        # ─── Metrics ────────────────────────────────────────────
        curr_vol = run_agg('sum', start, end)
        prev_vol = run_agg('sum', comp_start, comp_end)
        if filter_type == 'Daily':   prev_vol /= 7
        if filter_type == 'Weekly':  prev_vol /= 4
        metrics.append({
            'title': 'Total Transaction Volume',
            'value': round(curr_vol, 2),
            'diff':  pct_diff(curr_vol, prev_vol)
        })

        curr_cnt = run_agg('count', start, end)
        prev_cnt = run_agg('count', comp_start, comp_end)
        if filter_type == 'Daily':   prev_cnt /= 7
        if filter_type == 'Weekly':  prev_cnt /= 4
        metrics.append({
            'title': 'Total Transactions',
            'value': int(curr_cnt),
            'diff':  pct_diff(curr_cnt, prev_cnt)
        })

        if filter_type == 'Daily':
            curr_avg = fetch_one(conn, """
                SELECT COALESCE(AVG(usd_value), 0)::float AS val
                  FROM live_transactions
                 WHERE created_at::date = :d
            """, {'d': start})
        else:
            curr_avg = run_agg('avg', start, end)
        prev_avg = run_agg('avg', comp_start, comp_end)
        metrics.append({
            'title': 'Average Transaction Value',
            'value': round(curr_avg, 2),
            'diff':  pct_diff(curr_avg, prev_avg)
        })

        # ─── Charts ──────────────────────────────────────────────

        # 1) Sales by Currency
        current_rows = conn.execute(text("""
            SELECT transaction_currency AS name,
                   SUM(usd_value)::float AS total_usd
              FROM live_transactions
             WHERE created_at::date BETWEEN :s AND :e
             GROUP BY transaction_currency
        """), {'s': start, 'e': end}).mappings().all()
        total_usd_curr = sum(r['total_usd'] for r in current_rows) or 1
        total_usd_prev = run_agg('sum', comp_start, comp_end)
        charts.append({
            'title':             'Sales by Currency',
            'type':              'pie',
            'value':             round(total_usd_curr, 2),
            'hist_value':        round(total_usd_prev, 2),
            'pct_change':        pct_diff(total_usd_curr, total_usd_prev),
            'change_direction': 'increased' if total_usd_curr >= total_usd_prev else 'decreased',
            'data': [
                {
                    'name':  r['name'],
                    'value': round(r['total_usd'] / total_usd_curr * 100, 1)
                }
                for r in current_rows
            ]
        })
        insight_data['sales_by_currency'] = make_pct_trace("usd_value")

        # 2) Processing Fee Analysis
        def fetch_proc(s: date, e: date):
            return conn.execute(text("""
                SELECT a.name AS acquirer,
                       SUM((pricing_ic/100.0)*usd_value + gateway_fee)::float AS total_fees,
                       SUM(usd_value)::float                                 AS total_amt
                  FROM live_transactions t
                  JOIN acquirer a ON t.acquirer_id = a.id
                 WHERE t.created_at::date BETWEEN :s AND :e
                 GROUP BY a.name
            """), {'s': s, 'e': e}).mappings().all()

        curr_proc = fetch_proc(start, end)
        prev_proc = fetch_proc(comp_start, comp_end)

        curr_pct = [(r['total_fees']/r['total_amt'])*100 for r in curr_proc if r['total_amt']]
        prev_pct = [(r['total_fees']/r['total_amt'])*100 for r in prev_proc if r['total_amt']]

        mean_curr = statistics.mean(curr_pct) if curr_pct else 0.0
        mean_prev = statistics.mean(prev_pct) if prev_pct else 0.0
        z = None
        if len(prev_pct) > 1 and statistics.stdev(prev_pct):
            z = (mean_curr - statistics.mean(prev_pct)) / statistics.stdev(prev_pct)

        charts.append({
            'title':             'Processing Fee Analysis',
            'type':              'horizontal_bar',
            'value':             round(mean_curr, 4),
            'hist_value':        round(mean_prev, 4),
            'pct_change':        pct_diff(mean_curr, mean_prev),
            'change_direction': 'increased' if mean_curr >= mean_prev else 'decreased',
            'z_score':           round(z, 4) if z is not None else None,
            'x':                 curr_pct,
            'y':                 [r['acquirer'] for r in curr_proc],
            'series': [{
                'name': 'Fee % of Volume',
                'data': curr_pct
            }]
        })
        insight_data['processing_fee_pct'] = make_pct_trace(
            "(pricing_ic/100.0)*usd_value + gateway_fee"
        )

        # 3) Gateway Fee %
        insight_data['gateway_fee_pct'] = make_pct_trace("gateway_fee")

    return {
        'metrics':      metrics,
        'charts':       charts,
        'insight_data': insight_data
    }
