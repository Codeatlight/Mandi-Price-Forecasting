"""Explore the weekly prices: seasons, volatility, how moves spread, and what a spike is.

Uses weeks before TEST_START only. The final two years stay out of every number and
chart here, so choices such as the spike definition can't be shaped by them.

Run from the project root:  python -m src.explore
"""
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

WEEKLY = Path("data/processed/weekly_prices.parquet")
REPORT = Path("reports/exploration.md")
FIGURES = Path("reports/figures")

TEST_START = pd.Timestamp("2024-11-01")
CROPS = ["Onion", "Potato", "Tomato"]
COLOURS = {"Onion": "#2a78d6", "Potato": "#eb6834", "Tomato": "#1baf7a"}  # fixed order, validated palette
INK, MUTED, GRID = "#0b0b0b", "#52514e", "#e7e6e2"

BASE_WEEKS = 52  # a spike is measured against the market's own previous year
MIN_BASE_WEEKS = 26
SPIKE_RATIOS = [1.25, 1.5, 1.75, 2.0]
SPIKE_RATIO = 2.0  # rare enough to matter: 7 to 13% of market-weeks, and simple to explain
QUIET_WEEKS = 8  # weeks without a spike before a new episode counts
HORIZONS = [1, 2, 4]
SPREAD_FROM = {"Onion": "Maharashtra", "Potato": "Uttar Pradesh", "Tomato": "Maharashtra"}
MAX_LAG = 6
KEYS = ["Commodity", "State", "District", "market"]


def load():
    weekly = pd.read_parquet(WEEKLY)
    weekly = weekly[weekly["week"] < TEST_START].copy()
    assert weekly["week"].max() < TEST_START
    return weekly.sort_values([*KEYS, "week"])


def national(weekly):
    return weekly.groupby(["week", "Commodity"])["price"].median().unstack()[CROPS]


def seasonal_index(prices):
    """Typical percent above or below the surrounding year, by calendar month.

    Uses the median across years, so one huge spike can't pass for a normal season.
    """
    logged = np.log(prices)
    gap = logged - logged.rolling(53, center=True, min_periods=40).median()
    return (np.exp(gap.groupby(gap.index.month).median()) - 1) * 100


def volatility(weekly):
    rows = []
    for crop, group in weekly.groupby("Commodity"):
        logged = np.log(group.set_index([*KEYS, "week"])["price"])
        row = {"crop": crop}
        for weeks in HORIZONS:
            change = logged.groupby(level=KEYS).diff(weeks)
            row[f"typical_{weeks}w_move_pct"] = round(float((np.exp(change.abs().median()) - 1) * 100), 1)
        row["weeks_up_or_down_20pct"] = round(float((logged.groupby(level=KEYS).diff().abs() > np.log(1.2)).mean() * 100), 1)
        rows.append(row)
    return pd.DataFrame(rows)


def add_spike_flags(weekly):
    """A market's price against the median of its own previous year."""
    group = weekly.groupby(KEYS)["price"]
    base = group.transform(lambda s: s.shift(1).rolling(BASE_WEEKS, min_periods=MIN_BASE_WEEKS).median())
    return weekly.assign(ratio=weekly["price"] / base)


def spike_rates(flagged):
    rows = []
    known = flagged.dropna(subset=["ratio"])
    for ratio in SPIKE_RATIOS:
        row = {"at_least_x_times_last_year": ratio}
        row.update({crop: f"{(known[known['Commodity'] == crop]['ratio'] >= ratio).mean():.1%}" for crop in CROPS})
        rows.append(row)
    return pd.DataFrame(rows)


def national_episodes(prices):
    """Spells when the median across markets runs well above its own previous year."""
    rows = []
    for crop in CROPS:
        series = prices[crop].dropna()
        ratio = series / series.shift(1).rolling(BASE_WEEKS, min_periods=MIN_BASE_WEEKS).median()
        flagged = ratio >= SPIKE_RATIO
        start, last = None, None
        for week, on in flagged.items():
            if on:
                if start is None or (week - last).days > QUIET_WEEKS * 7:
                    if start is not None:
                        rows.append(episode(crop, series, ratio, start, last))
                    start = week
                last = week
        if start is not None:
            rows.append(episode(crop, series, ratio, start, last))
    return pd.DataFrame(rows)


