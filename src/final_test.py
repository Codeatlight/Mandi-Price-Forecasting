"""The final test: score forecasts, ranges and alerts on the untouched last two years, once.

Everything follows the rules fixed during validation: same settings, retrained before
each test year as a live system would be, ranges corrected by the previous year's
misses, and alert lines taken from validation years. This refuses to run a second time.
Test the code first with --dry-run, which uses two older years and writes nothing.

Run from the project root:
  python -m src.final_test --dry-run
  python -m src.final_test
"""
import argparse
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score

from src.alerts import (CLASSIFIER, FORECASTS as VALIDATION_ALERTS, RULE_RATIO, RULE_RISE, WARNING_WEEKS, measure, questions,
                        threshold_from)
from src.backtest import HORIZONS, KEYS, MAX_STALE_WEEKS, TEST_START, load_panel, spike_flags, table
from src.intervals import HIGH, LOW, conformal_shift, quantile_params
from src.models import PARAMS, SOURCE_STATE, features_for, long_form

REPORT = Path("reports/final_test.md")
FORECASTS = Path("data/processed/test_forecasts.parquet")
SEED = 42
RESAMPLES = 2000
TEST_YEARS = [(pd.Timestamp("2024-11-01"), pd.Timestamp("2025-11-01")), (pd.Timestamp("2025-11-01"), pd.Timestamp("2026-11-02"))]
DRY_YEARS = [(pd.Timestamp("2022-11-01"), pd.Timestamp("2023-11-01")), (pd.Timestamp("2023-11-01"), pd.Timestamp("2024-11-01"))]
VALIDATION_SCORES = {"Onion": (32.8, 14.2), "Potato": (14.6, 14.9), "Tomato": (44.5, 15.9)}


def fit_predict(features, target, target_week, train_end, start, end, params):
    train = (target_week < train_end) & target.notna().to_numpy()
    score = (target_week >= start) & (target_week < end)
    model = lgb.LGBMRegressor(**params).fit(features[train], target[train].to_numpy())
    return score, model.predict(features[score])


def forecast_year(part, features, horizon, start, end, spikes):
    logged = np.log(part.ffill(limit=MAX_STALE_WEEKS))
    target = long_form(np.log(part).shift(-horizon) - logged, "target").reindex(features.index)
    last = long_form(logged, "last").reindex(features.index)
    target_week = features.index.get_level_values(0) + pd.Timedelta(weeks=horizon)
    mask, middle = fit_predict(features, target, target_week, start, start, end, PARAMS)
    _, low = fit_predict(features, target, target_week, start, start, end, quantile_params(LOW))
    _, high = fit_predict(features, target, target_week, start, start, end, quantile_params(HIGH))

    year_before = start - pd.DateOffset(years=1)
    calibration, low_before = fit_predict(features, target, target_week, year_before, year_before, start, quantile_params(LOW))
    _, high_before = fit_predict(features, target, target_week, year_before, year_before, start, quantile_params(HIGH))
    usable = target[calibration].notna().to_numpy() & last[calibration].notna().to_numpy()
    actual_before = np.exp(last[calibration].to_numpy()[usable] + target[calibration].to_numpy()[usable])
    base_before = last[calibration].to_numpy()[usable]
    shift = conformal_shift(np.exp(base_before + low_before[usable]),
                            np.exp(base_before + np.maximum(low_before, high_before)[usable]), actual_before)

    rows = pd.DataFrame({"week": target_week[mask], "actual": np.exp(last[mask].to_numpy() + target[mask].to_numpy()),
                         "this_week": np.exp(last[mask].to_numpy()), "lightgbm": np.exp(last[mask].to_numpy() + middle),
                         "low": np.exp(last[mask].to_numpy() + low - shift),
                         "high": np.exp(last[mask].to_numpy() + np.maximum(low, high) + shift)},
                        index=features.index[mask].droplevel(0)).dropna(subset=["actual", "this_week"]).reset_index()
    flags = long_form(spikes.loc[:, part.columns], "spike").rename_axis(["week", *KEYS]).reset_index()
    return rows.merge(flags, on=["week", *KEYS], how="left").assign(horizon=horizon)


