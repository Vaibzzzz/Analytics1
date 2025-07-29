from datetime import datetime, timedelta, date
from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.stat_tests import compare_to_historical_single_point

engine = get_engine()

def fetch_dashboard_data() -> dict:
    """
    Returns combined metrics and charts for the dashboard,
    with extra statistical metrics (yesterday_val, historical_avg,
    z_score, p_value) on each chart.
    """
    metrics = []
    charts = []

    with engine.connect() as conn:

        # ─── Base Metrics ────────────────────────────────────────────
        total_volume = conn.execute(
            text("SELECT COALESCE(SUM(usd_value), 0) FROM live_transactions")
        ).scalar() or 0.0
        avg_value = conn.execute(
            text("SELECT COALESCE(AVG(usd_value), 0) FROM live_transactions")
        ).scalar() or 0.0

        metrics += [
            {"title": "Total Transaction Volume",  "value": round(float(total_volume), 2)},
            {"title": "Average Transaction Value", "value": round(float(avg_value),    2)},
        ]

        processing_partners = conn.execute(
            text("SELECT COUNT(*) FROM acquirer")
        ).scalar() or 0
        payment_methods = conn.execute(
            text("SELECT COUNT(DISTINCT credit_card_type) FROM live_transactions")
        ).scalar() or 0
        geographic_regions = conn.execute(
            text("SELECT COUNT(DISTINCT country) FROM merchant")
        ).scalar() or 0

        metrics += [
            {"title": "Processing Partners", "value": processing_partners},
            {"title": "Payment Methods",     "value": payment_methods},
            {"title": "Geographic Regions",  "value": geographic_regions},
        ]

        fraud_rate = conn.execute(
            text("""
                SELECT COUNT(*) FILTER (WHERE fraud) * 100.0 
                  / NULLIF(COUNT(*),0)
                  FROM live_transactions 
            """)
        ).scalar() or 0.0
        metrics.append({"title": "Fraud Rate (%)", "value": round(float(fraud_rate), 2)})

        fraud_loss = conn.execute(
            text("""
                SELECT COALESCE(SUM(usd_value),0) 
                  FROM live_transactions 
                 WHERE fraud = true
            """)
        ).scalar() or 0.0
        metrics.append({"title": "Fraud Loss", "value": round(float(fraud_loss), 2)})

        # helper to fetch hist & yesterday for any SQL aggregate
        def _stat_metrics(agg_sql: str, params: dict = {}):
            # last 8 days (excluding yesterday)
            hist = conn.execute(
                text(f"""
                    SELECT {agg_sql} AS val
                      FROM live_transactions
                     WHERE created_at::date 
                       BETWEEN CURRENT_DATE - INTERVAL '8 days' 
                           AND CURRENT_DATE - INTERVAL '1 day'
                     GROUP BY created_at::date
                     ORDER BY created_at::date
                """), params or {}
            ).scalars().all()
            hist_values = [float(v) for v in hist]
            hist_avg = sum(hist_values)/len(hist_values) if hist_values else 0.0

            yesterday = conn.execute(
                text(f"""
                    SELECT {agg_sql} AS val
                      FROM live_transactions
                     WHERE created_at::date = CURRENT_DATE - INTERVAL '1 day'
                """), params or {}
            ).scalar() or 0.0

            comp = compare_to_historical_single_point(float(yesterday), hist_values)
            return {
                "value": round(float(yesterday), 2),
                "historical_avg": round(hist_avg,     2),
                "z_score": comp["z_score"],
                "p_value": comp["p_value"],
            }

        # ─── Charts + Extra Metrics ──────────────────────────────────

        # 1) Revenue by Currency (Pie)
        pie_rows = conn.execute(text("""
            SELECT transaction_currency AS name,
                SUM(usd_value)::float    AS total
            FROM live_transactions
        GROUP BY transaction_currency
        """)).mappings().all()

        # total across all currencies (for % calculation)
        grand_total = sum(r["total"] for r in pie_rows) or 1

        chart1 = {
            "title": "Revenue by Currency",
            "type":  "pie",
            "data": [
                {
                "name":  r["name"],
                "value": round(r["total"] / grand_total * 100, 1)
                }
                for r in pie_rows
            ]
        }
        # stats on daily total revenue
        chart1["extra_metrics"] = _stat_metrics("SUM(usd_value)::float")
        charts.append(chart1)

        # 2) Top 5 Acquirers by Volume (Bar)
        chart2_rows = conn.execute(text("""
            SELECT a.name AS acquirer, COUNT(*) AS cnt
              FROM live_transactions t
              JOIN acquirer a ON t.acquirer_id = a.id
          GROUP BY a.name
          ORDER BY cnt DESC
          LIMIT 5
        """)).mappings().all()
        chart2 = {
            "title": "Top 5 Acquirers by Volume",
            "type":  "bar",
            "x":     [r["acquirer"] for r in chart2_rows],
            "y":     [r["cnt"]      for r in chart2_rows]
        }
        # stats on daily transaction count
        chart2["extra_metrics"] = _stat_metrics("COUNT(*)")
        charts.append(chart2)

        # 3) Payment Method Distribution (Bar)
        chart3_rows = conn.execute(text("""
            SELECT credit_card_type AS method, COUNT(*) AS cnt
              FROM live_transactions 
          GROUP BY credit_card_type
        """)).mappings().all()
        chart3 = {
            "title": "Payment Method Distribution",
            "type":  "bar",
            "x":     [r["method"] for r in chart3_rows],
            "y":     [r["cnt"]    for r in chart3_rows]
        }
        # stats on daily count of transactions
        chart3["extra_metrics"] = _stat_metrics("COUNT(*)")
        charts.append(chart3)

        # 4) AI-Powered Insights (List)
        insights = [
            "Implement ML-based fraud detection to reduce losses by 20–30%",
            "Optimize partner allocation on success performance",
            "Enhance 3DS flows to improve conversion rates",
            "Build market-specific geographic growth strategies",
            "Enable real-time alerting on KPI thresholds"
        ]
        chart4 = {
            "title": "AI-Powered Insights",
            "type":  "list",
            "data":  insights
        }
        # treat "yesterday_val" as count of insights
        hist_ins = [len(insights)] * 8
        hist_ins_float = [float(v) for v in hist_ins]
        comp_ins = compare_to_historical_single_point(float(len(insights)), hist_ins_float)
        chart4["extra_metrics"] = {
            "value":         len(insights),
            "historical_avg": round(sum(hist_ins_float)/len(hist_ins_float), 2),
            "z_score":        comp_ins["z_score"],
            "p_value":        comp_ins["p_value"],
        }
        charts.append(chart4)

        # 5) Recent Activity (List)
        now = datetime.utcnow()
        activity = [
            {"time": (now - timedelta(minutes=2)).isoformat(), "type": "alert",       "message": "Transaction volume spike detected"},
            {"time": (now - timedelta(hours=1)).isoformat(),   "type": "report",      "message": "Weekly performance report generated"},
            {"time": (now - timedelta(hours=3)).isoformat(),   "type": "analysis",    "message": "Fraud pattern analysis updated"},
            {"time": (now - timedelta(days=1)).isoformat(),    "type": "integration", "message": "New payment method integrated"},
        ]
        chart5 = {
            "title": "Recent Activity",
            "type":  "list",
            "data":  activity
        }
        # count of events yesterday
        yesterday_day = (now - timedelta(days=1)).date().isoformat()
        y_events = sum(1 for a in activity if a["time"].startswith(yesterday_day))
        hist_evt = [y_events] * 8
        hist_evt_float = [float(v) for v in hist_evt]
        comp_evt = compare_to_historical_single_point(float(y_events), hist_evt_float)
        chart5["extra_metrics"] = {
            "value":         y_events,
            "historical_avg": round(sum(hist_evt_float)/len(hist_evt_float), 2),
            "z_score":        comp_evt["z_score"],
            "p_value":        comp_evt["p_value"],
        }
        charts.append(chart5)

    return {
        "metrics": metrics,
        "charts":  charts
    }
