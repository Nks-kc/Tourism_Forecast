from __future__ import annotations

import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from config import OUTPUTS_REPORTS_DIR
from data_store import load_country_arrivals
from evaluation.comparison import ModelComparison
from forecasting.forecast import forecast, get_dataset_last_date
from forecasting.utils import next_month
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import inch
from reportlab.platypus import (
    PageBreak,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
    Table,
    TableStyle,
)

MODEL_KEYS = ["mlp", "linear_regression", "sarima", "holtwinters"]
MODEL_DISPLAY_NAMES = {
    "mlp": "MLP",
    "linear_regression": "Linear Regression",
    "sarima": "SARIMA",
    "holtwinters": "Holt-Winters",
}
DEFAULT_HORIZON = 6

_styles = getSampleStyleSheet()
_H1 = ParagraphStyle("H1", parent=_styles["Heading1"], spaceAfter=10)
_H2 = ParagraphStyle("H2", parent=_styles["Heading2"], spaceBefore=14, spaceAfter=6)
_BODY = _styles["BodyText"]


def _future_month_labels(last_date, horizon: int) -> list[str]:
    labels, current = [], last_date
    for _ in range(horizon):
        current = next_month(current)
        labels.append(current.strftime("%Y-%m"))
    return labels


def _forecast_all_models(country: str, horizon: int) -> dict:
    last_date = get_dataset_last_date()
    months = _future_month_labels(last_date, horizon)
    results = {}
    for key in MODEL_KEYS:
        try:
            values = forecast(model_name=key, country=country, horizon=horizon)
            results[MODEL_DISPLAY_NAMES[key]] = {
                "months": months,
                "arrivals": [round(max(0.0, float(v)), 2) for v in values],
            }
        except Exception:  # noqa: BLE001, S112
            continue
    return results


def _historical_analysis(country: str) -> dict:
    df = load_country_arrivals()
    country_df = df[df["country"] == country].copy()
    if country_df.empty:
        return {}
    country_df["date"] = pd.to_datetime(country_df["date"])
    country_df = country_df.sort_values("date")
    monthly_avg = country_df.groupby("month")["arrivals"].mean()
    peak_month = int(monthly_avg.idxmax())
    trough_month = int(monthly_avg.idxmin())
    yearly = country_df.groupby(country_df["date"].dt.year)["arrivals"].sum()
    yoy_growth = None
    if len(yearly) >= 2:
        prev, latest = yearly.iloc[-2], yearly.iloc[-1]
        if prev:
            yoy_growth = round((latest - prev) / prev * 100, 2)
    return {
        "peak_month": pd.Timestamp(2000, peak_month, 1).strftime("%B"),
        "trough_month": pd.Timestamp(2000, trough_month, 1).strftime("%B"),
        "peak_avg_arrivals": round(float(monthly_avg.max()), 1),
        "trough_avg_arrivals": round(float(monthly_avg.min()), 1),
        "latest_year": int(yearly.index[-1]) if len(yearly) else None,
        "latest_year_total": round(float(yearly.iloc[-1]), 0) if len(yearly) else None,
        "yoy_growth_pct": yoy_growth,
    }


def _model_comparison_section() -> dict:
    try:
        results = ModelComparison.load_results()
        return ModelComparison.compare(results)
    except (FileNotFoundError, ValueError):
        return {}


def _growth_pct(arrivals: list[float]) -> float | None:
    if len(arrivals) < 2 or arrivals[0] == 0:
        return None
    return round((arrivals[-1] - arrivals[0]) / arrivals[0] * 100, 2)


def _recommendations(
    country: str, history: dict, growth_pct: float | None
) -> list[str]:
    peak = history.get("peak_month", "the peak season")
    recs = [
        f"Hotels: Align staffing and room-inventory availability with the {peak} peak; consider dynamic pricing ahead of that window.",
        f"Travel agencies: Prioritize marketing spend and package availability for {country} in the lead-up to {peak}.",
        f"Trekking operators: Ensure guide and permit capacity is booked well ahead of the {peak} peak, and plan off-season promotions around {history.get('trough_month', 'the low season')}.",
        "Tourism planners: Use the forecast trend below to size seasonal infrastructure, transport, and public-service needs.",
    ]
    if growth_pct is not None:
        if growth_pct > 0:
            recs.insert(
                0,
                f"Overall outlook: Arrivals from {country} are expected to grow "
                f"{growth_pct:.1f}% over the forecast window -- businesses should prepare "
                "for increased demand.",
            )
        elif growth_pct < 0:
            recs.insert(
                0,
                f"Overall outlook: Arrivals from {country} are expected to decline "
                f"{abs(growth_pct):.1f}% over the forecast window -- consider promotional "
                "campaigns or cost management to offset softer demand.",
            )
    return recs


