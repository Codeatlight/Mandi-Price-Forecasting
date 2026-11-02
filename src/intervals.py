"""Forecast ranges: a low and a high price that should hold the real price 80% of the time.

Quantile LightGBM predicts each end of the range. On its own it is often overconfident,
so each year's range is widened or narrowed by the misses seen in the previous year
(conformal calibration), using nothing from the year being scored. That makes the first
validation year a warm-up, and scores start the year after.

A simple band is the comparison: this week's price, moved by the 10th and 90th percentile
of past changes for that crop.

Run from the project root:  python -m src.intervals
"""
from pathlib import Path

import numpy as np
import pandas as pd

from src.backtest import HORIZONS, KEYS, TEST_START, VALIDATION_START, load_panel, spike_flags, table
from src.models import PARAMS, SOURCE_STATE, features_for, long_form, rolling_forecast

REPORT = Path("reports/intervals.md")
FORECASTS = Path("data/processed/validation_intervals.parquet")
LOW, HIGH = 0.1, 0.9
TARGET_COVERAGE = 0.8
FIRST_SCORED_YEAR = VALIDATION_START.year + 1


def quantile_params(alpha):
    return {**PARAMS, "objective": "quantile", "alpha": alpha}


def conformal_shift(low, high, actual):
    """How far both ends must move, in log price, for 80% of last year's prices to fall inside."""
    miss = np.maximum(np.log(low) - np.log(actual), np.log(actual) - np.log(high))
    rank = min(1.0, np.ceil((len(miss) + 1) * TARGET_COVERAGE) / len(miss))
    return float(np.quantile(miss, rank))


def calibrate(rows):
    """Apply each previous year's correction to the next year."""
    years = rows["week"].dt.year
    kept = []
    for year in range(FIRST_SCORED_YEAR, TEST_START.year + 1):
        before = rows[years == year - 1]
        shift = conformal_shift(before["low"], before["high"], before["actual"])
        kept.append(rows[years == year].assign(low_cal=lambda d: d["low"] * np.exp(-shift),
                                               high_cal=lambda d: d["high"] * np.exp(shift), shift=shift))
    return pd.concat(kept)


def simple_band(part, rows, horizon):
    """Past changes for the crop, measured only on targets before each year."""
    logged = np.log(part.ffill(limit=3))
    changes = long_form(np.log(part) - logged.shift(horizon), "change").dropna()
    weeks = changes.index.get_level_values(0)
    out = []
    years = rows["week"].dt.year
    for year in sorted(years.unique()):
        past = changes[weeks < pd.Timestamp(year, 1, 1)]
        low, high = past.quantile([LOW, HIGH])
        out.append(rows[years == year].assign(low_band=lambda d: d["last"] * np.exp(low), high_band=lambda d: d["last"] * np.exp(high)))
    return pd.concat(out)


def report_row(rows, low, high):
    inside = rows["actual"].between(rows[low], rows[high])
    width = (rows[high] - rows[low]) / rows["actual"]
    return round(float(inside.mean() * 100), 1), round(float(width.median() * 100), 1)


def main():
    panel = load_panel()
    spikes = spike_flags(panel)
    crops = panel.columns.get_level_values("Commodity")
    summary, in_spikes, by_year, kept = [], [], [], []
    for crop in sorted(set(crops)):
        part = panel.loc[:, crops == crop]
        features = features_for(part, SOURCE_STATE[crop])
        for horizon in HORIZONS:
            print(crop, horizon, flush=True)
            low, _ = rolling_forecast(part, features, horizon, params=quantile_params(LOW))
            high, _ = rolling_forecast(part, features, horizon, params=quantile_params(HIGH))
            actual = long_form(part, "actual")
            actual.index.names = ["week", *KEYS]
            last = long_form(part.ffill(limit=3).shift(horizon), "last")
            last.index.names = ["week", *KEYS]
            spike = long_form(spikes.loc[:, part.columns], "spike")
            spike.index.names = ["week", *KEYS]
            rows = pd.concat([low.rename("low"), high.rename("high")], axis=1).join(actual).join(last).join(spike).dropna(subset=["actual", "last"]).reset_index()
            rows["high"] = rows[["low", "high"]].max(axis=1)
            scored = simple_band(part, calibrate(rows), horizon)
            raw = report_row(scored, "low", "high")
            cal = report_row(scored, "low_cal", "high_cal")
            band = report_row(scored, "low_band", "high_band")
            summary.append({"crop": crop, "weeks_ahead": horizon, "points": f"{len(scored):,}",
                            "raw_inside": raw[0], "calibrated_inside": cal[0], "calibrated_width": cal[1],
                            "simple_band_inside": band[0], "simple_band_width": band[1]})
            flagged = scored[scored["spike"].astype(bool)]
            in_spikes.append({"crop": crop, "weeks_ahead": horizon, "calibrated_inside": report_row(flagged, "low_cal", "high_cal")[0],
                              "simple_band_inside": report_row(flagged, "low_band", "high_band")[0]})
            for year, group in scored.groupby(scored["week"].dt.year):
                by_year.append({"crop": crop, "weeks_ahead": horizon, "year": year, "calibrated_inside": report_row(group, "low_cal", "high_cal")[0]})
            kept.append(scored.assign(horizon=horizon))
    summary, in_spikes, by_year = pd.DataFrame(summary), pd.DataFrame(in_spikes), pd.DataFrame(by_year)
    pd.concat(kept).to_parquet(FORECASTS, index=False)
    print(summary.to_string(index=False)); print(in_spikes.to_string(index=False))
    print(by_year[by_year["weeks_ahead"] == 4].pivot(index="year", columns="crop", values="calibrated_inside").to_string())
    REPORT.write_text("\n".join([
        "# Forecast ranges", "",
        f"Target: the real price falls inside the range {TARGET_COVERAGE:.0%} of the time. Validation years from {FIRST_SCORED_YEAR}. "
        "`inside` is the percent of real prices inside the range. `width` is the median range as a percent of the price, "
        "so lower is more useful if coverage holds. Written by `python -m src.intervals`.", "",
        table(summary), "", "## Weeks already in a spike", "", table(in_spikes), "",
        "## Calibrated coverage by year", "", table(by_year), "",
    ]), encoding="utf-8")


if __name__ == "__main__":
    main()
