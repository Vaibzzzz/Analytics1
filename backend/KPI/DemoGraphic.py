from sqlalchemy import text
from DB.connector import get_engine
from KPI.utils.time_utils import fetch_one, get_date_ranges, pct_diff
from typing import Optional

engine = get_engine()

MERCHANT_ID = 26  # hardcoded merchant ID


def get_demo_kpi_data():
    metrics = []
    charts = []

    with engine.connect() as conn:
        # Metric Card: Unique Cities where merchant is active
        city_count = fetch_one(
            conn,
            "SELECT COUNT(DISTINCT city) FROM transaction WHERE merchant_id = :m_id",
            {"m_id": MERCHANT_ID}
        )
        metrics.append({
            "title": "Cities Operational",
            "value": int(city_count)
        })

        # Chart: Success Rate by City
        rows = conn.execute(text("""
            SELECT city, SUM(amount) AS total_amount
            FROM transaction
            WHERE merchant_id = :m_id
            GROUP BY city
            ORDER BY total_amount DESC
            LIMIT 20
        """), {"m_id": MERCHANT_ID}).mappings().all()

        charts.append({
            "title": "Transaction Amount by City",
            "type": "horizontal_bar",
            "x": [round(r["total_amount"], 2) for r in rows],
            "y": [r["city"] for r in rows],
            "series": [
                {"name": "Transaction Amount", "data": [round(r["total_amount"], 2) for r in rows]}
            ]
        })

    return {"metrics": metrics, "charts": charts}
