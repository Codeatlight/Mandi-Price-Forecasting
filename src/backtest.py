"""Shared backtest tools, and the baselines every model must beat.

Each forecast uses only prices known at its origin week. For a target week w and
horizon h, the origin is w - h. No random splits: time runs one way.

Scores use the validation weeks. The final test weeks are read only by evaluation
at the end of the project, never here.

Run from the project root:  python -m src.backtest
"""
from pathlib import Path

import numpy as np
import pandas as pd

WEEKLY = Path("data/processed/weekly_prices.parquet")
REPORT = Path("reports/baselines.md")

VALIDATION_START = pd.Timestamp("2019-01-01")
TEST_START = pd.Timestamp("2024-11-01")
HORIZONS = [1, 2, 4]
SEASON_WEEKS = 52
MAX_STALE_WEEKS = 3  # the newest price known at the origin may be this old
SPIKE_RATIO = 2.0
BASE_WEEKS = 52
MIN_BASE_WEEKS = 26
KEYS = ["Commodity", "State", "District", "market"]


def load_panel(include_test=False):
    """Weekly prices with one column per series and every week present.

    Stops before the test period unless the final test asks for it.
    """
    weekly = pd.read_parquet(WEEKLY)
    if not include_test:
        weekly = weekly[weekly["week"] < TEST_START]
    panel = weekly.pivot_table(index="week", columns=KEYS, values="price")
    return panel.reindex(pd.date_range(panel.index.min(), panel.index.max(), freq="7D"))


def spike_flags(panel):
    """True where a price is at least SPIKE_RATIO times the previous year's median."""
    base = panel.shift(1).rolling(BASE_WEEKS, min_periods=MIN_BASE_WEEKS).median()
    return (panel / base) >= SPIKE_RATIO


def baselines(panel, horizon):
    """Forecasts indexed by target week, built only from what was known at the origin."""
    known = panel.ffill(limit=MAX_STALE_WEEKS)
    last = known.shift(horizon)
    last_year_target = known.shift(SEASON_WEEKS)
    last_year_origin = known.shift(SEASON_WEEKS + horizon)
    return {"this_week": last, "same_week_last_year": last_year_target,
            "this_week_plus_last_years_change": last * last_year_target / last_year_origin}


def stack(frame, name):
    return frame.stack(list(range(frame.columns.nlevels)), future_stack=True).rename(name)


def evaluate(forecasts, panel, spikes):
    """Long table of actual and forecast prices on the validation weeks."""
    actual = stack(panel, "actual")
    joined = pd.concat([actual, stack(spikes, "spike"), *[stack(f, n) for n, f in forecasts.items()]], axis=1).dropna()
    weeks = joined.index.get_level_values(0)
    return joined[(weeks >= VALIDATION_START) & (weeks < TEST_START)]


def score(rows, names):
    """Mean absolute percent error, and how often each method was within 10%."""
    out = {}
    for name in names:
        error = (rows[name] - rows["actual"]).abs() / rows["actual"]
        out[name] = {"mape": round(float(error.mean() * 100), 1), "within_10pct": round(float((error <= 0.1).mean() * 100), 1)}
    return out


def table(frame):
    rows = [list(frame.columns), ["---"] * frame.shape[1], *frame.astype(str).values.tolist()]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def main():
    panel = load_panel()
    spikes = spike_flags(panel)
    overall, during_spikes = [], []
    for horizon in HORIZONS:
        forecasts = baselines(panel, horizon)
        names = list(forecasts)
        rows = evaluate(forecasts, panel, spikes)
        crops = rows.index.get_level_values(1)
        for crop in sorted(set(crops)):
            part = rows[crops == crop]
            scores = score(part, names)
            overall.append({"crop": crop, "weeks_ahead": horizon, "points": f"{len(part):,}",
                            **{n: scores[n]["mape"] for n in names}})
            scores = score(part[part["spike"].astype(bool)], names)
            during_spikes.append({"crop": crop, "weeks_ahead": horizon, **{n: scores[n]["mape"] for n in names}})
    overall, during_spikes = pd.DataFrame(overall), pd.DataFrame(during_spikes)
    print(overall.to_string(index=False)); print(during_spikes.to_string(index=False))
    REPORT.write_text("\n".join([
        "# Baselines", "",
        f"Validation weeks {VALIDATION_START.date()} to {TEST_START.date()}. Written by `python -m src.backtest`. "
        "All methods are scored on the same crop, market and week points, so they compare directly.", "",
        "## Mean absolute percent error, lower is better", "", table(overall), "",
        "## The same, only for weeks already in a spike", "", table(during_spikes), "",
    ]), encoding="utf-8")


if __name__ == "__main__":
    main()
