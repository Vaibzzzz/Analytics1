from datetime import date, timedelta
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges
from KPI.utils.stat_tests import compare_to_historical_single_point
from KPI.chart_configs import DRILL_LVL1

engine = get_engine()

def fetch_processing_partners() -> Dict[str, Any]:
    """
    Fetch the count of processing partners.
    """
    with engine.connect() as conn:
        partners = conn.execute(
            text("SELECT COUNT(*)::float AS val FROM acquirer"),
            {}
        ).scalar() or 0.0
    return {
        'title': 'Processing Partners',
        'value': int(partners),
        'diff': None,
    }


def fetch_top5_acquirers(
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None
) -> Dict[str, Any]:
    """
    Fetch the Top 5 Acquirers by Volume bar chart.
    """
    start, end, _, _ = get_date_ranges(filter_type, custom)

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT a.name AS name,
                       COUNT(*)::float AS cnt
                  FROM live_transactions t
                  JOIN acquirer a ON t.acquirer_id = a.id
                 WHERE t.created_at::date BETWEEN :s AND :e
              GROUP BY a.name
              ORDER BY cnt DESC
                 LIMIT 5
            """), {'s': start, 'e': end}
        ).mappings().all()

    data = [{'name': r['name'], 'value': r['cnt']} for r in rows]

    return {
        'chartKey':           'top5Acquirers',
        'title':              'Top 5 Acquirers by Volume',
        'type':               'bar',
        'data':               data,
        'drillable':          True,
        'nextChart':          DRILL_LVL1,
        'start':              start,
        'end':                end,
        'baseFilteredField':  'a.name',
        'baseFilteredValue':  None,
        'extra_metrics':      _stat_metrics(start, end, "COUNT(*)"),
    }


def fetch_payment_method_distribution(
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None
) -> Dict[str, Any]:
    """
    Fetch the Payment Method Distribution bar chart.
    """
    start, end, _, _ = get_date_ranges(filter_type, custom)

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT credit_card_type AS name,
                       COUNT(*)::float     AS cnt
                  FROM live_transactions
                 WHERE created_at::date BETWEEN :s AND :e
              GROUP BY credit_card_type
            """), {'s': start, 'e': end}
        ).mappings().all()

    data = [{'name': r['name'], 'value': r['cnt']} for r in rows]

    return {
        'chartKey':           'paymentMethodDistribution',
        'title':              'Payment Method Distribution',
        'type':               'bar',
        'data':               data,
        'drillable':          True,
        'nextChart':          DRILL_LVL1,
        'start':              start,
        'end':                end,
        'baseFilteredField':  'credit_card_type',
        'baseFilteredValue':  None,
        'extra_metrics':      _stat_metrics(start, end, "COUNT(*)"),
    }

def fetch_processing_partner(
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None
) -> Dict[str, Any]:
    """
    Fetch Success Rate and USD Value grouped by Acquirer for 3D-style chart.
    """
    start, end, _, _ = get_date_ranges(filter_type, custom)

    with engine.connect() as conn:
        rows = conn.execute(text("""
            SELECT a.name AS name,
                   AVG(t.payment_successful::int)::float AS success_rate,
                   SUM(t.usd_value)::float AS usd_value
              FROM live_transactions t
              JOIN acquirer a ON t.acquirer_id = a.id
             WHERE t.created_at::date BETWEEN :s AND :e
          GROUP BY a.name
          ORDER BY usd_value DESC
        """), {"s": start, "e": end}).mappings().all()

    data = [
        {
            'name': r['name'],
            'success_rate': round(r['success_rate'] or 0.0, 2),
            'usd_value': round(r['usd_value'] or 0.0, 2),
        }
        for r in rows
    ]

    return {
        'chartKey':           'successRateByAcquirer',
        'title':              'Success Rate vs USD Value by Acquirer',
        'type':               'bubble',  # or 'scatter3D'
        'data':               data,
        'drillable':          False,
        'start':              start,
        'end':                end,
        'baseFilteredField':  'a.name',
        'baseFilteredValue':  None,
        'extra_metrics':      _stat_metrics(start, end, "AVG(payment_successful::int)::float"),
    }

def _stat_metrics(start: date, end: date, agg_sql: str) -> Dict[str, Any]:
    """
    Helper to compute yesterday + historical stats for a given aggregate SQL.
    """
    with engine.connect() as conn:
        hist = conn.execute(
            text(f"""
                SELECT {agg_sql} AS val
                  FROM live_transactions
                 WHERE created_at::date BETWEEN :hs AND :he
                 GROUP BY created_at::date
                 ORDER BY created_at::date
            """), {
                'hs': start - timedelta(days=8),
                'he': end - timedelta(days=1),
            }
        ).scalars().all()

        yesterday = conn.execute(
            text(f"""
                SELECT {agg_sql} AS val
                  FROM live_transactions
                 WHERE created_at::date = :d
            """), {
                'd': end - timedelta(days=1),
            }
        ).scalar() or 0.0

    hist_vals = [float(v) for v in hist]
    comp = compare_to_historical_single_point(yesterday, hist_vals)
    return {
        'value':          round(yesterday, 2),
        'historical_avg': round(sum(hist_vals) / len(hist_vals) if hist_vals else 0.0, 2),
        'z_score':        comp['z_score'],
        'p_value':        comp['p_value'],
    }