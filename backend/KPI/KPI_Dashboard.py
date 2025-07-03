from DB.connector import get_connection
import pandas as pd

def get_transaction_performance_data():
    conn = get_connection()

    metrics = []
    charts = []

    # Total Transactions
    df_txn_count = pd.read_sql("SELECT COUNT(*) AS total FROM transaction;", conn)
    metrics.append({
        "title": "Total Transactions",
        "value": int(df_txn_count.iloc[0]["total"])
    })

    # Total Value
    df_value = pd.read_sql("SELECT SUM(amount) AS total_value FROM transaction;", conn)
    metrics.append({
        "title": "Total Transaction Value",
        "value": float(round(df_value.iloc[0]["total_value"], 2))
    })

    # Avg Value
    df_avg = pd.read_sql("SELECT AVG(amount) AS avg_value FROM transaction;", conn)
    metrics.append({
        "title": "Average Transaction Value",
        "value": float(round(df_avg.iloc[0]["avg_value"], 2))
    })

    # Transactions per Acquirer
    df_acquirer = pd.read_sql("""
        SELECT acquirer_id, COUNT(*) AS txn_count
        FROM transaction
        GROUP BY acquirer_id
        ORDER BY txn_count DESC
        LIMIT 10;
    """, conn)

    charts.append({
        "title": "Transactions per Acquirer",
        "type": "bar",
        "x": df_acquirer["acquirer_id"].astype(str).tolist(),
        "y": [int(v) for v in df_acquirer["txn_count"].tolist()]  
    })

    conn.close()

    return {
        "metrics": metrics,
        "charts": charts
    }
