# Baselines

Validation weeks 2019-01-01 to 2024-11-01. Written by `python -m src.backtest`. All methods are scored on the same crop, market and week points, so they compare directly.

## Mean absolute percent error, lower is better

| crop | weeks_ahead | points | this_week | same_week_last_year | this_week_plus_last_years_change |
| --- | --- | --- | --- | --- | --- |
| Onion | 1 | 29,222 | 11.1 | 46.7 | 16.8 |
| Potato | 1 | 25,746 | 6.5 | 46.3 | 10.1 |
| Tomato | 1 | 24,223 | 15.9 | 52.0 | 24.6 |
| Onion | 2 | 28,980 | 16.4 | 46.7 | 23.7 |
| Potato | 2 | 25,565 | 10.0 | 46.2 | 14.8 |
| Tomato | 2 | 23,950 | 23.9 | 51.9 | 36.6 |
| Onion | 4 | 28,618 | 25.2 | 46.6 | 33.5 |
| Potato | 4 | 25,293 | 15.9 | 46.2 | 22.2 |
| Tomato | 4 | 23,566 | 37.1 | 52.0 | 56.6 |

## The same, only for weeks already in a spike

| crop | weeks_ahead | this_week | same_week_last_year | this_week_plus_last_years_change |
| --- | --- | --- | --- | --- |
| Onion | 1 | 15.3 | 58.9 | 21.4 |
| Potato | 1 | 7.6 | 59.3 | 11.4 |
| Tomato | 1 | 18.9 | 53.2 | 26.6 |
| Onion | 2 | 22.3 | 58.9 | 30.2 |
| Potato | 2 | 12.4 | 59.2 | 17.1 |
| Tomato | 2 | 27.9 | 53.2 | 38.2 |
| Onion | 4 | 33.9 | 58.8 | 41.4 |
| Potato | 4 | 19.1 | 59.1 | 24.6 |
| Tomato | 4 | 41.2 | 53.5 | 53.1 |
