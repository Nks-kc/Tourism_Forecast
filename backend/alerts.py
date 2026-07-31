from __future__ import annotations

import logging
from datetime import date

import pandas as pd
from data_store import load_country_arrivals
from forecasting.forecast import forecast
from notifications import (
    create_notification,
    get_forecast_snapshot,
    get_notification_settings,
    save_forecast_snapshot,
)
from watchlist import get_watchlist

logger = logging.getLogger(__name__)

ALERT_MODEL = "sarima"  # a stable, always-available model for alert scans
ALERT_HORIZON = 1


def _next_forecast_value(country: str) -> float | None:
    try:
        values = forecast(
            model_name=ALERT_MODEL, country=country, horizon=ALERT_HORIZON
        )
        return max(0.0, float(values[0]))
    except Exception as exc:  # noqa: BLE001 -- a single model failure shouldn't break the scan
        logger.warning("Alert scan: forecast failed for %s: %s", country, exc)
        return None


def _peak_month_for_country(country: str) -> int | None:
    try:
        df = load_country_arrivals()
    except FileNotFoundError:
        return None
    country_df = df[df["country"] == country]
    if country_df.empty:
        return None
    monthly_avg = country_df.groupby("month")["arrivals"].mean()
    return int(monthly_avg.idxmax())


def _days_until_next_occurrence(month: int, today: date) -> int:
    year = today.year if month >= today.month else today.year + 1
    target = date(year, month, 1)
    return (target - today).days


def check_forecast_change(
    user_id: int, country: str, threshold_pct: float
) -> dict | None:
    value = _next_forecast_value(country)
    if value is None:
        return None
    previous = get_forecast_snapshot(country, ALERT_HORIZON, ALERT_MODEL)
    save_forecast_snapshot(country, ALERT_HORIZON, ALERT_MODEL, value)
    if previous is None or previous == 0:
        return None
    pct_change = ((value - previous) / previous) * 100
    if abs(pct_change) < threshold_pct:
        return None
    direction = "increased" if pct_change > 0 else "decreased"
    return create_notification(
        user_id=user_id,
        title=f"Forecast change for {country}",
        message=(
            f"The forecast for {country} has {direction} by {abs(pct_change):.1f}% "
            f"(from {previous:.0f} to {value:.0f} projected arrivals)."
        ),
        type_="forecast_change",
        country=country,
    )


def check_low_arrival(
    user_id: int, country: str, threshold: float | None
) -> dict | None:
    if threshold is None:
        return None
    value = _next_forecast_value(country)
    if value is None or value >= threshold:
        return None
    return create_notification(
        user_id=user_id,
        title=f"Low arrivals expected for {country}",
        message=(
            f"Forecasted arrivals for {country} ({value:.0f}) are below your "
            f"threshold of {threshold:.0f}."
        ),
        type_="low_arrival",
        country=country,
    )


def check_seasonal_peak(user_id: int, country: str, lookahead_days: int) -> dict | None:
    peak_month = _peak_month_for_country(country)
    if peak_month is None:
        return None
    days_away = _days_until_next_occurrence(peak_month, date.today())
    if days_away > lookahead_days:
        return None
    month_name = pd.Timestamp(2000, peak_month, 1).strftime("%B")
    return create_notification(
        user_id=user_id,
        title=f"Seasonal peak approaching for {country}",
        message=(
            f"{country}'s historical peak tourism month ({month_name}) is "
            f"{days_away} day(s) away."
        ),
        type_="seasonal_peak",
        country=country,
    )


def run_watchlist_alerts(user_id: int) -> list[dict]:
    """Scan every watchlisted country for this user and create whichever
    alerts fire. Returns the notifications created."""
    settings = get_notification_settings(user_id)
    created = []
    for entry in get_watchlist(user_id):
        country = entry["country"]
        for check, arg in (
            (check_forecast_change, settings["change_threshold_pct"]),
            (check_low_arrival, settings["low_arrival_threshold"]),
            (check_seasonal_peak, settings["peak_lookahead_days"]),
        ):
            result = check(user_id, country, arg)
            if result:
                created.append(result)
    return created
