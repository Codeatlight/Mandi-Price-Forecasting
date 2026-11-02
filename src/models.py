"""Forecast models, scored against the baselines on the same market-weeks.

Exponential smoothing: a weighted average of past log prices, with more weight on
recent weeks. The weight is chosen per crop on weeks before validation starts.

LightGBM: one model per crop and horizon, across all markets. It predicts the change
in log price from the origin week. For each validation year it trains only on targets
before that year starts, as a live model would, and is then scored on that year.

Run from the project root:  python -m src.models
"""
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.backtest import (HORIZONS, KEYS, MAX_STALE_WEEKS, TEST_START, VALIDATION_START, baselines, load_panel,
                          spike_flags, table)

REPORT = Path("reports/models.md")
FORECASTS = Path("data/processed/validation_forecasts.parquet")

SEED = 42
ALPHAS = [0.3, 0.5, 0.7, 0.85, 1.0]
ALPHA_FROM = pd.Timestamp("2015-01-01")
SOURCE_STATE = {"Onion": "Maharashtra", "Potato": "Uttar Pradesh", "Tomato": "Maharashtra"}
CHANGE_WEEKS = [1, 2, 4, 8, 13, 26]
PARAMS = {"objective": "l1", "n_estimators": 300, "learning_rate": 0.03, "num_leaves": 15, "min_child_samples": 100,
          "subsample": 0.8, "subsample_freq": 1, "colsample_bytree": 0.7, "reg_lambda": 5.0, "random_state": SEED,
          "n_jobs": 4, "verbose": -1}
SOURCE_FEATURES = ["source_change_1", "source_change_2", "source_change_4"]


def smoothed(panel, alpha):
    known = np.log(panel.ffill(limit=MAX_STALE_WEEKS))
    return np.exp(known.ewm(alpha=alpha, adjust=False, ignore_na=True).mean()).where(known.notna())


def choose_alpha(panel, crop_columns, horizon):
    """The smoothing weight with the lowest error on weeks before validation."""
    part = panel[crop_columns]
    best, best_error = None, np.inf
    for alpha in ALPHAS:
        forecast = smoothed(part, alpha).shift(horizon)
        weeks = (part.index >= ALPHA_FROM) & (part.index < VALIDATION_START)
        error = float(np.nanmean(((forecast - part).abs() / part)[weeks].to_numpy()))
        if error < best_error:
            best, best_error = alpha, error
    return best


def long_form(frame, name):
    return frame.stack(list(range(frame.columns.nlevels)), future_stack=True).rename(name)


def features_for(part, source_state):
    """Everything here is known at the origin week, which is the index of each row."""
    logged = np.log(part.ffill(limit=MAX_STALE_WEEKS))
    states = part.columns.get_level_values("State")
    columns = {}
    for weeks in CHANGE_WEEKS:
        columns[f"change_{weeks}"] = logged.diff(weeks)
    weekly_change = logged.diff()
    columns["volatility_8"] = weekly_change.rolling(8, min_periods=4).std()
    columns["above_year_median"] = logged - logged.rolling(52, min_periods=26).median()
    position = pd.DataFrame(np.tile(np.arange(len(part), dtype=float)[:, None], part.shape[1]),
                            index=part.index, columns=part.columns)
    columns["weeks_since_price"] = position - position.where(part.notna()).ffill()

    source = logged.loc[:, states == source_state].median(axis=1)
    state_level = logged.T.groupby(level="State").median().T
    crop_level = logged.median(axis=1)
    frames = [long_form(frame, name) for name, frame in columns.items()]
    table_ = pd.concat(frames, axis=1)
    origin = table_.index.get_level_values(0)
    table_["crop_change_1"] = origin.map(crop_level.diff())
    table_["crop_change_4"] = origin.map(crop_level.diff(4))
    for weeks in [1, 2, 4]:
        table_[f"source_change_{weeks}"] = origin.map(source.diff(weeks))
    state = table_.index.get_level_values("State")
    places = pd.MultiIndex.from_arrays([origin, state])
    table_["state_change_1"] = long_form(state_level.diff(), "x").reindex(places).to_numpy()
    table_["state_change_4"] = long_form(state_level.diff(4), "x").reindex(places).to_numpy()
    table_["week_sin"] = np.sin(2 * np.pi * origin.isocalendar().week.to_numpy() / 52)
    table_["week_cos"] = np.cos(2 * np.pi * origin.isocalendar().week.to_numpy() / 52)
    table_["market_code"] = table_.index.get_level_values("market").astype("category").codes
    table_["state_code"] = state.astype("category").codes
    return table_


