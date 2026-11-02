# Exploration

Weeks before 2024-11-01 only. Written by `python -m src.explore`. Prices are rupees per quintal.

## Findings

- **Perishability shows up clearly.** A typical four-week move is about 12% for potato, 20% for onion and 32% for tomato.
- **Each crop has its own season.** Onion runs about 27% below its year in May and 48% above in November. Tomato jumps about 45% in July. Potato bottoms in February and is the gentlest.
- **Spikes recur.** Most of onion's start in the second half of the year: 2010, 2013, 2015, 2017, 2019, 2020 and 2023 all had one.
- **Onion moves spread.** Maharashtra's price changes lead Uttar Pradesh, Punjab, Haryana and West Bengal by about a week, with correlations of 0.46 to 0.55. Tomato and potato move mostly at the same time.
- **A spike is defined as a price at least 2 times the market's median over the previous 52 weeks.** Lower lines catch about a quarter of all weeks, which is too common to be useful.

Correlations show timing, not cause. Price levels also drift up over time, which raises how often any fixed ratio is met.

## Typical price moves

| crop | typical_1w_move_pct | typical_2w_move_pct | typical_4w_move_pct | weeks_up_or_down_20pct |
| --- | --- | --- | --- | --- |
| Onion | 7.4 | 11.9 | 20.0 | 20.5 |
| Potato | 4.0 | 6.9 | 11.8 | 11.2 |
| Tomato | 11.8 | 20.0 | 32.2 | 34.6 |

## Seasons

Median percent above or below the surrounding year:

| month | Onion | Potato | Tomato |
| --- | --- | --- | --- |
| 1 | 3.7 | -22.4 | -10.9 |
| 2 | 0.0 | -27.1 | -17.1 |
| 3 | -5.8 | -20.4 | -11.8 |
| 4 | -25.3 | -9.1 | -12.7 |
| 5 | -26.7 | 0.0 | -20.8 |
| 6 | -12.0 | 4.4 | -0.7 |
| 7 | 0.0 | 9.9 | 45.5 |
| 8 | 4.0 | 10.2 | 26.3 |
| 9 | 10.9 | 5.3 | 6.7 |
| 10 | 43.8 | 6.4 | 17.5 |
| 11 | 48.1 | 9.5 | 20.5 |
| 12 | 10.0 | 0.0 | 0.0 |

## How often is a market above its previous year?

| at_least_x_times_last_year | Onion | Potato | Tomato |
| --- | --- | --- | --- |
| 1.25 | 33.8% | 35.3% | 36.3% |
| 1.5 | 23.4% | 22.0% | 25.2% |
| 1.75 | 16.9% | 12.2% | 17.5% |
| 2.0 | 12.9% | 6.6% | 12.7% |

## National spike episodes (at least 2.0 times the previous year's median)

| crop | start | weeks | peak_price | peak_vs_last_year |
| --- | --- | --- | --- | --- |
| Onion | 2010-09-27 | 18 | 3500 | 3.5 |
| Onion | 2013-01-21 | 5 | 1800 | 2.5 |
| Onion | 2013-07-29 | 17 | 5225 | 4.3 |
| Onion | 2015-08-10 | 10 | 4800 | 2.9 |
| Onion | 2017-08-07 | 25 | 3308 | 3.7 |
| Onion | 2019-08-26 | 24 | 7825 | 7.2 |
| Onion | 2020-10-19 | 2 | 4500 | 2.2 |
| Onion | 2023-10-16 | 8 | 4000 | 2.8 |
| Potato | 2012-06-18 | 12 | 1185 | 2.1 |
| Potato | 2016-05-09 | 12 | 1625 | 2.2 |
| Potato | 2018-05-07 | 18 | 1362 | 2.3 |
| Potato | 2020-11-02 | 4 | 3350 | 2.1 |
| Tomato | 2010-06-28 | 4 | 2200 | 2.7 |
| Tomato | 2010-12-27 | 1 | 2391 | 2.3 |
| Tomato | 2012-04-02 | 1 | 2100 | 2.1 |
| Tomato | 2013-05-27 | 12 | 3100 | 2.6 |
| Tomato | 2013-10-28 | 4 | 3500 | 2.1 |
| Tomato | 2014-07-14 | 7 | 3500 | 2.6 |
| Tomato | 2015-11-09 | 2 | 3500 | 2.2 |
| Tomato | 2016-06-06 | 2 | 4450 | 2.5 |
| Tomato | 2017-07-03 | 23 | 5000 | 3.8 |
| Tomato | 2020-09-07 | 3 | 3600 | 2.1 |
| Tomato | 2021-10-11 | 12 | 5000 | 3.3 |
| Tomato | 2023-06-26 | 9 | 8000 | 4.8 |
| Tomato | 2023-11-27 | 1 | 3200 | 2.0 |
| Tomato | 2024-07-15 | 2 | 5300 | 2.4 |
| Tomato | 2024-09-30 | 3 | 5200 | 2.3 |

## Do price changes spread between states?

Correlation of weekly changes, with the source state leading by up to 6 weeks. A best lag of 0 means they move together.

| crop | from | to | same_week | best_lag_weeks | best_correlation |
| --- | --- | --- | --- | --- | --- |
| Onion | Maharashtra | Haryana | 0.34 | 1 | 0.48 |
| Onion | Maharashtra | Kerala | 0.36 | 0 | 0.36 |
| Onion | Maharashtra | Madhya Pradesh | 0.36 | 0 | 0.36 |
| Onion | Maharashtra | Punjab | 0.43 | 1 | 0.54 |
| Onion | Maharashtra | Uttar Pradesh | 0.27 | 1 | 0.55 |
| Onion | Maharashtra | West Bengal | 0.37 | 1 | 0.46 |
| Potato | Uttar Pradesh | Haryana | 0.44 | 0 | 0.44 |
| Potato | Uttar Pradesh | Kerala | 0.16 | 2 | 0.2 |
| Potato | Uttar Pradesh | Maharashtra | 0.23 | 0 | 0.23 |
| Potato | Uttar Pradesh | Punjab | 0.44 | 0 | 0.44 |
| Potato | Uttar Pradesh | Tripura | 0.22 | 1 | 0.29 |
| Potato | Uttar Pradesh | West Bengal | 0.44 | -1 | 0.46 |
| Tomato | Maharashtra | Andhra Pradesh | 0.31 | 0 | 0.31 |
| Tomato | Maharashtra | Haryana | 0.25 | 1 | 0.28 |
| Tomato | Maharashtra | Karnataka | 0.37 | 0 | 0.37 |
| Tomato | Maharashtra | Kerala | 0.38 | 0 | 0.38 |
| Tomato | Maharashtra | Odisha | 0.27 | 0 | 0.27 |
| Tomato | Maharashtra | Punjab | 0.36 | 0 | 0.36 |
| Tomato | Maharashtra | Uttar Pradesh | 0.25 | 1 | 0.35 |
