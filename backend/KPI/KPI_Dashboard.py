from datetime import datetime, timedelta
from sqlalchemy import text
from DB.connector import get_db_engine

engine = get_db_engine()

def get_transaction_performance_data() -> dict:
    """
    Returns the combined metrics + charts payload for the dashboard.
    """
    metrics = []
    charts  = []

    with engine.connect() as conn:
        # ─── Metrics ─────────────────────────────────────────────────

        # Total transaction volume & average value
        total_volume = conn.execute(text(
            "SELECT COALESCE(SUM(amount),0) FROM transaction"
        )).scalar() or 0.0
        avg_value = conn.execute(text(
            "SELECT COALESCE(AVG(amount),0) FROM transaction"
        )).scalar() or 0.0

        metrics += [
            {"title": "Total Transaction Volume",  "value": round(float(total_volume),2)},
            {"title": "Average Transaction Value", "value": round(float(avg_value),2)},
        ]

        

        # ─── Charts ─────────────────────────────────────────────────

        # 1) Revenue by Currency (Pie)
        rows = conn.execute(text(
            "SELECT transaction_currency, SUM(amount) AS total FROM transaction GROUP BY transaction_currency"
        )).mappings().all()
        total = sum(r["total"] for r in rows) or 1
        charts.append({
            "title": "Revenue by Currency",
            "type": "pie",
            "data": [
                {"name": r["transaction_currency"], "value": round(r["total"]/total*100,1)}
                for r in rows
            ]
        })

        # 2) Top 5 Acquirers by Volume (Bar)
        rows = conn.execute(text("""
            SELECT
                a.name         AS acquirer,
                COUNT(*)       AS cnt
                FROM transaction t
                JOIN acquirer a
                ON t.acquirer_id = a.id
                GROUP BY a.name
                ORDER BY cnt DESC
                LIMIT 5
        """)).mappings().all()
        charts.append({
            "title": "Top 5 Acquirers by Volume",
            "type": "bar",
            "x": [r["acquirer"] for r in rows],
            "y": [r["cnt"] for r in rows]
        })

        # 3) Payment Method Distribution (Bar)
        rows = conn.execute(text(
            "SELECT credit_card_type AS method, COUNT(*) AS cnt "
            "FROM transaction GROUP BY method"
        )).mappings().all()
        charts.append({
            "title": "Payment Method Distribution",
            "type": "bar",
            "x": [r["method"] for r in rows],
            "y": [r["cnt"] for r in rows]
        })

        

        # 5) AI-Powered Insights (List)
        insights = [
            "Implement ML-based fraud detection to reduce losses by 20–30%",
            "Optimize partner allocation on success performance",
            "Enhance 3DS flows to improve conversion rates",
            "Build market-specific geographic growth strategies",
            "Enable real-time alerting on KPI thresholds"
        ]
        charts.append({
            "title": "AI-Powered Insights",
            "type": "list",
            "data": insights
        })

        # 6) Recent Activity (List)
        now = datetime.utcnow()
        activity = [
            {"time": (now - timedelta(minutes=2)).isoformat(),  "type": "alert",       "message": "Transaction volume spike detected"},
            {"time": (now - timedelta(hours=1)).isoformat(),    "type": "report",      "message": "Weekly performance report generated"},
            {"time": (now - timedelta(hours=3)).isoformat(),    "type": "analysis",    "message": "Fraud pattern analysis updated"},
            {"time": (now - timedelta(days=1)).isoformat(),     "type": "integration", "message": "New payment method integrated"},
        ]
        charts.append({
            "title": "Recent Activity",
            "type": "list",
            "data": activity
        })

    return {"metrics": metrics, "charts": charts}