def episode(crop, series, ratio, start, last):
    window = series[start:last]
    return {"crop": crop, "start": start.date(), "weeks": ((last - start).days // 7) + 1,
            "peak_price": int(window.max()), "peak_vs_last_year": round(float(ratio[start:last].max()), 1)}


def spread(weekly):
    """Does a producing state's price change come before changes elsewhere?"""
    rows = []
    states = weekly.groupby(["Commodity", "State", "week"])["price"].median()
    for crop, source in SPREAD_FROM.items():
        table = states[crop].unstack(0).pipe(np.log).diff()
        counts = weekly[weekly["Commodity"] == crop].groupby("State")["market"].nunique()
        for state in counts[counts >= 3].index.drop(source, errors="ignore"):
            pair = table[[source, state]].dropna()
            correlations = {lag: pair[source].corr(pair[state].shift(-lag)) for lag in range(-MAX_LAG, MAX_LAG + 1)}
            best = max(correlations, key=correlations.get)
            rows.append({"crop": crop, "from": source, "to": state, "same_week": round(correlations[0], 2),
                         "best_lag_weeks": best, "best_correlation": round(correlations[best], 2)})
    return pd.DataFrame(rows)


def style(axis):
    axis.spines[["top", "right", "left"]].set_visible(False)
    axis.spines["bottom"].set_color(MUTED)
    axis.grid(axis="y", color=GRID, linewidth=0.8)
    axis.set_axisbelow(True)
    axis.tick_params(colors=MUTED, length=0, labelsize=10)


def save(figure, name):
    FIGURES.mkdir(parents=True, exist_ok=True)
    figure.savefig(FIGURES / name, dpi=150, bbox_inches="tight", facecolor="#fcfcfb")
    plt.close(figure)


def chart_history(prices):
    figure, axes = plt.subplots(3, 1, figsize=(10, 7), sharex=True, sharey=True, facecolor="#fcfcfb")
    for axis, crop in zip(axes, CROPS):
        axis.plot(prices.index, prices[crop], color=COLOURS[crop], linewidth=1.6)
        axis.set_ylabel("Rs per quintal", color=MUTED, fontsize=10)
        axis.text(0.01, 0.84, crop, transform=axis.transAxes, color=INK, fontsize=12, fontweight="bold")
        style(axis)
    axes[0].set_title("Median weekly wholesale price across markets, 2010 to October 2024", color=INK, loc="left", fontsize=13)
    save(figure, "price_history.png")


def chart_seasons(seasons):
    figure, axis = plt.subplots(figsize=(10, 4.5), facecolor="#fcfcfb")
    for crop in CROPS:
        axis.plot(seasons.index, seasons[crop], color=COLOURS[crop], linewidth=2, marker="o", markersize=5, label=crop)
        peak = seasons[crop].idxmax()
        axis.text(peak, seasons[crop].max() + 2.5, crop, color=INK, fontsize=11, ha="center")
    axis.axhline(0, color=MUTED, linewidth=1)
    axis.set_xticks(range(1, 13), ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    axis.set_xlim(0.7, 12.3)
    axis.set_ylim(-32, 58)
    axis.set_ylabel("Percent above or below the year", color=MUTED, fontsize=10)
    axis.set_title("Onion peaks in October and November, tomato in July, and potato stays flattest", color=INK, loc="left", fontsize=13)
    axis.legend(frameon=False, ncol=3, loc="lower right", fontsize=10)
    style(axis)
    save(figure, "seasonal_index.png")


def table(frame):
    rows = [list(frame.columns), ["---"] * frame.shape[1], *frame.astype(str).values.tolist()]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def main():
    weekly = load()
    prices = national(weekly)
    seasons = seasonal_index(prices)
    moves = volatility(weekly)
    flagged = add_spike_flags(weekly)
    rates = spike_rates(flagged)
    episodes = national_episodes(prices)
    moved = spread(weekly)
    chart_history(prices)
    chart_seasons(seasons)

    print(moves.to_string(index=False)); print(rates.to_string(index=False))
    print(episodes.to_string(index=False)); print(seasons.round(1).to_string())
    print(moved.sort_values(["crop", "best_correlation"], ascending=[True, False]).to_string(index=False))
    REPORT.write_text("\n".join([
        "# Exploration", "",
        f"Weeks before {TEST_START.date()} only. Written by `python -m src.explore`. Prices are rupees per quintal.", "",
        "## Findings", "",
        "- **Perishability shows up clearly.** A typical four-week move is about 12% for potato, 20% for onion and 32% for tomato.",
        "- **Each crop has its own season.** Onion runs about 27% below its year in May and 48% above in November. Tomato jumps "
        "about 45% in July. Potato bottoms in February and is the gentlest.",
        "- **Spikes recur.** Most of onion's start in the second half of the year: 2010, 2013, 2015, 2017, 2019, 2020 and 2023 all had one.",
        "- **Onion moves spread.** Maharashtra's price changes lead Uttar Pradesh, Punjab, Haryana and West Bengal by about a week, "
        "with correlations of 0.46 to 0.55. Tomato and potato move mostly at the same time.",
        f"- **A spike is defined as a price at least {SPIKE_RATIO:g} times the market's median over the previous 52 weeks.** Lower lines "
        "catch about a quarter of all weeks, which is too common to be useful.", "",
        "Correlations show timing, not cause. Price levels also drift up over time, which raises how often any fixed ratio is met.", "",
        "## Typical price moves", "", table(moves), "",
        "## Seasons", "", "Median percent above or below the surrounding year:", "",
        table(seasons.round(1).rename_axis("month").reset_index()), "",
        "## How often is a market above its previous year?", "", table(rates), "",
        f"## National spike episodes (at least {SPIKE_RATIO} times the previous year's median)", "", table(episodes), "",
        "## Do price changes spread between states?", "",
        f"Correlation of weekly changes, with the source state leading by up to {MAX_LAG} weeks. A best lag of 0 means they move together.", "",
        table(moved), "",
    ]), encoding="utf-8")


if __name__ == "__main__":
    main()
