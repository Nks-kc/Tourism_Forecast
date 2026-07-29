from __future__ import annotations

import glob
import logging
from pathlib import Path

import pandas as pd
from config import EXTERNAL_DATA_GLOB, INTERIM_RECONCILED_CSV, INTERIM_VALIDATION_REPORT
from feature_engineering.data_loader import load_data

logger = logging.getLogger(__name__)
MONTHLY_TOTALS_SHEET = "Tourist Arrival_month"
NATIONALITY_SHEET = "Tourist Arrival_Nationalities_m"
AGGREGATE_TOLERANCE = 2


def _find_external_workbook() -> Path | None:
    matches = sorted(glob.glob(EXTERNAL_DATA_GLOB))
    return Path(matches[0]) if matches else None


def _load_monthly_totals(workbook_path: Path) -> pd.DataFrame:
    import openpyxl

    wb = openpyxl.load_workbook(workbook_path, data_only=True)
    ws = wb[MONTHLY_TOTALS_SHEET]
    records = []
    for row in ws.iter_rows(values_only=True):
        year = row[0]
        if not isinstance(year, int):
            continue
        for month_index in range(12):
            value = row[1 + month_index]
            if value is not None:
                records.append(
                    {"year": year, "month": month_index + 1, "total_external": value}
                )
    return pd.DataFrame(records)


def _load_nationality_breakdown(workbook_path: Path) -> pd.DataFrame:
    import openpyxl

    wb = openpyxl.load_workbook(workbook_path, data_only=True)
    ws = wb[NATIONALITY_SHEET]
    records = []
    current_country = None
    for row in ws.iter_rows(min_row=4, values_only=True):
        country = row[0] if row[0] else current_country
        current_country = country
        year = row[1]
        if country is None or not isinstance(year, int):
            continue
        for month_index in range(12):
            value = row[2 + month_index]
            if value is not None:
                records.append(
                    {
                        "country": country,
                        "year": year,
                        "month": month_index + 1,
                        "arrivals_external": value,
                    }
                )
    return pd.DataFrame(records)


def _check_aggregate_totals(
    raw_df: pd.DataFrame, monthly_totals: pd.DataFrame
) -> list[str]:
    raw_totals = (
        raw_df.groupby(["year", "month"], as_index=False)["arrivals"]
        .sum()
        .rename(columns={"arrivals": "total_raw"})
    )
    merged = monthly_totals.merge(raw_totals, on=["year", "month"], how="outer")
    merged["diff"] = (merged["total_external"] - merged["total_raw"]).abs()
    notes = []
    for row in merged.itertuples():
        if pd.isna(row.total_external) or pd.isna(row.total_raw):
            continue
        if row.diff > AGGREGATE_TOLERANCE:
            notes.append(
                f"{row.year}-{row.month:02d}: raw total {row.total_raw:.0f} vs external total {row.total_external:.0f} (diff {row.diff:.0f})"
            )
    return notes


def _reconcile_others(
    raw_df: pd.DataFrame, nationality_breakdown: pd.DataFrame
) -> tuple[pd.DataFrame, list[str]]:
    reconciled = raw_df.copy()
    notes = []
    grand_total = nationality_breakdown[
        nationality_breakdown["country"] == "Grand Total"
    ].set_index(["year", "month"])["arrivals_external"]
    named_sum = (
        nationality_breakdown[
            ~nationality_breakdown["country"].isin(["Grand Total", "Others"])
        ]
        .groupby(["year", "month"])["arrivals_external"]
        .sum()
    )
    stated_others = nationality_breakdown[
        nationality_breakdown["country"] == "Others"
    ].set_index(["year", "month"])["arrivals_external"]
    implied_others = (grand_total - named_sum).dropna()
    for (year, month), implied_value in implied_others.items():
        stated_value = stated_others.get((year, month))
        if (
            stated_value is not None
            and abs(stated_value - implied_value) <= AGGREGATE_TOLERANCE
        ):
            continue
        mask = (
            (reconciled["country"] == "Others")
            & (reconciled["year"] == year)
            & (reconciled["month"] == month)
        )
        if not mask.any():
            continue
        current_value = reconciled.loc[mask, "arrivals"].iloc[0]
        if abs(current_value - implied_value) <= AGGREGATE_TOLERANCE:
            continue
        reconciled.loc[mask, "arrivals"] = implied_value
        notes.append(
            f"{year}-{month:02d}: 'Others' corrected from {current_value:.0f} to {implied_value:.0f} (source workbook's stated Others, {(stated_value if stated_value is not None else 'missing')}, disagreed with Grand Total minus named countries)"
        )
    return (reconciled, notes)


