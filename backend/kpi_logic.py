import pandas as pd
import difflib

KPI_COLUMNS = {
    "transaction_value": ["usd_value", "amount", "transaction amount"],
    "transaction_id": ["i_transaction_id", "internal_transaction_id"],
    "fraud_flag": ["fraud", "is_fraud"],
    "transaction_date": ["date_time", "timestamp", "created_at"],
    "city": ["city", "location", "billing_city"],
    "successful": ["status"],
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

    # Numeric Conversion
    if 'transaction_value' in mapping:
        df[mapping['transaction_value']] = pd.to_numeric(df[mapping['transaction_value']], errors='coerce')

    if 'fraud_flag' in mapping:
        df[mapping['fraud_flag']] = pd.to_numeric(df[mapping['fraud_flag']], errors='coerce')

    if 'transaction_date' in mapping:
        df[mapping['transaction_date']] = pd.to_datetime(df[mapping['transaction_date']], errors='coerce')

    # 1. Average Transaction Amount
    tx_val = mapping.get("transaction_value")
    if tx_val:
        kpis["average_transaction_amount"] = round(df[tx_val].mean(skipna=True), 2)

    # 2. Transaction Volume
    tx_id = mapping.get("transaction_id")
    if tx_id:
        kpis["transaction_volume"] = df[tx_id].nunique()

    # 3. Fraud Rate
    fraud_col = mapping.get("fraud_flag")
    if fraud_col:
        fraud_rate = df[fraud_col].sum() / len(df) if len(df) else 0.0
        kpis["fraud_rate"] = round(fraud_rate, 4)

    # 4. Conversion Rate
    success_col = mapping.get("successful")
    if success_col:
        converted = df[success_col].astype(str).str.upper().eq("Y").sum()
        kpis["conversion_rate"] = round(converted / len(df), 4) if len(df) else 0.0

    # 5. Transactions per day
    date_col = mapping.get("transaction_date")
    if date_col:
        df_day = df[df[date_col].notna()].copy()
        df_day['day'] = df_day[date_col].dt.date
        daily = df_day.groupby("day").size().reset_index(name="count")
        kpis["transactions_per_day"] = {
            "dates": daily['day'].astype(str).tolist(),
            "counts": daily['count'].tolist()
        }

    # 6. Transactions per month
    if date_col:
        df_month = df[df[date_col].notna()].copy()
        df_month['month'] = df_month[date_col].dt.to_period("M").astype(str)
        monthly = df_month.groupby("month").size().reset_index(name="count")
        kpis["transactions_per_month"] = {
            "months": monthly['month'].tolist(),
            "counts": monthly['count'].tolist()
        }

    # 7. Top Cities by Volume
    city_col = mapping.get("city")
    if city_col:
        top_cities = df[city_col].value_counts().nlargest(10)
        kpis["top_cities"] = {
            "labels": top_cities.index.tolist(),
            "values": top_cities.values.tolist()
        }

    # 8. Top Growing Cities
    if city_col and date_col:
        df_growth = df[df[date_col].notna()].copy()
        df_growth['month'] = df_growth[date_col].dt.to_period("M").astype(str)
        growth = df_growth.groupby([city_col, 'month']).size().reset_index(name='count')
        pct_change = growth.groupby(city_col)['count'].pct_change()
        avg_growth = pct_change.groupby(growth[city_col]).mean().dropna().nlargest(5)
        kpis['top_growing_cities'] = {
            "cities": avg_growth.index.tolist(),
            "growth_rates": avg_growth.values.round(2).tolist()
        }

    # 9. Most Risky Cities
    if city_col and fraud_col:
        df_risk = df.copy()
        df_risk['is_fraud'] = df[fraud_col] > 0
        risk = df_risk.groupby(city_col)['is_fraud'].mean().nlargest(5)
        kpis['most_risky_cities'] = {
            "cities": risk.index.tolist(),
            "fraud_rates": risk.values.round(4).tolist()
        }

    return kpis
