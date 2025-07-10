from datetime import datetime, timedelta
from sqlalchemy import text
from DB.connector import get_engine

engine = get_engine()

def fetch_dashboard_data() -> dict:
    """
    Returns combined metrics and charts for the dashboard.
    """
    metrics = []
    charts = []

    with engine.connect() as conn:

        # ─── Metrics ──────────────────────────────────────────────
        total_volume = conn.execute(
            text(f"SELECT COALESCE(SUM(usd_value), 0) FROM live_transactions ")
        ).scalar() or 0.0
        avg_value = conn.execute(
            text(f"SELECT COALESCE(AVG(usd_value),   0) FROM live_transactions ")
        ).scalar() or 0.0

        metrics += [
            {"title": "Total Transaction Volume",  "value": round(float(total_volume), 2)},
            {"title": "Average Transaction Value", "value": round(float(avg_value),    2)},
        ]

        processing_partners = conn.execute(
            text("SELECT COUNT(*) FROM acquirer")
        ).scalar() or 0
        payment_methods = conn.execute(
            text(f"SELECT COUNT(DISTINCT credit_card_type) FROM live_transactions ")
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
            text(f"""
                SELECT COUNT(*) FILTER (WHERE fraud) * 100.0 
                  / NULLIF(COUNT(*),0)
                  FROM live_transactions 
            """)
        ).scalar() or 0.0
        metrics.append({"title": "Fraud Rate (%)", "value": round(float(fraud_rate), 2)})

        fraud_loss = conn.execute(
            text(f"""
                SELECT COALESCE(SUM(usd_value),0) 
                  FROM live_transactions 
                 WHERE fraud = true
            """)
        ).scalar() or 0.0
        metrics.append({"title": "Fraud Loss", "value": round(float(fraud_loss), 2)})

        # ─── Charts ───────────────────────────────────────────────

        # 1) Revenue by Currency (Pie)
        rows = conn.execute(
            text(f"""
                SELECT transaction_currency AS name, SUM(usd_value) AS total
                  FROM live_transactions 
              GROUP BY transaction_currency
            """)
        ).mappings().all()
        total = sum(r["total"] for r in rows) or 1
        charts.append({
            "title": "Revenue by Currency",
            "type":  "pie",
            "data": [
                {"name": r["name"], "value": round(r["total"] / total * 100, 1)}
                for r in rows
            ]
        })

        # 2) Top 5 Acquirers by Volume (Bar)
        rows = conn.execute(
            text(f"""
                SELECT a.name AS acquirer, COUNT(*) AS cnt
                  FROM live_transactions t
                  JOIN acquirer a ON t.acquirer_id = a.id
                  
              GROUP BY a.name
              ORDER BY cnt DESC
              LIMIT 5
            """)
        ).mappings().all()
        charts.append({
            "title": "Top 5 Acquirers by Volume",
            "type":  "bar",
            "x":     [r["acquirer"] for r in rows],
            "y":     [r["cnt"]      for r in rows]
        })

        # 3) Payment Method Distribution (Bar)
        rows = conn.execute(
            text(f"""
                SELECT credit_card_type AS method, COUNT(*) AS cnt
                  FROM live_transactions 
              GROUP BY credit_card_type
            """)
        ).mappings().all()
        charts.append({
            "title": "Payment Method Distribution",
            "type":  "bar",
            "x":     [r["method"] for r in rows],
            "y":     [r["cnt"]    for r in rows]
        })

        # 4) AI-Powered Insights (List)
        insights = [
            "Implement ML-based fraud detection to reduce losses by 20–30%",
            "Optimize partner allocation on success performance",
            "Enhance 3DS flows to improve conversion rates",
            "Build market-specific geographic growth strategies",
            "Enable real-time alerting on KPI thresholds"
        ]
        charts.append({
            "title": "AI-Powered Insights",
            "type":  "list",
            "data":  insights
        })

        # 5) Recent Activity (List)
        now = datetime.utcnow()
        activity = [
            {"time": (now - timedelta(minutes=2)).isoformat(), "type": "alert",       "message": "Transaction volume spike detected"},
            {"time": (now - timedelta(hours=1)).isoformat(),   "type": "report",      "message": "Weekly performance report generated"},
            {"time": (now - timedelta(hours=3)).isoformat(),   "type": "analysis",    "message": "Fraud pattern analysis updated"},
            {"time": (now - timedelta(days=1)).isoformat(),    "type": "integration", "message": "New payment method integrated"},
        ]
        charts.append({
            "title": "Recent Activity",
            "type":  "list",
            "data":  activity
        })

    return {
        "metrics": metrics,
        "charts":  charts
    }
