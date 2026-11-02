"""Stress-test the validation forecasts: how sure is the gain, and where does it fail?

Works from data/processed/validation_forecasts.parquet, so it needs no retraining and
touches no test weeks. Intervals resample whole weeks, because markets in the same
week move together and treating them as separate would overstate certainty.

Run from the project root:  python -m src.validate
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest import table

FORECASTS = Path("data/processed/validation_forecasts.parquet")
REPORT = Path("reports/validation.md")
SEED = 42
RESAMPLES = 2000
LONGEST = 4


def add_errors(rows):
    return rows.assign(
        base_error=(rows["this_week"] - rows["actual"]).abs() / rows["actual"],
        model_error=(rows["lightgbm"] - rows["actual"]).abs() / rows["actual"],
        base_rupees=(rows["this_week"] - rows["actual"]).abs(),
        model_rupees=(rows["lightgbm"] - rows["actual"]).abs())


def gain_interval(rows):
    """Percent reduction in error, with a 95% interval from resampling weeks."""
    weekly = rows.groupby("week")[["base_error", "model_error"]].sum().to_numpy()
    rng = np.random.default_rng(SEED)
    picks = rng.integers(0, len(weekly), (RESAMPLES, len(weekly)))
    totals = weekly[picks].sum(axis=1)
    gains = (1 - totals[:, 1] / totals[:, 0]) * 100
    low, high = np.percentile(gains, [2.5, 97.5])
    return round(float((1 - weekly[:, 1].sum() / weekly[:, 0].sum()) * 100), 1), round(float(low), 1), round(float(high), 1)


def summary(rows):
    results = []
    for (crop, horizon), part in rows.groupby(["Commodity", "horizon"]):
        gain, low, high = gain_interval(part)
        results.append({"crop": crop, "weeks_ahead": horizon, "gain_pct": gain, "interval_95": f"{low} to {high}",
                        "error_rupees_base": int(part["base_rupees"].mean()), "error_rupees_model": int(part["model_rupees"].mean()),
                        "typical_error_pct_base": round(float(part["base_error"].median() * 100), 1),
                        "typical_error_pct_model": round(float(part["model_error"].median() * 100), 1)})
    return pd.DataFrame(results)


def by_month(rows):
    part = rows[rows["horizon"] == LONGEST]
    grouped = part.groupby(["Commodity", part["week"].dt.month])[["base_error", "model_error"]].mean()
    gain = ((1 - grouped["model_error"] / grouped["base_error"]) * 100).round(0).astype(int).unstack(0)
    return gain.rename_axis("month").reset_index()


def by_market(rows):
    part = rows[rows["horizon"] == LONGEST]
    grouped = part.groupby(["Commodity", "State", "market"])[["base_error", "model_error"]].mean()
    grouped["gain"] = (1 - grouped["model_error"] / grouped["base_error"]) * 100
    shares = grouped.groupby("Commodity")["gain"].agg(
        markets="size", beat_baseline=lambda g: int((g > 0).sum()), worst=lambda g: round(g.min(), 1), best=lambda g: round(g.max(), 1))
    worst = grouped.reset_index().nsmallest(6, "gain")[["Commodity", "State", "market", "gain"]].round(1)
    return shares.reset_index(), worst


def main():
    rows = add_errors(pd.read_parquet(FORECASTS))
    main_table = summary(rows)
    months = by_month(rows)
    shares, worst = by_market(rows)
    print(main_table.to_string(index=False)); print(months.to_string(index=False)); print(shares.to_string(index=False)); print(worst.to_string(index=False))
    REPORT.write_text("\n".join([
        "# Validation", "", "Validation weeks only. Written by `python -m src.validate`. Prices are rupees per quintal.", "",
        "## Gain over next week equals this week", "",
        "Intervals resample whole weeks. Typical error is the median, which big misses affect less.", "", table(main_table), "",
        f"## Gain by target month, {LONGEST} weeks ahead (percent)", "", table(months), "",
        f"## Markets, {LONGEST} weeks ahead", "", table(shares), "", "Hardest markets:", "", table(worst), "",
    ]), encoding="utf-8")


if __name__ == "__main__":
    main()
