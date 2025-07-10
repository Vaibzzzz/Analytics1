from datetime import date
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import get_date_ranges, pct_diff, fetch_one
from typing import Optional, Tuple

engine = get_engine()

def get_risk_and_fraud_data(filter_type: str = 'YTD',
                            custom: Optional[Tuple[date, date]] = None) -> dict:
    """
    Returns risk & fraud KPI metrics and chart data based on the selected date range filter.
    KPIs:
      - Fraud Loss
      - Fraud Rate (%)
      - Fraud Detection Rate (%) & Count
      - Potential Fraud Saving
      - 3DS Authentication Effectiveness (%)
    Charts:
      - Risk Analysis by Region
    """
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)
    metrics, charts = [], []

    with engine.connect() as conn:
        # ─── 1) Fraud Loss ──────────────────────────────────────────────
        sql_loss = """
          SELECT COALESCE(SUM(usd_value),0)
            FROM live_transactions
           WHERE fraud = true
             AND created_at::date BETWEEN :s AND :e
        """
        curr_loss = fetch_one(conn, sql_loss, {'s': start, 'e': end})
        prev_loss = fetch_one(conn, sql_loss, {'s': comp_start, 'e': comp_end})
        metrics.append({
            'title': 'Fraud Loss',
            'value': round(curr_loss, 2),
            'diff': pct_diff(curr_loss, prev_loss)
        })

        # ─── 2) Fraud Rate (%) ─────────────────────────────────────────
        sql_total = "SELECT COUNT(*)::float FROM live_transactions WHERE created_at::date BETWEEN :s AND :e"
        sql_fraud = """
          SELECT COUNT(*)::float
            FROM live_transactions
           WHERE fraud = true
             AND created_at::date BETWEEN :s AND :e
        """
        curr_total = fetch_one(conn, sql_total, {'s': start, 'e': end}) or 1
        prev_total = fetch_one(conn, sql_total, {'s': comp_start, 'e': comp_end}) or 1
        curr_fraud = fetch_one(conn, sql_fraud, {'s': start, 'e': end})
        prev_fraud = fetch_one(conn, sql_fraud, {'s': comp_start, 'e': comp_end})
        curr_rate = round(curr_fraud / curr_total * 100, 2)
        prev_rate = round(prev_fraud / prev_total * 100, 2)
        metrics.append({
            'title': 'Fraud Rate (%)',
            'value': curr_rate,
            'diff': pct_diff(curr_rate, prev_rate)
        })

        # ─── 3) Fraud Detection Rate & Count ───────────────────────────
        sql_detect = """
          SELECT COUNT(*)::float
            FROM live_transactions
           WHERE pred_fraud = true
             AND created_at::date BETWEEN :s AND :e
        """
        curr_detect = fetch_one(conn, sql_detect, {'s': start, 'e': end})
        prev_detect = fetch_one(conn, sql_detect, {'s': comp_start, 'e': comp_end})
        curr_detect_pct = round(curr_detect / curr_total * 100, 2)
        prev_detect_pct = round(prev_detect / prev_total * 100, 2)
        metrics += [
            {
                'title': 'Fraud Detection Rate (%)',
                'value': curr_detect_pct,
                'diff': pct_diff(curr_detect_pct, prev_detect_pct)
            },
            {
                'title': 'Fraud Detections (count)',
                'value': int(curr_detect),
                'diff': pct_diff(curr_detect, prev_detect)
            }
        ]

        # ─── 4) Potential Fraud Saving ──────────────────────────────────
        avg_fraud_loss = curr_loss / curr_fraud if curr_fraud else 0
        curr_saving = round(curr_detect_pct / 100 * avg_fraud_loss, 2)
        prev_avg_fraud = prev_loss / prev_fraud if prev_fraud else 0
        prev_saving = round(prev_detect_pct / 100 * prev_avg_fraud, 2)
        metrics.append({
            'title': 'Potential Fraud Saving',
            'value': curr_saving,
            'diff': pct_diff(curr_saving, prev_saving)
        })

        # ─── 5) 3DS Authentication Effectiveness (Metric) ─────────────
        rows_3ds = conn.execute(text("""
          SELECT
            COUNT(*) FILTER (WHERE fraud = true AND sca_type = 'THREEDS_2_0')::float AS fraud_3ds,
            COUNT(*) FILTER (WHERE sca_type = 'THREEDS_2_0')::float               AS total_3ds
          FROM live_transactions
         WHERE created_at::date BETWEEN :s AND :e
        """), {'s': start, 'e': end}).mappings().all()
        fraud_3ds = rows_3ds[0]['fraud_3ds']
        total_3ds = rows_3ds[0]['total_3ds'] or 1
        effectiveness = round(fraud_3ds / total_3ds * 100, 2)
        # comparison window
        prev_3ds_rows = conn.execute(text("""
          SELECT
            COUNT(*) FILTER (WHERE fraud = true AND sca_type = 'THREEDS_2_0')::float AS fraud_3ds,
            COUNT(*) FILTER (WHERE sca_type = 'THREEDS_2_0')::float               AS total_3ds
          FROM live_transactions
         WHERE created_at::date BETWEEN :s AND :e
        """), {'s': comp_start, 'e': comp_end}).mappings().all()
        prev_fraud_3ds = prev_3ds_rows[0]['fraud_3ds']
        prev_total_3ds = prev_3ds_rows[0]['total_3ds'] or 1
        prev_effectiveness = round(prev_fraud_3ds / prev_total_3ds * 100, 2)

        metrics.append({
            'title': '3DS Authentication Effectiveness (%)',
            'value': effectiveness,
            'diff': pct_diff(effectiveness, prev_effectiveness)
        })

        # ─── Chart: Risk Analysis by Region ─────────────────────────────
        rows = conn.execute(text("""
            SELECT
              t.region,
              COUNT(*) FILTER (WHERE t.fraud = true)::float AS fraud_count,
              COUNT(*)::float                             AS total_count
            FROM live_transactions t
            WHERE t.created_at::date BETWEEN :s AND :e
            GROUP BY t.region
        """), {'s': start, 'e': end}).mappings().all()

        # 2) fetch every label in the region_enum
        all_regions = conn.execute(text("""
            SELECT unnest(enum_range(NULL::region_enum)) AS region
        """)).scalars().all()

        # 3) build a quick lookup of your fetched counts
        row_map = { r['region']: r for r in rows }

        # 4) for each enum value, compute a rate (or 0 if no data)
        x = []
        y = []
        for region in all_regions:
            rec = row_map.get(region)
            if rec and rec['total_count']:
                rate = round(rec['fraud_count'] / rec['total_count'] * 100, 2)
            else:
                rate = 0.0
            x.append(region)
            y.append(rate)

        charts.append({
            'title': 'Risk Analysis by Region',
            'type':  'bar',
            'x':      x,
            'y':      y
        })


    return {
        'metrics': metrics,
        'charts': charts,
    }