def reconcile(raw_df: pd.DataFrame) -> tuple[pd.DataFrame, dict]:
    workbook_path = _find_external_workbook()
    if workbook_path is None:
        logger.warning(
            "No .xlsx file found in data/external/ -- skipping cross-validation. The raw dataset will be used as-is."
        )
        return (
            raw_df,
            {
                "external_source": None,
                "status": "skipped",
                "reason": "no .xlsx file found in data/external/",
            },
        )
    logger.info("Cross-validating against %s", workbook_path.name)
    monthly_totals = _load_monthly_totals(workbook_path)
    nationality_breakdown = _load_nationality_breakdown(workbook_path)
    aggregate_notes = _check_aggregate_totals(raw_df, monthly_totals)
    reconciled_df, correction_notes = _reconcile_others(raw_df, nationality_breakdown)
    report = {
        "external_source": workbook_path.name,
        "status": "completed",
        "months_checked_against_aggregate_totals": int(
            monthly_totals[["year", "month"]].drop_duplicates().shape[0]
        ),
        "aggregate_total_discrepancies": aggregate_notes,
        "others_corrections": correction_notes,
    }
    if aggregate_notes:
        logger.warning(
            "%d month(s) differ from the external aggregate totals by more than %d -- see the validation report for details.",
            len(aggregate_notes),
            AGGREGATE_TOLERANCE,
        )
    if correction_notes:
        logger.info(
            "Reconciled 'Others' for %d month(s) against the external nationality breakdown.",
            len(correction_notes),
        )
    else:
        logger.info(
            "'Others' already matches the external source for every month checked."
        )
    return (reconciled_df, report)


def _write_report(report: dict, path: Path) -> None:
    lines = [
        "Data cross-validation report",
        "=" * 60,
        f"External source: {report['external_source'] or '(none found)'}",
        f"Status: {report['status']}",
    ]
    if report["status"] == "skipped":
        lines.append(f"Reason: {report['reason']}")
    else:
        lines.append(
            f"Months checked against aggregate totals: {report['months_checked_against_aggregate_totals']}"
        )
        lines.append("")
        lines.append(
            f"Aggregate total discrepancies (> {AGGREGATE_TOLERANCE} units): {len(report['aggregate_total_discrepancies'])}"
        )
        for note in report["aggregate_total_discrepancies"]:
            lines.append(f"  - {note}")
        lines.append("")
        lines.append(
            f"'Others' corrections applied: {len(report['others_corrections'])}"
        )
        for note in report["others_corrections"]:
            lines.append(f"  - {note}")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(lines) + "\n")


def run_cross_validation() -> pd.DataFrame:
    raw_df = load_data()
    reconciled_df, report = reconcile(raw_df)
    Path(INTERIM_RECONCILED_CSV).parent.mkdir(parents=True, exist_ok=True)
    reconciled_df.to_csv(INTERIM_RECONCILED_CSV, index=False)
    _write_report(report, Path(INTERIM_VALIDATION_REPORT))
    logger.info("Reconciled dataset written to %s", INTERIM_RECONCILED_CSV)
    logger.info("Validation report written to %s", INTERIM_VALIDATION_REPORT)
    return reconciled_df


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO, format="%(levelname)s - %(message)s")
    run_cross_validation()
