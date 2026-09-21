"""
Forecast service using Nixtla TimeGPT.
This module calls an external AI API - no machine learning code here.
"""

import os
import pandas as pd
from datetime import date, timedelta
from dotenv import load_dotenv
from nixtla import NixtlaClient

load_dotenv()

client = NixtlaClient(api_key=os.getenv("TIMEGPT_API_KEY"))


def generate_forecast(product_id, user_id, days=14):
    """
    Fetches historical sales for a product and requests a forecast from TimeGPT.
    Returns a list of (date, forecast_value) tuples.
    """
    from models import SalesRecord

    end_date = date.today()
    start_date = end_date - timedelta(days=60)

    records = SalesRecord.query.filter(
        SalesRecord.product_id == product_id,
        SalesRecord.user_id == user_id,
        SalesRecord.date >= start_date
    ).order_by(SalesRecord.date).all()

    if not records:
        return []

    daily = {}
    for r in records:
        daily[r.date] = daily.get(r.date, 0) + r.revenue

    start = min(daily.keys())
    end = max(daily.keys())
    filled = []
    d = start
    while d <= end:
        filled.append({"ds": d.isoformat(), "y": daily.get(d, 0.0)})
        d += timedelta(days=1)

    if len(filled) < 10:
        return []

    df = pd.DataFrame(filled)

    try:
        forecast_df = client.forecast(
            df=df,
            h=days,
            freq="D",
            time_col="ds",
            target_col="y",
        )
    except Exception as e:
        print(f"TimeGPT API error: {e}")
        return []

    result = []
    for _, row in forecast_df.iterrows():
        result.append((row["ds"].date(), round(row["TimeGPT"], 2)))

    return result


def generate_recommendation(forecast):
    """
    Takes the forecast list [(date, value), ...] and returns a dict of
    rule-based recommendations. The safety margin adapts to the trend:
        Rising  -> restock 20% above forecast (avoid stockouts)
        Stable  -> restock 10% above forecast (normal buffer)
        Falling -> restock 10% below forecast (avoid overstock)
    """
    if not forecast or len(forecast) < 2:
        return None

    values = [v for _, v in forecast]
    total = sum(values)
    avg_daily = total / len(values)

    # Trend: compare first half vs second half of the forecast horizon
    half = len(values) // 2
    first_half_avg = sum(values[:half]) / half if half else 0
    second_half_avg = sum(values[half:]) / (len(values) - half) if (len(values) - half) else 0

    if second_half_avg > first_half_avg * 1.05:
        trend = "Rising"
        trend_note = "Demand is expected to increase. Restock above the forecast to avoid stockouts."
        multiplier = 1.20
        margin_label = "20% above forecast"
    elif second_half_avg < first_half_avg * 0.95:
        trend = "Falling"
        trend_note = "Demand is expected to decrease. Reduce restocking to avoid overstock."
        multiplier = 0.90
        margin_label = "10% below forecast"
    else:
        trend = "Stable"
        trend_note = "Demand is expected to remain steady. Standard restocking buffer applies."
        multiplier = 1.10
        margin_label = "10% above forecast"

    recommended_restock = round(total * multiplier, 2)

    peak_date, peak_value = max(forecast, key=lambda x: x[1])

    return {
        "total_forecast": round(total, 2),
        "avg_daily": round(avg_daily, 2),
        "trend": trend,
        "trend_note": trend_note,
        "recommended_restock": recommended_restock,
        "margin_label": margin_label,
        "peak_date": peak_date.isoformat() if hasattr(peak_date, "isoformat") else str(peak_date),
        "peak_value": round(peak_value, 2),
    }