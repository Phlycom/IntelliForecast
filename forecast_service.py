import random
from datetime import date, timedelta
from models import SalesRecord


def generate_forecast(product_id, user_id, days=14):
    """
    Mock forecast service.
    Takes the last 30 days of sales for a product, computes a 7-day
    moving average, and projects a 14-day forecast with slight variation.
    This is a placeholder that will later be replaced with AWS Forecast API calls.
    """
    today = date.today()
    start_date = today - timedelta(days=30)

    records = SalesRecord.query.filter(
        SalesRecord.product_id == product_id,
        SalesRecord.user_id == user_id,
        SalesRecord.date >= start_date
    ).order_by(SalesRecord.date).all()

    if not records:
        return []

    daily_totals = {}
    for r in records:
        daily_totals[r.date] = daily_totals.get(r.date, 0) + r.revenue

    dates = sorted(daily_totals.keys())

    if len(dates) < 7:
        avg = sum(daily_totals.values()) / len(daily_totals)
    else:
        last_7 = [daily_totals[d] for d in dates[-7:]]
        avg = sum(last_7) / 7

    random.seed(42)
    forecast = []
    last_date = dates[-1]
    for i in range(1, days + 1):
        next_date = last_date + timedelta(days=i)
        noise = random.uniform(-0.15, 0.15)
        value = round(avg * (1 + noise + i * 0.01), 2)
        forecast.append((next_date, value))

    return forecast