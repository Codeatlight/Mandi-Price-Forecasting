"""Spike alerts: can we warn before a market's price reaches twice its normal level?

A spike begins when a market reaches SPIKE_RATIO times its previous-year median after
at least QUIET_WEEKS without a spike. At each week, for markets not already in a spike,
the question is whether one begins within the next WARNING_WEEKS.

A classifier is retrained before each validation year, on questions fully answered
before that year starts. Its alert threshold comes only from earlier years, which
makes the first validation year a warm-up. A simple rule of thumb is the comparison.

Run from the project root:  python -m src.alerts
"""
from pathlib import Path

import lightgbm as lgb
import numpy as np
import pandas as pd
from sklearn.metrics import average_precision_score, precision_recall_curve

from src.backtest import BASE_WEEKS, MIN_BASE_WEEKS, SPIKE_RATIO, TEST_START, VALIDATION_START, load_panel, table
from src.models import PARAMS, SOURCE_STATE, features_for, long_form

REPORT = Path("reports/alerts.md")
FORECASTS = Path("data/processed/validation_alerts.parquet")
QUIET_WEEKS = 8
WARNING_WEEKS = 4
SEED = 42
FIRST_SCORED_YEAR = VALIDATION_START.year + 1
RULE_RATIO = 1.5  # the rule of thumb: already 1.5 times normal
RULE_RISE = 0.1  # and up at least about 10% in four weeks
CLASSIFIER = {**{k: v for k, v in PARAMS.items() if k != "objective"}, "objective": "binary"}


def spike_table(part):
    base = part.shift(1).rolling(BASE_WEEKS, min_periods=MIN_BASE_WEEKS).median()
    ratio = part / base
    spike = ratio >= SPIKE_RATIO
    earlier = spike.astype(float).shift(1).rolling(QUIET_WEEKS, min_periods=1).max().fillna(0)
    begins = spike & (earlier == 0)
    return ratio, spike, begins


def questions(part):
    """One row per market and origin week that isn't in a spike, with the later answer."""
    ratio, spike, begins = spike_table(part)
    upcoming = begins.astype(float).shift(-WARNING_WEEKS).rolling(WARNING_WEEKS, min_periods=1).max()
    known = (part.index[-1] - pd.Timedelta(weeks=WARNING_WEEKS))
    upcoming.loc[upcoming.index > known] = np.nan
    rows = pd.concat([long_form(ratio, "ratio"), long_form(spike, "in_spike"), long_form(upcoming, "label")], axis=1)
    rows = rows[(~rows["in_spike"].astype(bool)) & rows["ratio"].notna() & rows["label"].notna()]
    return rows.drop(columns="in_spike"), begins


def rolling_scores(features, labels, shuffle=False):
    origin = features.index.get_level_values(0)
    scores = pd.Series(index=features.index, dtype=float)
    for year in range(VALIDATION_START.year, TEST_START.year + 1):
        start, end = pd.Timestamp(year, 1, 1), min(pd.Timestamp(year + 1, 1, 1), TEST_START)
        train = origin + pd.Timedelta(weeks=WARNING_WEEKS) < start
        score = (origin >= start) & (origin < end)
        y = labels[train].to_numpy()
        if shuffle:
            y = np.random.default_rng(SEED + year).permutation(y)
        model = lgb.LGBMClassifier(**CLASSIFIER).fit(features[train], y)
        scores[score] = model.predict_proba(features[score])[:, 1]
    return scores


def threshold_from(labels, scores):
    """The alert line with the best balance of hits and false alarms on earlier years."""
    precision, recall, cuts = precision_recall_curve(labels, scores)
    balance = 2 * precision[:-1] * recall[:-1] / np.maximum(precision[:-1] + recall[:-1], 1e-9)
    return float(cuts[int(np.argmax(balance))])


def apply_thresholds(rows):
    """Each year's alerts use a line chosen on earlier years only."""
    years = rows.index.get_level_values(0).year
    alert = pd.Series(False, index=rows.index)
    for year in range(FIRST_SCORED_YEAR, TEST_START.year + 1):
        earlier = rows[years < year]
        alert[years == year] = rows.loc[years == year, "score"] >= threshold_from(earlier["label"], earlier["score"])
    return alert


def calendar_scores(rows, late):
    """How often a spike was coming in each calendar month, from earlier years only."""
    origin = rows.index.get_level_values(0)
    months = late.index.get_level_values(0).month
    years = late.index.get_level_values(0).year
    scores = pd.Series(0.0, index=late.index)
    for year in sorted(set(years)):
        answered = origin + pd.Timedelta(weeks=WARNING_WEEKS) < pd.Timestamp(year, 1, 1)
        rates = rows.loc[answered, "label"].groupby(origin[answered].month).mean()
        scores[years == year] = pd.Series(months[years == year]).map(rates).fillna(0).to_numpy()
    return scores


