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