def gain_interval(rows):
    base = (rows["this_week"] - rows["actual"]).abs() / rows["actual"]
    model = (rows["lightgbm"] - rows["actual"]).abs() / rows["actual"]
    weekly = pd.DataFrame({"base": base, "model": model, "week": rows["week"]}).groupby("week").sum().to_numpy()
    picks = np.random.default_rng(SEED).integers(0, len(weekly), (RESAMPLES, len(weekly)))
    totals = weekly[picks].sum(axis=1)
    low, high = np.percentile((1 - totals[:, 1] / totals[:, 0]) * 100, [2.5, 97.5])
    return round(base.mean() * 100, 2), round(model.mean() * 100, 2), round((1 - model.mean() / base.mean()) * 100, 1), f"{low:.1f} to {high:.1f}"


def forecast_scores(rows):
    out = []
    for (crop, horizon), part in rows.groupby(["Commodity", "horizon"]):
        base, model, gain, interval = gain_interval(part)
        inside = part["actual"].between(part["low"], part["high"])
        spike = part["spike"].fillna(False).astype(bool)
        out.append({"crop": crop, "weeks_ahead": horizon, "points": f"{len(part):,}", "this_week": base, "lightgbm": model, "gain_pct": gain,
                    "gain_95_interval": interval, "range_inside_pct": round(inside.mean() * 100, 1),
                    "range_width_pct": round(float(((part["high"] - part["low"]) / part["actual"]).median() * 100), 1),
                    "inside_in_spikes_pct": round(inside[spike].mean() * 100, 1)})
    return pd.DataFrame(out)


def alert_scores(panel, crop, part, years):
    rows, begins = questions(part)
    features = features_for(part, SOURCE_STATE[crop]).reindex(rows.index)
    features["log_ratio"] = np.log(rows["ratio"])
    origin = rows.index.get_level_values(0)
    rows["score"] = np.nan
    for start, end in years:
        train = origin + pd.Timedelta(weeks=WARNING_WEEKS) < start
        score = (origin >= start) & (origin < end)
        model = lgb.LGBMClassifier(**CLASSIFIER).fit(features[train], rows.loc[train, "label"].to_numpy())
        rows.loc[score, "score"] = model.predict_proba(features[score])[:, 1]
    earlier = pd.read_parquet(VALIDATION_ALERTS)
    earlier = earlier[(earlier["Commodity"] == crop) & (earlier.iloc[:, 0] < years[0][0])]
    line = threshold_from(earlier["label"], earlier["score"])
    late = rows[rows["score"].notna()].copy()
    late["model"] = late["score"] >= line
    late["rule"] = (late["ratio"] >= RULE_RATIO) & (features.loc[late.index, "change_4"] >= RULE_RISE)
    window = dict(start=years[0][0], end=years[-1][1])
    summary = [measure(late, column, begins, crop, **window) for column in ["model", "rule"]]
    quality = {"crop": crop, "share_with_spike_coming_pct": round(late["label"].mean() * 100, 2),
               "model_score": round(average_precision_score(late["label"], late["score"]) * 100, 1)}
    return summary, quality, late.reset_index()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--dry-run", action="store_true", help="use two older years and write nothing")
    dry_run = parser.parse_args().dry_run
    if not dry_run and REPORT.exists():
        raise SystemExit(f"{REPORT} exists: the final test has been used and must not be run again.")
    years = DRY_YEARS if dry_run else TEST_YEARS
    panel = load_panel(include_test=not dry_run)
    spikes = spike_flags(panel)
    crops = panel.columns.get_level_values("Commodity")
    forecasts, alerts, qualities, kept_alerts = [], [], [], []
    for crop in sorted(set(crops)):
        part = panel.loc[:, crops == crop]
        features = features_for(part, SOURCE_STATE[crop])
        for horizon in HORIZONS:
            print(crop, horizon, flush=True)
            forecasts += [forecast_year(part, features, horizon, start, end, spikes) for start, end in years]
        summary, quality, late = alert_scores(panel, crop, part, years)
        alerts += summary
        qualities.append(quality)
        kept_alerts.append(late)
    rows = pd.concat(forecasts)
    scores, alerts, qualities = forecast_scores(rows), pd.DataFrame(alerts), pd.DataFrame(qualities)
    print(scores.to_string(index=False)); print(alerts.to_string(index=False)); print(qualities.to_string(index=False))
    if dry_run:
        print("dry run: nothing written")
        return
    rows.to_parquet(FORECASTS, index=False)
    REPORT.write_text("\n".join([
        "# Final test", "",
        f"One run on weeks from {TEST_START.date()}, retrained before each test year. Written by `python -m src.final_test`, which refuses to run twice.", "",
        "## Forecasts and 80% ranges", "", table(scores), "",
        "## Spike alerts", "", table(alerts), "", table(qualities), "",
    ]), encoding="utf-8")


if __name__ == "__main__":
    main()
