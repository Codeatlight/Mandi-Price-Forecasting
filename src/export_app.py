"""Train on all data and write what the app shows to app/market_data.json.

Forecasts start from the latest week. They are given only for markets that are still
reporting. Each range is corrected by the misses of the latest full year, and each
alert uses the line chosen on validation years. The file holds prices and forecasts
only, so the app needs neither the raw data nor an API key.

Run from the project root:  python -m src.export_app
"""
import json
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd

from src.alerts import CLASSIFIER, FORECASTS as VALIDATION_ALERTS, WARNING_WEEKS, questions, spike_table, threshold_from
from src.backtest import HORIZONS, KEYS, MAX_STALE_WEEKS, SPIKE_RATIO, load_panel
from src.intervals import HIGH, LOW, conformal_shift, quantile_params
from src.models import PARAMS, SOURCE_STATE, features_for, long_form

OUT = Path("app/market_data.json")
MARKETS = Path("data/processed/markets.parquet")
HISTORY_WEEKS = 156
CALIBRATION_WEEKS = 52
TRUSTED_ALERTS = {"Onion": True, "Tomato": True, "Potato": False}  # potato has too few spikes to judge


def fit(features, target, mask, params):
    return lgb.LGBMRegressor(**params).fit(features[mask], target[mask].to_numpy())


def forecasts(part, features, latest):
    logged = np.log(part.ffill(limit=MAX_STALE_WEEKS))
    origin = features.index.get_level_values(0)
    at_latest = features[origin == latest]
    out = {}
    for horizon in HORIZONS:
        target = long_form(np.log(part).shift(-horizon) - logged, "target").reindex(features.index)
        last = long_form(logged, "last").reindex(features.index)
        known = target.notna().to_numpy()
        target_week = origin + pd.Timedelta(weeks=horizon)
        cutoff = latest + pd.Timedelta(weeks=horizon) - pd.Timedelta(weeks=CALIBRATION_WEEKS)
        older = known & (target_week < cutoff)
        recent = known & (target_week >= cutoff) & last.notna().to_numpy()
        low_model, high_model = fit(features, target, older, quantile_params(LOW)), fit(features, target, older, quantile_params(HIGH))
        low = last[recent].to_numpy() + low_model.predict(features[recent])
        high = last[recent].to_numpy() + np.maximum(low_model.predict(features[recent]), high_model.predict(features[recent]))
        actual = last[recent].to_numpy() + target[recent].to_numpy()
        shift = conformal_shift(np.exp(low), np.exp(high), np.exp(actual))

        base = logged.loc[latest].reindex(at_latest.index.droplevel(0)).to_numpy()
        middle = fit(features, target, known, PARAMS).predict(at_latest)
        bottom = fit(features, target, known, quantile_params(LOW)).predict(at_latest)
        top = np.maximum(bottom, fit(features, target, known, quantile_params(HIGH)).predict(at_latest))
        frame = pd.DataFrame({"middle": np.exp(base + middle), "low": np.exp(base + bottom - shift), "high": np.exp(base + top + shift)},
                             index=at_latest.index.droplevel(0))
        out[horizon] = frame.assign(low=lambda d: d[["low", "middle"]].min(axis=1), high=lambda d: d[["high", "middle"]].max(axis=1))
    return out


def alert_status(crop, part, features, latest):
    rows, _ = questions(part)
    ratio, spike, _ = spike_table(part)
    train = features.reindex(rows.index).copy()
    train["log_ratio"] = np.log(rows["ratio"])
    model = lgb.LGBMClassifier(**CLASSIFIER).fit(train, rows["label"].to_numpy())
    now = features[features.index.get_level_values(0) == latest].copy()
    level = long_form(ratio, "ratio").reindex(now.index)
    now["log_ratio"] = np.log(level)
    risk = pd.Series(model.predict_proba(now[train.columns])[:, 1], index=now.index.droplevel(0))
    earlier = pd.read_parquet(VALIDATION_ALERTS)
    earlier = earlier[earlier["Commodity"] == crop]
    line = threshold_from(earlier["label"], earlier["score"])
    in_spike = spike.loc[latest].reindex(risk.index).fillna(False).astype(bool)
    status = pd.Series("normal", index=risk.index)
    status[(risk >= line) & level.notna().to_numpy()] = "watch"
    status[in_spike] = "spike"
    return status, level.droplevel(0).reindex(risk.index)


def rounded(values):
    return [None if pd.isna(v) else int(round(v)) for v in values]


def main():
    panel = load_panel(include_test=True)
    panel = panel.loc[:panel.notna().sum(axis=1).ne(0)[::-1].idxmax()]
    latest = panel.index[-1]
    markets = pd.read_parquet(MARKETS).set_index(KEYS)
    crops = panel.columns.get_level_values("Commodity")
    series = []
    for crop in sorted(set(crops)):
        print(crop, flush=True)
        part = panel.loc[:, crops == crop]
        features = features_for(part, SOURCE_STATE[crop])
        predicted = forecasts(part, features, latest)
        status, level = alert_status(crop, part, features, latest)
        recent = part.iloc[-HISTORY_WEEKS:]
        base = (part.shift(1).rolling(52, min_periods=26).median()).iloc[-HISTORY_WEEKS:]
        for key in part.columns:
            reporting = bool(markets.loc[key, "reporting_now"])
            row = {"crop": key[0], "state": key[1], "district": key[2], "market": key[3].title(), "reporting": reporting,
                   "last_week": str(part[key].dropna().index[-1].date()), "prices": rounded(recent[key]), "normal": rounded(base[key])}
            if reporting and key in predicted[1].index and pd.notna(predicted[1].loc[key, "middle"]):
                row["status"] = status[key] if TRUSTED_ALERTS[crop] or status[key] == "spike" else "unrated"
                row["vs_normal"] = None if pd.isna(level[key]) else round(float(level[key]), 2)
                row["forecast"] = {str(h): rounded(predicted[h].loc[key, ["low", "middle", "high"]]) for h in HORIZONS}
            series.append(row)
    OUT.write_text(json.dumps({"latest_week": str(latest.date()), "spike_ratio": SPIKE_RATIO,
                               "weeks": [str(w.date()) for w in panel.index[-HISTORY_WEEKS:]], "series": series},
                              separators=(",", ":")), encoding="utf-8")
    live = [s for s in series if "forecast" in s]
    print(f"{len(series)} series, {len(live)} live, {OUT.stat().st_size // 1024} KB, latest {latest.date()}")
    print(pd.Series([(s["crop"], s["status"]) for s in live]).value_counts().to_string())
    assert all(s["forecast"][str(h)][0] <= s["forecast"][str(h)][1] <= s["forecast"][str(h)][2] for s in live for h in HORIZONS)


if __name__ == "__main__":
    main()
