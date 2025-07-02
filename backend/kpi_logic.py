import pandas as pd
import difflib

# Define KPI requirements with aliases
KPI_COLUMNS = {
    "transaction_value": ["transaction value", "usd value", "txn_amt"],
    "transaction_id": ["reference id", "ext reference id"],
    "fraud_amount": ["fraud amount$", "fraud", "fraud_flag"],
    "transaction_date": ["transaction date/ time", "date", "txn_date"],
    "city": ["city", "location", "billing_city"],
    "successful": ["successful", "is_success", "status"],
}


def find_best_column(possible_names, actual_columns):
    for name in possible_names:
        match = difflib.get_close_matches(name.lower(), [col.lower() for col in actual_columns], n=1, cutoff=0.7)
        if match:
            for col in actual_columns:
                if col.lower() == match[0]:
                    return col
    return None


def map_columns(df):
    mapping = {}
    for key, aliases in KPI_COLUMNS.items():
        match = find_best_column(aliases, df.columns)
        if match:
            mapping[key] = match
    return mapping


def compute_all_kpis(df: pd.DataFrame):
    df.columns = [col.strip() for col in df.columns]  # clean column names
    mapping = map_columns(df)
    kpis = {}

    # Safely convert numeric columns
    for key in ["transaction_value", "fraud_amount"]:
        col = mapping.get(key)
        if col and col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # Safely convert date column
    tx_date = mapping.get("transaction_date")
    if tx_date:
        df[tx_date] = pd.to_datetime(df[tx_date], errors='coerce')

    # 1. Average Transaction Amount
    tx_val = mapping.get("transaction_value")
    if tx_val:
        kpis["average_transaction_amount"] = round(df[tx_val].mean(skipna=True), 2)

    # 2. Transaction Volume
    tx_id = mapping.get("transaction_id")
    if tx_id:
        kpis["transaction_volume"] = df[tx_id].nunique()

    # 3. Fraud Rate
    fraud_col = mapping.get("fraud_amount")
    if fraud_col:
        fraud_txns = df[df[fraud_col] > 0]
        kpis["fraud_rate"] = round(len(fraud_txns) / len(df), 4) if len(df) > 0 else 0.0

    # 4. Transactions per day
    if tx_date:
        df_day = df[df[tx_date].notna()].copy()
        df_day["day"] = df_day[tx_date].dt.date
        daily_counts = df_day.groupby("day").size().reset_index(name="count")
        kpis["transactions_per_day"] = daily_counts.to_dict(orient="list")

    # 5. Transactions per month
    if tx_date:
        df_month = df[df[tx_date].notna()].copy()
        df_month["month"] = df_month[tx_date].dt.to_period("M").astype(str)
        monthly_counts = df_month.groupby("month").size().reset_index(name="count")
        kpis["transactions_per_month"] = monthly_counts.to_dict(orient="list")

    # 6. Top cities by volume
    city_col = mapping.get("city")
    if city_col:
        top_cities = df[city_col].value_counts().nlargest(10)
        kpis["top_cities"] = {"labels": top_cities.index.tolist(), "values": top_cities.values.tolist()}

    # 7. Top growing cities (monthly growth)
    if city_col and tx_date:
        df_growth = df[df[tx_date].notna()].copy()
        df_growth["month"] = df_growth[tx_date].dt.to_period("M").astype(str)
        growth_data = df_growth.groupby([city_col, "month"]).size().reset_index(name="count")
        pct_change = growth_data.groupby(city_col)["count"].pct_change()
        mean_growth = pct_change.groupby(growth_data[city_col]).mean().dropna().nlargest(5)
        kpis["top_growing_cities"] = {
            "cities": mean_growth.index.tolist(),
            "growth_rates": mean_growth.values.round(2).tolist()
        }

    # 8. Most risky cities (fraud rate)
    if city_col and fraud_col:
        df_fraud = df.copy()
        df_fraud["is_fraud"] = df[fraud_col] > 0
        fraud_rates = df_fraud.groupby(city_col)["is_fraud"].mean().nlargest(5)
        kpis["most_risky_cities"] = {
            "cities": fraud_rates.index.tolist(),
            "fraud_rates": fraud_rates.values.round(4).tolist()
        }

    # 9. Conversion Rate
    success_col = mapping.get("successful")
    if success_col and success_col in df.columns:
        converted = df[success_col].astype(str).str.upper().eq("Y").sum()
        total = len(df)
        conversion_rate = converted / total if total else 0.0
        kpis["conversion_rate"] = round(conversion_rate, 4)

    return kpis
