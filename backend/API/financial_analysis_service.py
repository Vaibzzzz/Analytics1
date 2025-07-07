from sqlalchemy import text
from DB.connector import get_engine

engine = get_engine()

def get_financial_analysis_data() -> dict:
    """
    Returns the financial analysis data for the dashboard.
    """
    
    metrics = []
    charts = []

    with engine.connect() as conn:
        total_volume = conn.execute(
            text("SELECT COALESCE(SUM(amount), 0) FROM transaction")
        ).scalar() or 0.0
        avg_value = conn.execute(
            text("SELECT COALESCE(AVG(amount), 0) FROM transaction")
        ).scalar() or 0.0

        metrics += [
            {"title": "Total Transaction Volume",  "value": round(float(total_volume), 2)},
            {"title": "Average Transaction Value", "value": round(float(avg_value), 2)},
        ]

        distinct_currencies = conn.execute(
            text("SELECT COUNT(DISTINCT transaction_currency) FROM transaction")
        ).scalar() or 0

        metrics += [
            {"title": "Distinct Currencies", "value": distinct_currencies},
        ]

        # ─── Charts ────────────────────────────────────────────────────────
        # 1) Revenue by Currency (Pie)
        rows = conn.execute(
            text("SELECT transaction_currency AS name, SUM(amount) AS total FROM transaction GROUP BY transaction_currency")
        ).mappings().all()
        total = sum(r["total"] for r in rows) or 1
        charts.append({
            "title": "Revenue by Currency",
            "type": "pie",
            "data": [
                {"name": r["name"], "value": round(r["total"] / total * 100, 1)}
                for r in rows
            ]
        })

    return { "metrics": metrics, "charts": charts }