def caught_beforehand(rows, alert_column, begins):
    """Share of scored spike beginnings with an alert in the weeks just before."""
    alerts = rows[rows[alert_column]].reset_index()
    columns = list(alerts.columns[:5])
    marked = set(map(tuple, alerts[columns].to_numpy()))
    events = long_form(begins, "begin")
    events = events[events.astype(bool)]
    weeks = events.index.get_level_values(0)
    events = events[(weeks >= pd.Timestamp(FIRST_SCORED_YEAR, 1, 1)) & (weeks < TEST_START)]
    caught, leads = 0, []
    for key in events.index:
        hits = [lead for lead in range(1, WARNING_WEEKS + 1) if (key[0] - pd.Timedelta(weeks=lead), *key[1:]) in marked]
        if hits:
            caught += 1
            leads.append(max(hits))
    return len(events), caught, (float(np.median(leads)) if leads else 0.0)


def measure(rows, column, begins, crop):
    total, caught, lead = caught_beforehand(rows, column, begins)
    alerts = rows[rows[column]]
    market_years = rows.groupby(rows.index.names[1:]).ngroups * (len(set(rows.index.get_level_values(0).year)))
    return {"crop": crop, "method": column, "alerts": f"{len(alerts):,}",
            "alerts_correct_pct": round(float(alerts["label"].mean() * 100), 1) if len(alerts) else 0.0,
            "spikes": total, "spikes_warned_pct": round(caught / max(total, 1) * 100, 1), "median_warning_weeks": lead,
            "false_alerts_per_market_year": round(float((1 - alerts["label"]).sum() / market_years), 1)}


def main():
    panel = load_panel()
    crops = panel.columns.get_level_values("Commodity")
    results, quality, kept = [], [], []
    for crop in sorted(set(crops)):
        print(crop, flush=True)
        part = panel.loc[:, crops == crop]
        rows, begins = questions(part)
        features = features_for(part, SOURCE_STATE[crop]).reindex(rows.index)
        features["log_ratio"] = np.log(rows["ratio"])
        rows["score"] = rolling_scores(features, rows["label"])
        fake = rolling_scores(features, rows["label"], shuffle=True)
        rows["change_4"] = features["change_4"]
        scored = rows[rows["score"].notna()].copy()
        scored["model"] = apply_thresholds(scored)
        scored["rule"] = (scored["ratio"] >= RULE_RATIO) & (scored["change_4"] >= RULE_RISE)
        late = scored[scored.index.get_level_values(0).year >= FIRST_SCORED_YEAR]
        results += [measure(late, "model", begins, crop), measure(late, "rule", begins, crop)]
        fake_scores = fake[late.index]
        quality.append({"crop": crop, "share_with_spike_coming_pct": round(float(late["label"].mean() * 100), 2),
                        "model_precision_score": round(average_precision_score(late["label"], late["score"]) * 100, 1),
                        "calendar_only_score": round(average_precision_score(late["label"], calendar_scores(rows, late)) * 100, 1),
                        "rule_ratio_only_score": round(average_precision_score(late["label"], late["ratio"]) * 100, 1),
                        "shuffled_targets_score": round(average_precision_score(late["label"], fake_scores) * 100, 1)})
        kept.append(late.reset_index())
    results, quality = pd.DataFrame(results), pd.DataFrame(quality)
    pd.concat(kept).to_parquet(FORECASTS, index=False)
    print(results.to_string(index=False)); print(quality.to_string(index=False))
    REPORT.write_text("\n".join([
        "# Spike alerts", "",
        f"Question: at a market not in a spike, will a price of at least {SPIKE_RATIO:g} times its previous-year median begin within "
        f"{WARNING_WEEKS} weeks? Scored on {FIRST_SCORED_YEAR} to October 2024. Written by `python -m src.alerts`.", "",
        "`alerts_correct_pct` is the share of alerts followed by a spike. `spikes_warned_pct` is the share of spikes with an alert in the "
        f"{WARNING_WEEKS} weeks before. The rule alerts when a market is at least {RULE_RATIO} times normal and rose about {RULE_RISE:.0%} in four weeks.", "",
        table(results), "",
        "## Ranking quality", "",
        "Average precision, where the share with a spike coming is what guessing scores. The calendar score uses only how often "
        "spikes came in each month in earlier years, so beating it shows the model does more than recognise the season.", "", table(quality), "",
    ]), encoding="utf-8")


if __name__ == "__main__":
    main()
