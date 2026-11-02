"""Clean the raw prices and build one weekly price series per crop and market.

The order matters, and every stage's row count goes into reports/cleaning_report.md
so nothing disappears unnoticed:
  1. Drop exact duplicates, and years too thin to model.
  2. Join up market names, which changed when Agmarknet 2.0 launched in November 2025.
  3. Remove impossible prices, then prices far from the market's own recent level.
  4. Take the median across varieties for each market and day, then each week.

The outlier check looks at dates on both sides of each price, which is fine for
tidying history. A live app must use a backward-only version instead.

Prices are in rupees per quintal (100 kg).

Run from the project root:  python -m src.clean
"""
import glob
import re
from pathlib import Path

import pandas as pd

from src.collect import NEW_DISTRICT_NAMES

RAW = Path("data/raw")
PROCESSED = Path("data/processed")
REPORT = Path("reports/cleaning_report.md")

START = "2010-01-01"  # earlier years are too thin to model
LOWEST_PRICE = 20
HIGHEST_PRICE = 30_000  # 300 rupees a kg, above even the 2023 tomato peak
LEVEL_WINDOW_DAYS = 91
LEVEL_MIN_DAYS = 15
MAX_RATIO = 5  # a price this many times above or below the market's own level is an error
COVERAGE_FROM = "2015-01-01"
MIN_WEEK_COVERAGE = 0.6  # keep markets that report in most weeks
ACTIVE_SINCE = "2026-01-01"  # and that are still reporting
RECENT_WEEKS = 4
NAME_FIXES = {"CHANDWAD": "CHANDVAD", "PIMPALGAON BASWANT": "PIMPALGAON"}
OLD_DISTRICT_NAMES = {new: old for old, new in NEW_DISTRICT_NAMES.items()}


def load():
    frame = pd.concat([pd.read_csv(f, dtype=str) for f in glob.glob(str(RAW / "*" / "*.csv.gz"))], ignore_index=True)
    frame["date"] = pd.to_datetime(frame["Arrival_Date"], format="%d/%m/%Y")
    for column in ["Min_Price", "Max_Price", "Modal_Price"]:
        frame[column] = pd.to_numeric(frame[column])
    frame["District"] = frame["District"].replace(OLD_DISTRICT_NAMES)  # keep one series across renames
    return frame.drop(columns=["Arrival_Date", "Commodity_Code"])


def clean_market_name(name):
    """Agmarknet 2.0 added APMC to names, so remove it, then join known spelling variants."""
    name = re.sub(r"\s+", " ", name.upper()).strip()
    name = re.sub(r"^AGRICULTURE PRODUCE MARKET COMITEE\s+", "", name)
    name = re.sub(r"^APMC\s+", "", name)
    name = re.sub(r"\s+APMC$", "", name).strip()
    return NAME_FIXES.get(name, name)


def market_level(rows):
    """Each market's usual price around each date: a median of its daily medians."""
    daily = rows.groupby(["Commodity", "State", "District", "market", "date"], as_index=False)["Modal_Price"].median()
    levels = []
    for _, group in daily.groupby(["Commodity", "State", "District", "market"]):
        series = group.set_index("date")["Modal_Price"].sort_index()
        level = series.rolling(f"{LEVEL_WINDOW_DAYS}D", center=True, min_periods=LEVEL_MIN_DAYS).median()
        levels.append(group.assign(level=level.to_numpy()))
    return pd.concat(levels)[["Commodity", "State", "District", "market", "date", "level"]]


def weekly_series(daily):
    """Median price per market and week, with weeks starting on Monday."""
    week = daily["date"].dt.to_period("W-SUN").dt.start_time
    return (daily.assign(week=week)
            .groupby(["Commodity", "State", "District", "market", "week"], as_index=False)
            .agg(price=("price", "median"), days_reported=("price", "size")))


def coverage(weekly):
    """Share of weeks each market reported since COVERAGE_FROM, and its last report."""
    recent = weekly[weekly["week"] >= COVERAGE_FROM]
    all_weeks = recent["week"].nunique()
    keys = ["Commodity", "State", "District", "market"]
    result = recent.groupby(keys).agg(weeks=("week", "nunique"), last_week=("week", "max")).reset_index()
    result["coverage"] = (result["weeks"] / all_weeks).round(3)
    result["kept"] = (result["coverage"] >= MIN_WEEK_COVERAGE) & (result["last_week"] >= ACTIVE_SINCE)
    return result


def table(frame):
    rows = [list(frame.columns), ["---"] * frame.shape[1], *frame.astype(str).values.tolist()]
    return "\n".join("| " + " | ".join(map(str, row)) + " |" for row in rows)


