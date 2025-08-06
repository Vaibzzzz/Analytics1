from datetime import datetime, timedelta
from sqlalchemy import text
from collections import defaultdict
from DB.connector import get_engine
from KPI.utils.stat_tests import compare_to_historical_single_point

engine = get_engine()

def fetch_dashboard_data() -> dict:
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
            {"title": "Average Transaction Value", "value": round(float(avg_value), 2)},
        ]

        processing_partners = conn.execute(text("SELECT COUNT(*) FROM acquirer")).scalar() or 0
        payment_methods = conn.execute(text("SELECT COUNT(DISTINCT credit_card_type) FROM live_transactions")).scalar() or 0
        geographic_regions = conn.execute(text("SELECT COUNT(DISTINCT country) FROM merchant")).scalar() or 0

        metrics += [
            {"title": "Processing Partners", "value": processing_partners},
            {"title": "Payment Methods",     "value": payment_methods},
            {"title": "Geographic Regions",  "value": geographic_regions},
        ]

        fraud_rate = conn.execute(text("""
            SELECT COUNT(*) FILTER (WHERE fraud) * 100.0 / NULLIF(COUNT(*), 0)
            FROM live_transactions
        """)).scalar() or 0.0

        metrics.append({"title": "Fraud Rate (%)", "value": round(float(fraud_rate), 2)})

        fraud_loss = conn.execute(text("""
            SELECT COALESCE(SUM(usd_value), 0)
            FROM live_transactions
            WHERE fraud = true
        """)).scalar() or 0.0

        metrics.append({"title": "Fraud Loss", "value": round(float(fraud_loss), 2)})

        # ─── Historical Stats Helper ─────────────────────────────────
        def _stat_metrics(agg_sql: str, params: dict = {}):
            hist = conn.execute(text(f"""
                SELECT {agg_sql} AS val
                FROM live_transactions
                WHERE created_at::date BETWEEN CURRENT_DATE - INTERVAL '8 days' AND CURRENT_DATE - INTERVAL '1 day'
                GROUP BY created_at::date
                ORDER BY created_at::date
            """), params or {}).scalars().all()

            hist_values = [float(v) for v in hist]
            hist_avg = sum(hist_values) / len(hist_values) if hist_values else 0.0

            yesterday = conn.execute(text(f"""
                SELECT {agg_sql} AS val
                FROM live_transactions
                WHERE created_at::date = CURRENT_DATE - INTERVAL '1 day'
            """), params or {}).scalar() or 0.0

            comp = compare_to_historical_single_point(float(yesterday), hist_values)
            return {
                "value": round(float(yesterday), 2),
                "historical_avg": round(hist_avg, 2),
                "z_score": comp["z_score"],
                "p_value": comp["p_value"],
            }

        # ─── Chart 1: Revenue by Currency ────────────────────────────
        pie_rows = conn.execute(text("""
            SELECT transaction_currency AS name,
                   SUM(usd_value)::float AS total
            FROM live_transactions
            GROUP BY transaction_currency
        """)).mappings().all()

        grand_total = sum(r["total"] for r in pie_rows) or 1

        chart1 = {
            "title": "Revenue by Currency",
            "type":  "pie",
            "data": [
                {"name": r["name"], "value": round(r["total"] / grand_total * 100, 1)}
                for r in pie_rows
            ],
            "extra_metrics": _stat_metrics("SUM(usd_value)::float")
        }
        charts.append(chart1)

        # ─── Chart 2: Top 5 Acquirers by Volume ─────────────────────
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
            "y":     [r["cnt"]      for r in chart2_rows],
            "extra_metrics": _stat_metrics("COUNT(*)")
        }
        charts.append(chart2)
        # ─── Chart 3: Payment Method Distribution + Drilldown ───────
        from collections import defaultdict

        # Level 0: Main chart by credit_card_type
        chart3_rows = conn.execute(text("""
            SELECT credit_card_type AS method, COUNT(*) AS cnt
            FROM live_transactions
            GROUP BY credit_card_type
        """)).mappings().all()

        methods = [r["method"] for r in chart3_rows]
        counts = [r["cnt"] for r in chart3_rows]


        # Final chart object
        chart3 = {
            "title": "Payment Method Distribution",
            "type": "bar",
            "x": methods,
            "y": counts,
            "drilldown": {
                "level": "lvl_1",
                "type": "bar"
            },
            "extra_metrics": _stat_metrics("COUNT(*)")
        }

        charts.append(chart3)

        # ─── Chart 4: AI-Powered Insights ───────────────────────────
        insights = [
            "Implement ML-based fraud detection to reduce losses by 20–30%",
            "Optimize partner allocation on success performance",
            "Enhance 3DS flows to improve conversion rates",
            "Build market-specific geographic growth strategies",
            "Enable real-time alerting on KPI thresholds"
        ]

        hist_ins = [len(insights)] * 8
        comp_ins = compare_to_historical_single_point(float(len(insights)), hist_ins)

        chart4 = {
            "title": "AI-Powered Insights",
            "type":  "list",
            "data":  insights,
            "extra_metrics": {
                "value":         len(insights),
                "historical_avg": round(sum(hist_ins) / len(hist_ins), 2),
                "z_score":        comp_ins["z_score"],
                "p_value":        comp_ins["p_value"],
            }
        }
        charts.append(chart4)

        # ─── Chart 5: Recent Activity (Simulated) ───────────────────
        now = datetime.utcnow()
        activity = [
            {"time": (now - timedelta(minutes=2)).isoformat(), "type": "alert",       "message": "Transaction volume spike detected"},
            {"time": (now - timedelta(hours=1)).isoformat(),   "type": "report",      "message": "Weekly performance report generated"},
            {"time": (now - timedelta(hours=3)).isoformat(),   "type": "analysis",    "message": "Fraud pattern analysis updated"},
            {"time": (now - timedelta(days=1)).isoformat(),    "type": "integration", "message": "New payment method integrated"},
        ]

        yesterday_day = (now - timedelta(days=1)).date().isoformat()
        y_events = sum(1 for a in activity if a["time"].startswith(yesterday_day))
        hist_evt = [y_events] * 8
        comp_evt = compare_to_historical_single_point(float(y_events), hist_evt)

        chart5 = {
            "title": "Recent Activity",
            "type":  "list",
            "data":  activity,
            "extra_metrics": {
                "value":         y_events,
                "historical_avg": round(sum(hist_evt) / len(hist_evt), 2),
                "z_score":        comp_evt["z_score"],
                "p_value":        comp_evt["p_value"],
            }
        }
        charts.append(chart5)

    return {
        "metrics": metrics,
        "charts":  charts
    }
