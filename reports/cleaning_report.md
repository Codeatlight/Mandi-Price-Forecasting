# Cleaning report

Written by `python -m src.clean`. Prices are rupees per quintal.

## Rows at each stage

| stage | rows |
| --- | --- |
| Raw download | 1,562,930 |
| Exact duplicates removed | 1,456,384 |
| From 2010-01-01 onward | 1,295,248 |
| Modal price between 20 and 30,000 | 1,294,775 |
| Within 5 times of the market's own level | 1,294,236 |
| One row per crop, market and day | 1,225,199 |
| One row per crop, market and week | 278,001 |
| Weeks in steadily reporting markets | 220,938 |

Market names went from 666 to 362 after removing APMC labels and joining spelling variants. Prices outside the possible range: 473. Rows with minimum and maximum swapped back: 261. Rows far from their market's level: 539.

## Markets kept

Kept if reporting in at least 60% of weeks since 2015-01-01 and still reporting in 2026.

| Commodity | markets | median_coverage | markets_before |
| --- | --- | --- | --- |
| Onion | 116 | 0.907 | 208 |
| Potato | 99 | 0.911 | 169 |
| Tomato | 102 | 0.8685 | 197 |

## Markets that have gone quiet

Latest week in the data: 2026-10-26. A market counts as reporting now if it has a price in the last 4 weeks. Quiet markets stay useful for backtests, but the app must not show live forecasts for them.

| Commodity | markets | reporting_now |
| --- | --- | --- |
| Onion | 116 | 84 |
| Potato | 99 | 83 |
| Tomato | 102 | 55 |

| Commodity | State | markets | last_report |
| --- | --- | --- | --- |
| Onion | Kerala | 25 | 2026-05-18 |
| Onion | Maharashtra | 1 | 2026-05-11 |
| Onion | Uttar Pradesh | 6 | 2026-08-24 |
| Potato | Kerala | 14 | 2026-05-18 |
| Potato | Punjab | 1 | 2026-07-06 |
| Potato | West Bengal | 1 | 2026-09-14 |
| Tomato | Karnataka | 2 | 2026-05-25 |
| Tomato | Kerala | 38 | 2026-05-18 |
| Tomato | Punjab | 2 | 2026-08-24 |
| Tomato | Uttar Pradesh | 5 | 2026-09-21 |

## Largest prices removed for being far from the market's level

| date | Commodity | market | Modal_Price | level | ratio |
| --- | --- | --- | --- | --- | --- |
| 2017-07-29 | Potato | GONIANA | 5500.0 | 250.0 | 22.0 |
| 2025-08-19 | Onion | JUNNAR(ALEPHATA) | 25000.0 | 1375.0 | 18.2 |
| 2017-08-14 | Onion | RAMPURAPHUL(NABHA MANDI) | 2100.0 | 140.0 | 15.0 |
| 2025-08-14 | Onion | SHAJAPUR | 14888.0 | 1033.0 | 14.4 |
| 2025-08-14 | Onion | SHAJAPUR | 14888.0 | 1033.0 | 14.4 |
| 2017-12-19 | Potato | BATHINDA | 3200.0 | 225.0 | 14.2 |
| 2025-11-10 | Potato | BATHINDA | 13000.0 | 1000.0 | 13.0 |
| 2010-07-23 | Potato | HOSHIARPUR | 5000.0 | 390.0 | 12.8 |

## Removals by year

| year | removed |
| --- | --- |
| 2021 | 14 |
| 2022 | 13 |
| 2023 | 58 |
| 2024 | 26 |
| 2025 | 91 |
| 2026 | 6 |
