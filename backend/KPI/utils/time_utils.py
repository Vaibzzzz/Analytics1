# services/utils/time_filters.py
from typing import Optional, Tuple
from datetime import date, datetime, timedelta
from dateutil.relativedelta import relativedelta
from sqlalchemy import text

def get_date_ranges(filter_type: str, custom: Optional[tuple[date, date]]) -> tuple[date, date, date, date]:
    """
    Given a filter name and optional custom (start, end) dates,
    returns (start, end, comp_start, comp_end) date windows
    for current vs. comparison periods.
    """
    # Use a fixed “now” for testing/demo; replace with datetime.now() in prod
    base = datetime(2023, 12, 30, 23, 56, 0)
    today_date = base.date()

    if filter_type == 'Today':
        start = end = today_date
        comp_start = comp_end = today_date - timedelta(days=1)

    elif filter_type == 'Yesterday':
        start = end = today_date - timedelta(days=1)
        comp_start = comp_end = today_date - timedelta(days=2)

    elif filter_type == 'Daily':
        end = today_date - timedelta(days=1)
        start = end
        comp_end = end - timedelta(days=1)
        comp_start = comp_end - timedelta(days=6)

    elif filter_type == 'Weekly':
        end = today_date - timedelta(days=1)
        start = end - timedelta(days=6)
        comp_end = start - timedelta(days=1)
        comp_start = comp_end - timedelta(days=27)

    elif filter_type == 'MTD':
        start = today_date.replace(day=1)
        end = today_date
        prev_month_end = start - timedelta(days=1)
        comp_start = prev_month_end.replace(day=1)
        comp_end = prev_month_end

    elif filter_type == 'Monthly':
        # previous month vs. the three months before it
        first_of_this = today_date.replace(day=1)
        prev_month_end = first_of_this - timedelta(days=1)
        prev_month_start = prev_month_end.replace(day=1)

        start = prev_month_start
        end   = prev_month_end

        comp_start = (prev_month_start - relativedelta(months=3))
        comp_end   = prev_month_start - timedelta(days=1)

    elif filter_type == 'YTD':
        start = today_date.replace(month=1, day=1)
        end   = today_date
        comp_start = start.replace(year=start.year - 1)
        comp_end   = comp_start + (end - start)

    elif filter_type == 'custom' and custom:
        start, end = custom
        length = end - start
        comp_end = start - timedelta(days=1)
        comp_start = comp_end - length

    else:
        raise ValueError(f"Unsupported filter: {filter_type}")

    return start, end, comp_start, comp_end


def fetch_one(conn, sql: str, params: dict):
    """
    Executes a scalar SQL query and returns its single numeric result.
    Falls back to 0.0 if nothing is returned.
    """
    return float(conn.execute(text(sql), params).scalar() or 0.0)


def pct_diff(current: float, previous: float) -> float:
    """
    Returns the percentage difference between current and previous:
      (current - previous) / previous * 100,
    rounded to 2 decimals, or 0 if previous is zero.
    """
    if previous:
        return round((current - previous) / previous * 100, 2)
    return 0.0
