from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import text
from DB.connector import get_engine

engine = get_engine()

def get_date_ranges(filter_type: str, custom: tuple[date, date] = None):
    # For testing, fixed "today" timestamp
    base = datetime(2023, 12, 30, 23, 56, 0)
    today_date = base.date()

    if filter_type == 'Today':
        # Compare today vs yesterday
        start = today_date
        end = today_date
        comp_start = today_date - timedelta(days=1)
        comp_end = comp_start

    elif filter_type == 'Yesterday':
        # Yesterday vs day before yesterday
        start = today_date - timedelta(days=1)
        end = start
        comp_end = today_date - timedelta(days=2)
        comp_start = comp_end

    elif filter_type == 'Daily':
        # Yesterday vs 7-day avg prior week
        end = today_date - timedelta(days=1)
        start = end
        comp_end = end - timedelta(days=1)
        comp_start = comp_end - timedelta(days=6)

    elif filter_type == 'Weekly':
        # Last 7 days (excluding today) vs avg of prior 4-week span
        end = today_date - timedelta(days=1)
        start = end - timedelta(days=6)
        comp_end = start - timedelta(days=1)
        comp_start = comp_end - timedelta(days=27)

    elif filter_type == 'MTD':
        # Month-to-date vs full previous month
        start = today_date.replace(day=1)
        end = today_date
        prev_month_end = start - timedelta(days=1)
        comp_start = prev_month_end.replace(day=1)
        comp_end = prev_month_end

    elif filter_type == 'Monthly':
        # Last 3 months vs prior 3-month span
        # Note: last month vs prior 3 month 
        end = today_date
        start = (base - relativedelta(months=3) + timedelta(days=1)).date()
        comp_end = (base - relativedelta(months=3)).date()
        comp_start = (base - relativedelta(months=6) + timedelta(days=1)).date()

    elif filter_type == 'YTD':
        # Year-to-date vs same span last year
        start = today_date.replace(month=1, day=1)
        end = today_date
        comp_start = start.replace(year=start.year - 1)
        comp_end = comp_start + (end - start)

    elif filter_type == 'custom' and custom:
        # Custom span vs previous equal-length span
        start, end = custom
        length = end - start
        comp_end = start - timedelta(days=1)
        comp_start = comp_end - length

    else:
        raise ValueError(f"Unsupported filter: {filter_type}")

    return start, end, comp_start, comp_end


def fetch_one(conn, sql: str, params: dict):
    return float(conn.execute(text(sql), params).scalar() or 0.0)


def pct_diff(current: float, previous: float) -> float:
    if previous:
        return round((current - previous) / previous * 100, 2)
    return 0.0


def get_financial_performance_data(filter_type: str = 'YTD', custom: tuple[date, date] = None) -> dict:
    start, end, comp_start, comp_end = get_date_ranges(filter_type, custom)
    metrics, charts = [], []

    with engine.connect() as conn:
        # SQL templates
        sql_sum = "SELECT COALESCE(SUM(usd_value),0) FROM transaction WHERE date_time::date BETWEEN :s AND :e"
        sql_count = "SELECT COUNT(*)::float FROM transaction WHERE date_time::date BETWEEN :s AND :e"
        sql_avg = "SELECT COALESCE(AVG(usd_value),0) FROM transaction WHERE date_time::date BETWEEN :s AND :e"

        # 1) Total Transaction Volume
        curr_vol = fetch_one(conn, sql_sum, {'s': start, 'e': end})
        prev_val = fetch_one(conn, sql_sum, {'s': comp_start, 'e': comp_end})
        if filter_type == 'Daily':
            prev_val /= 7
        elif filter_type == 'Weekly':
            prev_val /= 4
        metrics.append({'title': 'Total Transaction Volume','value': round(curr_vol,2),'diff': pct_diff(curr_vol, prev_val)})

        # 2) Total Transactions
        curr_cnt = fetch_one(conn, sql_count, {'s': start, 'e': end})
        prev_cnt = fetch_one(conn, sql_count, {'s': comp_start, 'e': comp_end})
        if filter_type == 'Daily':
            prev_cnt /= 7
        elif filter_type == 'Weekly':
            prev_cnt /= 4
        metrics.append({'title': 'Total Transactions','value': int(curr_cnt),'diff': pct_diff(curr_cnt, prev_cnt)})

        # 3) Average Transaction Value
        if filter_type == 'Daily':
            curr_avg = fetch_one(conn, text("SELECT COALESCE(AVG(usd_value),0) FROM transaction WHERE date_time::date = :d"),{'d': start})
            prev_avg = fetch_one(conn, sql_avg, {'s': comp_start, 'e': comp_end})
        else:
            curr_avg = fetch_one(conn, sql_avg, {'s': start, 'e': end})
            prev_avg = fetch_one(conn, sql_avg, {'s': comp_start, 'e': comp_end})
        metrics.append({'title': 'Average Transaction Value','value': round(curr_avg,2),'diff': pct_diff(curr_avg, prev_avg)})

        # 4) Sales By Currency
        rows = conn.execute(text("SELECT transaction_currency AS name,SUM(usd_value) AS total_usd FROM transaction WHERE date_time::date BETWEEN :s AND :e GROUP BY transaction_currency"),{'s': start,'e': end}).mappings().all()
        total_usd = sum(r['total_usd'] for r in rows) or 1
        charts.append({'title':'Sales by Currency','type':'pie','data':[{'name':r['name'],'value':round(r['total_usd']/total_usd*100,1)} for r in rows]})

        # # 5) Processing Fee Analysis
        # rows = conn.execute(text("SELECT a.name AS acquirer,SUM((t.pricing_ic*t.usd_value)+t.gateway_fee) AS total_fees,SUM(t.amount) AS total_amt FROM transaction t JOIN acquirer a ON t.acquirer_id=a.id WHERE date_time::date BETWEEN :s AND :e GROUP BY a.name ORDER BY total_fees/NULLIF(SUM(t.amount),0) DESC"),{'s': start,'e': end}).mappings().all()
        # charts.append({'title':'Processing Fee Analysis','type':'bar','x':[r['acquirer'] for r in rows],'y':[round((r['total_fees']/r['total_amt'])*100,2) if r['total_amt'] else 0 for r in rows]})

    return {'metrics':metrics,'charts':charts}