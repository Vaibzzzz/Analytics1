from datetime import date
from typing import Optional, Tuple
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges
from KPI.utils.stat_tests import compare_to_historical_single_point

engine = get_engine()

def get_gateway_fee_analysis(filter_type: str = 'YTD',
                             custom: Optional[Tuple[date, date]] = None) -> dict:
    """
    Returns a bar chart showing gateway fee distribution by acquirer
    from live_transactions within the selected time range, along with
    statistical insight comparing yesterday's total fee to historical trend.
    """
    start, end, _, _ = get_date_ranges(filter_type, custom)
    print(f"Gateway Fee Analysis: {start} to {end}")

    charts = []
    metrics = []

    with engine.connect() as conn:
        # ─── Chart: Gateway Fee Distribution by Acquirer ────────────────
        rows = conn.execute(text("""
            SELECT a.name AS acquirer,
                   SUM(t.gateway_fee) AS total_gateway_fee,
                   COUNT(*) AS txn_count
              FROM live_transactions t
              JOIN acquirer a ON t.acquirer_id = a.id
             WHERE t.created_at::date BETWEEN :s AND :e
             GROUP BY a.name
             ORDER BY total_gateway_fee DESC
        """), {'s': start, 'e': end}).mappings().all()

        chart_data = {
            'title': 'Gateway Fee Distribution',
            'type': 'bar',
            'x': [r['acquirer'] for r in rows],
            'y': [round(r['total_gateway_fee'], 2) for r in rows],
            'series': [{
                'name': 'Gateway Fee (USD)',
                'data': [round(r['total_gateway_fee'], 2) for r in rows]
            }]
        }
        charts.append(chart_data)

        # ─── Metric: Gateway Fee Statistical Insight ────────────────────
        hist_rows = conn.execute(text("""
            SELECT created_at::date AS day,
                   SUM(gateway_fee)::float AS total_fee
              FROM live_transactions
             WHERE created_at::date BETWEEN CURRENT_DATE - INTERVAL '7 days' AND CURRENT_DATE - INTERVAL '1 day'
             GROUP BY created_at::date
             ORDER BY day
        """)).mappings().all()
        hist_values = [r['total_fee'] for r in hist_rows]
        hist_avg = sum(hist_values) / len(hist_values) if hist_values else 0

        yesterday_val = conn.execute(text("""
            SELECT SUM(gateway_fee)::float AS total_fee
              FROM live_transactions
             WHERE created_at::date = CURRENT_DATE - INTERVAL '1 day'
        """)).scalar() or 0

        comparison_result = compare_to_historical_single_point(yesterday_val, hist_values)

        metrics.append({
    'title': 'Gateway Fee (Stat Insight)',
    'value': round(yesterday_val, 2),
    'insight': comparison_result['insight'],
    'z_score': comparison_result['z_score'],
    'p_value': comparison_result['p_value'],
    'is_significant': bool(comparison_result['is_significant']),
    'historical_avg': round(hist_avg, 2)

})


    return {
        'metrics': metrics,
        'charts': charts
    }