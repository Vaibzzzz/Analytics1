from datetime import date
from typing import Optional, Tuple
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges, fetch_one, pct_diff
from KPI.utils.stat_tests import compare_to_historical_single_point

engine = get_engine()
MERCHANT_ID = 26  # Adjust as needed

def get_customer_insights_data(
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None
) -> dict:
    """
    Returns customer-insights metrics and charts based on the selected date range filter.

    Metrics:
      - Unique Payment Methods (with % diff vs comparison period)
      - Unique Payment Methods Statistical Insight (yesterday vs historical)

    Charts:
      - Transactions by Acquirer (pie)
      - Transaction Type Distribution (bar)
      - Payment Creation Patterns (bar)
    """
    # Determine current vs comparison windows
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)

    metrics = []
    charts  = []

    with engine.connect() as conn:
        # ─── Metric: Unique Payment Methods ──────────────────────────────
        sql_methods = """
            SELECT COUNT(DISTINCT credit_card_type)::float
              FROM live_transactions
             WHERE merchant_id = :m_id
               AND created_at::date BETWEEN :s AND :e
        """
        curr_methods = fetch_one(conn, sql_methods, {
            'm_id': MERCHANT_ID, 's': start, 'e': end
        })
        prev_methods = fetch_one(conn, sql_methods, {
            'm_id': MERCHANT_ID, 's': comp_start, 'e': comp_end
        })
        metrics.append({
            'title': 'Unique Payment Methods',
            'value': int(curr_methods),
            'diff': pct_diff(curr_methods, prev_methods)
        })

        # ─── Metric: Statistical Insight for Yesterday ───────────────────
        sql_hist_methods = """
            SELECT created_at::date AS day, COUNT(DISTINCT credit_card_type)::float AS count
              FROM live_transactions
             WHERE merchant_id = :m_id
               AND created_at::date BETWEEN CURRENT_DATE - INTERVAL '180 days' AND CURRENT_DATE - INTERVAL '1 day'
             GROUP BY created_at::date
             ORDER BY day
        """
        hist_rows = conn.execute(text(sql_hist_methods), {'m_id': MERCHANT_ID}).mappings().all()
        hist_values = [row['count'] for row in hist_rows]

        sql_yesterday = """
            SELECT COUNT(DISTINCT credit_card_type)::float AS count
              FROM live_transactions
             WHERE merchant_id = :m_id
               AND created_at::date = CURRENT_DATE - INTERVAL '1 day'
        """
        yesterday_val = fetch_one(conn, sql_yesterday, {'m_id': MERCHANT_ID})

        comparison_result = compare_to_historical_single_point(yesterday_val, hist_values)

        metrics.append({
            'title': 'Unique Payment Methods (Stat Insight)',
            'value': int(yesterday_val),
            'diff': None,
            'insight': comparison_result['insight'],
            'z_score': comparison_result['z_score'],
            'p_value': comparison_result['p_value'],
            'is_significant': comparison_result['is_significant']
        })

        # ─── Chart 1: Transactions by Acquirer ───────────────────────────
        acquirer_rows = conn.execute(text("""
            SELECT a.name AS name, COUNT(*) AS value
              FROM live_transactions lt
              JOIN acquirer a ON lt.acquirer_id = a.id
             WHERE lt.merchant_id = :m_id
               AND lt.created_at::date BETWEEN :s AND :e
             GROUP BY a.name
             ORDER BY value DESC
        """), {'m_id': MERCHANT_ID, 's': start, 'e': end}).mappings().all()

        charts.append({
            'title': 'Transactions by Acquirer',
            'type':  'pie',
            'data':  [{'name': row['name'], 'value': row['value']} for row in acquirer_rows]
        })

        # ─── Chart 2: Transaction Type Distribution ─────────────────────
        txn_type_rows = conn.execute(text("""
            SELECT transaction_type, COUNT(*) AS txn_count
              FROM live_transactions
             WHERE merchant_id = :m_id
               AND created_at::date BETWEEN :s AND :e
             GROUP BY transaction_type
             ORDER BY txn_count DESC
        """), {'m_id': MERCHANT_ID, 's': start, 'e': end}).mappings().all()

        charts.append({
            'title': 'Transaction Type Distribution',
            'type':  'bar',
            'x':     [row['transaction_type'] for row in txn_type_rows],
            'y':     [row['txn_count'] for row in txn_type_rows]
        })

        # ─── Chart 3: Payment Creation Patterns ─────────────────────────
        creation_rows = conn.execute(text("""
            SELECT creation_type, COUNT(*) AS txn_count
              FROM live_transactions
             WHERE merchant_id = :m_id
               AND created_at::date BETWEEN :s AND :e
             GROUP BY creation_type
             ORDER BY txn_count DESC
        """), {'m_id': MERCHANT_ID, 's': start, 'e': end}).mappings().all()

        charts.append({
            'title': 'Payment Creation Patterns',
            'type':  'bar',
            'x':     [row['creation_type'] for row in creation_rows],
            'y':     [row['txn_count'] for row in creation_rows]
        })

    return {
        'metrics': metrics,
        'charts':  charts
    }