def rolling_forecast(part, features, horizon, drop=(), shuffle=False):
    """Forecasts by target week, retraining before each validation year."""
    logged = np.log(part.ffill(limit=MAX_STALE_WEEKS))
    target = long_form(np.log(part).shift(-horizon) - logged, "target").reindex(features.index)
    last = long_form(logged, "last").reindex(features.index)
    target_week = features.index.get_level_values(0) + pd.Timedelta(weeks=horizon)
    columns = [c for c in features.columns if c not in drop]
    results, trees = [], []
    for year in range(VALIDATION_START.year, TEST_START.year + 1):
        start, end = pd.Timestamp(year, 1, 1), min(pd.Timestamp(year + 1, 1, 1), TEST_START)
        train = (target_week < start) & target.notna().to_numpy()
        score = (target_week >= start) & (target_week < end) & last.notna().to_numpy()
        y = target[train].to_numpy()
        if shuffle:
            y = np.random.default_rng(SEED + year).permutation(y)
        model = lgb.LGBMRegressor(**PARAMS).fit(features.loc[train, columns], y)
        predicted = np.exp(last[score].to_numpy() + model.predict(features.loc[score, columns]))
        index = features.index[score].droplevel(0)
        results.append(pd.DataFrame({"week": target_week[score], "lightgbm": predicted}, index=index))
        trees.append(pd.Series(model.booster_.feature_importance("gain"), index=columns))
    frame = pd.concat(results).set_index("week", append=True).reorder_levels(["week", *KEYS])
    return frame["lightgbm"], sum(trees)


def mape(forecast, actual):
    return float(((forecast - actual).abs() / actual).mean() * 100)


def main():
    panel = load_panel()
    spikes = spike_flags(panel)
    results, by_year, spike_rows, kept, importance, checks = [], [], [], [], {}, []
    crops = panel.columns.get_level_values("Commodity")
    for crop in sorted(set(crops)):
        part = panel.loc[:, crops == crop]
        features = features_for(part, SOURCE_STATE[crop])
        for horizon in HORIZONS:
            print(crop, horizon, flush=True)
            alpha = choose_alpha(panel, panel.columns[crops == crop], horizon)
            model, gain = rolling_forecast(part, features, horizon)
            no_source, _ = rolling_forecast(part, features, horizon, drop=SOURCE_FEATURES)
            joined = pd.concat([long_form(part, "actual"), long_form(baselines(part, horizon)["this_week"], "this_week"),
                                long_form(smoothed(part, alpha).shift(horizon), "smoothing"),
                                long_form(spikes.loc[:, part.columns], "spike")], axis=1)
            joined.index.names = ["week", *KEYS]
            joined = joined.join(model, how="inner").join(no_source.rename("no_source")).dropna(
                subset=["actual", "this_week", "smoothing", "lightgbm"])
            base = mape(joined["this_week"], joined["actual"])
            error = mape(joined["lightgbm"], joined["actual"])
            results.append({"crop": crop, "weeks_ahead": horizon, "points": f"{len(joined):,}", "alpha": alpha,
                            "this_week": round(base, 2), "smoothing": round(mape(joined["smoothing"], joined["actual"]), 2),
                            "lightgbm": round(error, 2), "gain_pct": round((1 - error / base) * 100, 1),
                            "without_source_state": round(mape(joined["no_source"], joined["actual"]), 2)})
            years = joined.index.get_level_values("week").year
            for year in sorted(set(years)):
                rows = joined[years == year]
                by_year.append({"crop": crop, "weeks_ahead": horizon, "year": year, "this_week": round(mape(rows["this_week"], rows["actual"]), 1),
                                "lightgbm": round(mape(rows["lightgbm"], rows["actual"]), 1)})
            rows = joined[joined["spike"].astype(bool)]
            spike_rows.append({"crop": crop, "weeks_ahead": horizon, "this_week": round(mape(rows["this_week"], rows["actual"]), 1),
                               "lightgbm": round(mape(rows["lightgbm"], rows["actual"]), 1)})
            importance[f"{crop} {horizon}w"] = (gain / gain.sum()).sort_values(ascending=False).head(5).round(3).to_dict()
            kept.append(joined.assign(horizon=horizon).reset_index())
            if horizon == 4:
                fake, _ = rolling_forecast(part, features, horizon, shuffle=True)
                both = joined[["actual"]].join(fake.rename("fake"), how="inner")
                checks.append({"crop": crop, "real_gain_pct": results[-1]["gain_pct"],
                               "shuffled_targets_gain_pct": round((1 - mape(both["fake"], both["actual"]) / base) * 100, 1)})
    results, by_year = pd.DataFrame(results), pd.DataFrame(by_year)
    wins = by_year.assign(win=by_year["lightgbm"] < by_year["this_week"]).groupby(["crop", "weeks_ahead"])["win"].agg(["sum", "size"]).reset_index()
    pd.concat(kept).to_parquet(FORECASTS, index=False)
    print(results.to_string(index=False)); print(wins.to_string(index=False)); print(pd.DataFrame(spike_rows).to_string(index=False))
    print(pd.DataFrame(checks).to_string(index=False))
    for key, value in importance.items():
        print(key, value)
    REPORT.write_text("\n".join([
        "# Models", "",
        f"Validation weeks {VALIDATION_START.date()} to {TEST_START.date()}, on the same points for every method. "
        "Numbers are mean absolute percent error, lower is better. `gain_pct` is LightGBM's reduction against `this_week`. "
        "Written by `python -m src.models`.", "",
        table(results), "",
        "## Years LightGBM beat next week equals this week", "", table(wins), "",
        "## Error by year", "", table(by_year), "",
        "## Weeks already in a spike", "", table(pd.DataFrame(spike_rows)), "",
        "## Check with shuffled training targets", "", "A model with nothing to learn should show no real gain.", "", table(pd.DataFrame(checks)), "",
        "## Features doing the most work", "", *[f"- {key}: {value}" for key, value in importance.items()], "",
    ]), encoding="utf-8")


if __name__ == "__main__":
    main()
