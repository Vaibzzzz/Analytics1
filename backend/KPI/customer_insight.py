from datetime import date
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges, fetch_one, pct_diff
from typing import Optional, Tuple

engine = get_engine()
MERCHANT_ID = 26  # Adjust as needed

def get_customer_insights_data(
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None
) -> dict:
    """
    Returns customer‐insights metrics and charts based on the selected date range filter.

    Metrics:
      - Unique Payment Methods (with % diff vs comparison period)

    Charts:
      - Transactions by Acquirer (bar)
      - Transaction Type Distribution (bar)
      - Payment Creation Patterns (bar)
    """
    # determine current vs comparison windows
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)

    metrics = []
    charts  = []

    with engine.connect() as conn:
        # ─── Metric: Unique Payment Methods ─────────────────────────────────
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

        # ─── Chart 1: Transactions by Acquirer ─────────────────────────────
        acquirer_rows = conn.execute(text("""
            SELECT a.name AS name, COUNT(*) AS value
              FROM live_transactions lt
              JOIN acquirer a
                ON lt.acquirer_id = a.id
             WHERE lt.merchant_id = :m_id
               AND lt.created_at::date BETWEEN :s AND :e
             GROUP BY a.name
             ORDER BY value DESC
        """), {'m_id': MERCHANT_ID, 's': start, 'e': end}).mappings().all()

        charts.append({
            'title': 'Transactions by Acquirer',
            'type':  'pie',
            'data':  [
                {'name': row['name'], 'value': row['value']}
                for row in acquirer_rows
            ]
        })
        # ─── Chart 2: Transaction Type Distribution ───────────────────────
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
            'y':     [row['txn_count']         for row in txn_type_rows]
        })

        # ─── Chart 3: Payment Creation Patterns ───────────────────────────
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
            'y':     [row['txn_count']      for row in creation_rows]
        })

    return {
        'metrics': metrics,
        'charts':  charts
    }