def _country_section(elements: list, country: str, horizon: int) -> None:
    elements.append(Paragraph(country, _H1))

    forecasts = _forecast_all_models(country, horizon)
    history = _historical_analysis(country)

    # Forecast summary
    elements.append(Paragraph("Forecast Summary", _H2))
    if forecasts:
        primary_name = next(iter(forecasts))
        primary = forecasts[primary_name]
        growth_pct = _growth_pct(primary["arrivals"])
        summary_lines = [
            f"Forecast period: {primary['months'][0]} to {primary['months'][-1]} ({horizon}-month horizon).",
            f"Forecasted arrivals ({primary_name}): {primary['arrivals'][0]:,.0f} to {primary['arrivals'][-1]:,.0f}.",
        ]
        if growth_pct is not None:
            direction = "growth" if growth_pct >= 0 else "decline"
            summary_lines.append(
                f"Projected {direction} over the horizon: {abs(growth_pct):.1f}%."
            )
        for line in summary_lines:
            elements.append(Paragraph(line, _BODY))
    else:
        growth_pct = None
        elements.append(
            Paragraph("No forecast could be generated for this country.", _BODY)
        )

    # Historical analysis
    elements.append(Paragraph("Historical Analysis", _H2))
    if history:
        elements.append(
            Paragraph(
                f"Peak season historically occurs in {history['peak_month']} "
                f"(avg. {history['peak_avg_arrivals']:,.0f} arrivals/month); the quietest "
                f"month is typically {history['trough_month']} "
                f"(avg. {history['trough_avg_arrivals']:,.0f} arrivals/month).",
                _BODY,
            )
        )
        if history.get("yoy_growth_pct") is not None:
            elements.append(
                Paragraph(
                    f"Year-over-year arrivals in {history['latest_year']} changed by "
                    f"{history['yoy_growth_pct']:.1f}% versus the prior year "
                    f"(total: {history['latest_year_total']:,.0f}).",
                    _BODY,
                )
            )
    else:
        elements.append(
            Paragraph("No historical data available for this country.", _BODY)
        )

    # Forecast analysis
    elements.append(Paragraph("Forecast Analysis", _H2))
    analysis_bits = []
    if history:
        analysis_bits.append(
            f"Expect seasonal peaks around {history['peak_month']} and quieter demand "
            f"around {history['trough_month']}, consistent with historical patterns."
        )
    if growth_pct is not None:
        trend = "an upward" if growth_pct >= 0 else "a downward"
        analysis_bits.append(
            f"The forecast points to {trend} trend ({growth_pct:+.1f}% over the horizon), "
            "which should inform staffing, inventory, and capacity planning."
        )
    if not analysis_bits:
        analysis_bits.append(
            "Insufficient data to generate a detailed forecast analysis."
        )
    for bit in analysis_bits:
        elements.append(Paragraph(bit, _BODY))

    # Stakeholder recommendations
    elements.append(Paragraph("Stakeholder Recommendations", _H2))
    for rec in _recommendations(country, history, growth_pct):
        elements.append(Paragraph(f"\u2022 {rec}", _BODY))

    elements.append(Spacer(1, 0.2 * inch))


def _model_comparison_table(elements: list) -> None:
    comparison = _model_comparison_section()
    elements.append(Paragraph("Model Comparison", _H1))
    if not comparison:
        elements.append(
            Paragraph(
                "No model evaluation results are available. Run 'python train.py' first.",
                _BODY,
            )
        )
        return
    elements.append(
        Paragraph(
            f"Best-performing model: <b>{comparison['best_model']}</b> "
            f"(lowest {comparison['primary_metric']}, the primary ranking metric).",
            _BODY,
        )
    )
    data = [["Model", "MAE", "RMSE", "MAPE (%)", "Best Overall"]]
    for name, metrics in comparison["models"].items():
        data.append(
            [
                name,
                f"{metrics['MAE']['value']:.2f}",
                f"{metrics['RMSE']['value']:.2f}",
                f"{metrics['MAPE']['value']:.2f}",
                "Yes" if metrics["is_best_overall"] else "",
            ]
        )
    table = Table(data, hAlign="LEFT")
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1f2937")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                (
                    "ROWBACKGROUNDS",
                    (0, 1),
                    (-1, -1),
                    [colors.white, colors.HexColor("#f3f4f6")],
                ),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("TOPPADDING", (0, 0), (-1, -1), 4),
                ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
            ]
        )
    )
    elements.append(table)
    elements.append(Spacer(1, 0.25 * inch))


def generate_report(
    owner_username: str,
    report_type: str,
    countries: list[str],
    horizon: int = DEFAULT_HORIZON,
) -> Path:
    """Build the PDF and return its path on disk. `report_type` is one of
    'watchlist', 'country', or 'countries' -- purely descriptive metadata."""
    Path(OUTPUTS_REPORTS_DIR).mkdir(parents=True, exist_ok=True)
    filename = f"report_{owner_username}_{uuid.uuid4().hex[:8]}.pdf"
    path = Path(OUTPUTS_REPORTS_DIR) / filename

    doc = SimpleDocTemplate(str(path), pagesize=letter, title="Tourism Forecast Report")
    elements = [
        Paragraph("Tourism Forecast Report", _H1),
        Paragraph(
            f"Generated for: {owner_username} on "
            f"{datetime.now(tz=timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
            _BODY,
        ),
        Paragraph(f"Countries covered: {', '.join(countries)}", _BODY),
        Spacer(1, 0.2 * inch),
    ]

    for i, country in enumerate(countries):
        _country_section(elements, country, horizon)
        if i < len(countries) - 1:
            elements.append(PageBreak())

    elements.append(PageBreak())
    _model_comparison_table(elements)

    doc.build(elements)
    return path
