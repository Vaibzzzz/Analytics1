# File: app/services/financial.py

from datetime import date, timedelta
from typing import Optional, Tuple, List, Dict, Any
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges, pct_diff
from KPI.utils.stat_tests import compare_to_historical_single_point
from KPI.chart_configs import DRILL_LVL1

engine = get_engine()

def fetch_dashboard_metrics(
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None
) -> List[Dict[str, Any]]:
    """
    Fetch only the base KPIs:
    - Total Transaction Volume (with pct diff)
    - Average Transaction Value (with pct diff)
    - Processing Partners
    - Payment Methods
    - Geographic Regions
    - Fraud Rate (%)
    - Fraud Loss
    """
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)

    with engine.connect() as conn:
        # Total Transaction Volume
        total = conn.execute(
            text("""
                SELECT COALESCE(SUM(usd_value),0)::float AS val
                  FROM live_transactions
                 WHERE created_at::date BETWEEN :s AND :e
            """), {'s': start, 'e': end}
        ).scalar() or 0.0
        prev_total = conn.execute(
            text("""
                SELECT COALESCE(SUM(usd_value),0)::float AS val
                  FROM live_transactions
                 WHERE created_at::date BETWEEN :cs AND :ce
            """), {'cs': comp_start, 'ce': comp_end}
        ).scalar() or 0.0

        metrics = [
            {
                'title': 'Total Transaction Volume',
                'value': round(total, 2),
                'diff': pct_diff(total, prev_total),
            }
        ]

        # Average Transaction Value
        avg = conn.execute(
            text("""
                SELECT COALESCE(AVG(usd_value),0)::float AS val
                  FROM live_transactions
                 WHERE created_at::date BETWEEN :s AND :e
            """), {'s': start, 'e': end}
        ).scalar() or 0.0
        prev_avg = conn.execute(
            text("""
                SELECT COALESCE(AVG(usd_value),0)::float AS val
                  FROM live_transactions
                 WHERE created_at::date BETWEEN :cs AND :ce
            """), {'cs': comp_start, 'ce': comp_end}
        ).scalar() or 0.0

        metrics.append({
            'title': 'Average Transaction Value',
            'value': round(avg, 2),
            'diff': pct_diff(avg, prev_avg),
        })

        # Processing Partners Count
        partners = conn.execute(
            text("SELECT COUNT(*)::float AS val FROM acquirer"),
            {}
        ).scalar() or 0.0
        metrics.append({
            'title': 'Processing Partners',
            'value': int(partners),
            'diff': None,
        })

        # Payment Methods Count
        methods = conn.execute(
            text("""
                SELECT COUNT(DISTINCT credit_card_type)::float AS val
                  FROM live_transactions
                 WHERE created_at::date BETWEEN :s AND :e
            """), {'s': start, 'e': end}
        ).scalar() or 0.0
        metrics.append({
            'title': 'Payment Methods',
            'value': int(methods),
            'diff': None,
        })

        # Geographic Regions Count
        regions = conn.execute(
            text("SELECT COUNT(DISTINCT country)::float AS val FROM merchant"),
            {}
        ).scalar() or 0.0
        metrics.append({
            'title': 'Geographic Regions',
            'value': int(regions),
            'diff': None,
        })

        # Fraud Rate (%)
        fraud_rate = conn.execute(
            text("""
                SELECT COUNT(*) FILTER (WHERE fraud)::float * 100
                  / NULLIF(COUNT(*),0) AS val
                  FROM live_transactions
                 WHERE created_at::date BETWEEN :s AND :e
            """), {'s': start, 'e': end}
        ).scalar() or 0.0
        metrics.append({
            'title': 'Fraud Rate (%)',
            'value': round(fraud_rate, 2),
            'diff': None,
        })

        # Fraud Loss
        loss = conn.execute(
            text("""
                SELECT COALESCE(SUM(usd_value),0)::float AS val
                  FROM live_transactions
                 WHERE fraud = true
                   AND created_at::date BETWEEN :s AND :e
            """), {'s': start, 'e': end}
        ).scalar() or 0.0
        metrics.append({
            'title': 'Fraud Loss',
            'value': round(loss, 2),
            'diff': None,
        })

    return metrics


def fetch_revenue_by_currency(
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None
) -> Dict[str, Any]:
    """
    Fetch the Revenue by Currency pie chart.
    """
    start, end, _, _ = get_date_ranges(filter_type, custom)

    with engine.connect() as conn:
        rows = conn.execute(
            text("""
                SELECT transaction_currency AS name,
                       SUM(usd_value)::float AS total
                  FROM live_transactions
                 WHERE created_at::date BETWEEN :s AND :e
              GROUP BY transaction_currency
            """), {'s': start, 'e': end}
        ).mappings().all()

    total_all = sum(r['total'] for r in rows) or 1
    data = [
        {'name': r['name'], 'value': round(r['total'] / total_all * 100, 1)}
        for r in rows
    ]

    return {
        'chartKey':           'revenueByCurrency',
        'title':              'Revenue by Currency',
        'type':               'pie',
        'data':               data,
        'drillable':          True,
        'nextChart':          DRILL_LVL1,
        'start':              start,
        'end':                end,
        'baseFilteredField':  'transaction_currency',
        'baseFilteredValue':  None,
        'extra_metrics':      _stat_metrics(start, end, "SUM(usd_value)::float"),
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


def fetch_dashboard_data(
    filter_type: str = 'YTD',
    custom: Optional[Tuple[date, date]] = None
) -> Dict[str, Any]:
    """
    Combines:
     - dashboard metrics (list of Metric dicts)
     - all top-level charts
    """
    metrics = fetch_dashboard_metrics(filter_type, custom)
    charts: List[Dict[str, Any]] = [
        fetch_revenue_by_currency(filter_type, custom),
        fetch_top5_acquirers(filter_type, custom),
        fetch_payment_method_distribution(filter_type, custom),
    ]
    return {
        "metrics": metrics,
        "charts": charts,
    }