def main():
    stages = []
    note = lambda stage, frame: stages.append({"stage": stage, "rows": f"{len(frame):,}"})

    rows = load()
    note("Raw download", rows)
    rows = rows.drop_duplicates()
    note("Exact duplicates removed", rows)
    rows = rows[rows["date"] >= START].copy()
    note(f"From {START} onward", rows)

    names_before = rows.groupby(["District", "Market"]).ngroups
    rows["market"] = rows["Market"].map(clean_market_name)
    names_after = rows.groupby(["District", "market"]).ngroups

    possible = rows["Modal_Price"].between(LOWEST_PRICE, HIGHEST_PRICE)
    impossible = rows[~possible]
    rows = rows[possible].copy()
    note(f"Modal price between {LOWEST_PRICE} and {HIGHEST_PRICE:,}", rows)

    swapped = rows["Min_Price"] > rows["Max_Price"]
    rows.loc[swapped, ["Min_Price", "Max_Price"]] = rows.loc[swapped, ["Max_Price", "Min_Price"]].to_numpy()

    keys = ["Commodity", "State", "District", "market", "date"]
    rows = rows.merge(market_level(rows), on=keys, how="left")
    ratio = rows["Modal_Price"] / rows["level"]
    far = (ratio > MAX_RATIO) | (ratio < 1 / MAX_RATIO)
    removed = rows[far]
    rows = rows[~far].copy()
    note(f"Within {MAX_RATIO} times of the market's own level", rows)

    daily = rows.groupby(keys, as_index=False).agg(
        price=("Modal_Price", "median"), low=("Min_Price", "median"), high=("Max_Price", "median"),
        varieties=("Variety", "nunique"))
    note("One row per crop, market and day", daily)

    weekly = weekly_series(daily)
    note("One row per crop, market and week", weekly)
    covered = coverage(weekly)
    kept = covered[covered["kept"]]
    weekly = weekly.merge(kept[["Commodity", "State", "District", "market"]], on=["Commodity", "State", "District", "market"])
    note("Weeks in steadily reporting markets", weekly)

    latest_week = weekly["week"].max()
    kept = kept.assign(reporting_now=kept["last_week"] >= latest_week - pd.Timedelta(weeks=RECENT_WEEKS))
    PROCESSED.mkdir(exist_ok=True)
    daily.to_parquet(PROCESSED / "daily_prices.parquet", index=False)
    weekly.to_parquet(PROCESSED / "weekly_prices.parquet", index=False)
    kept.drop(columns="kept").to_parquet(PROCESSED / "markets.parquet", index=False)
    silent = kept[~kept["reporting_now"]].groupby(["Commodity", "State"]).agg(
        markets=("market", "size"), last_report=("last_week", "max")).reset_index().assign(
        last_report=lambda d: d["last_report"].dt.date)
    reporting = kept.groupby("Commodity")["reporting_now"].agg(["size", "sum"]).reset_index().rename(
        columns={"size": "markets", "sum": "reporting_now"})

    summary = kept.groupby("Commodity").agg(markets=("market", "size"), median_coverage=("coverage", "median")).reset_index()
    summary = summary.merge(covered.groupby("Commodity").size().rename("markets_before").reset_index())
    examples = removed.assign(ratio=ratio[far].round(1)).nlargest(8, "ratio")[
        ["date", "Commodity", "market", "Modal_Price", "level", "ratio"]].assign(date=lambda d: d["date"].dt.date)
    by_year = removed.groupby(removed["date"].dt.year).size().rename("removed").rename_axis("year").reset_index().tail(6)

    lines = [
        "# Cleaning report", "", "Written by `python -m src.clean`. Prices are rupees per quintal.", "",
        "## Rows at each stage", "", table(pd.DataFrame(stages)), "",
        f"Market names went from {names_before} to {names_after} after removing APMC labels and joining spelling variants. "
        f"Prices outside the possible range: {len(impossible):,}. Rows with minimum and maximum swapped back: {int(swapped.sum()):,}. "
        f"Rows far from their market's level: {len(removed):,}.", "",
        "## Markets kept", "",
        f"Kept if reporting in at least {MIN_WEEK_COVERAGE:.0%} of weeks since {COVERAGE_FROM} and still reporting in 2026.", "",
        table(summary), "",
        "## Markets that have gone quiet", "",
        f"Latest week in the data: {latest_week.date()}. A market counts as reporting now if it has a price in the last "
        f"{RECENT_WEEKS} weeks. Quiet markets stay useful for backtests, but the app must not show live forecasts for them.", "",
        table(reporting), "", table(silent), "",
        "## Largest prices removed for being far from the market's level", "", table(examples), "",
        "## Removals by year", "", table(by_year), "",
    ]
    REPORT.write_text("\n".join(lines), encoding="utf-8")
    print(pd.DataFrame(stages).to_string(index=False))
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
