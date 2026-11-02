# Final test

One run on weeks from 2024-11-01, retrained before each test year. Written by `python -m src.final_test`, which refuses to run twice.

## Forecasts and 80% ranges

| crop | weeks_ahead | points | this_week | lightgbm | gain_pct | gain_95_interval | range_inside_pct | range_width_pct | inside_in_spikes_pct |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | 1 | 10,254 | 10.35 | 10.07 | 2.6 | 0.4 to 4.9 | 78.2 | 26.5 | 81.2 |
| Onion | 2 | 10,221 | 14.67 | 13.98 | 4.7 | 0.3 to 8.7 | 77.7 | 38.1 | 79.4 |
| Onion | 4 | 10,176 | 21.41 | 19.91 | 7.0 | -0.1 to 13.2 | 78.2 | 56.4 | 72.6 |
| Potato | 1 | 9,036 | 5.59 | 5.4 | 3.4 | 0.8 to 5.8 | 81.5 | 17.2 | 85.7 |
| Potato | 2 | 8,994 | 8.75 | 8.18 | 6.6 | 0.9 to 11.5 | 79.9 | 25.8 | 85.7 |
| Potato | 4 | 8,930 | 14.07 | 12.95 | 8.0 | -0.9 to 15.4 | 77.2 | 37.6 | 28.6 |
| Tomato | 1 | 8,320 | 13.87 | 13.42 | 3.2 | 0.5 to 6.0 | 81.9 | 42.1 | 71.6 |
| Tomato | 2 | 8,286 | 20.71 | 19.37 | 6.5 | 2.1 to 11.0 | 82.1 | 60.8 | 60.2 |
| Tomato | 4 | 8,228 | 31.23 | 27.13 | 13.1 | 5.9 to 19.5 | 83.5 | 93.3 | 42.8 |

## Spike alerts

| crop | method | alerts | alerts_correct_pct | spikes | spikes_warned_pct | median_warning_weeks | false_alerts_per_market_year |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | model | 392 | 45.9 | 92 | 79.3 | 3.0 | 0.6 |
| Onion | rule | 361 | 32.1 | 92 | 71.7 | 3.0 | 0.7 |
| Potato | model | 5 | 20.0 | 1 | 100.0 | 1.0 | 0.0 |
| Potato | rule | 33 | 3.0 | 1 | 100.0 | 1.0 | 0.1 |
| Tomato | model | 948 | 16.8 | 106 | 84.9 | 3.0 | 2.6 |
| Tomato | rule | 577 | 19.9 | 106 | 66.0 | 1.5 | 1.5 |

| crop | share_with_spike_coming_pct | model_score |
| --- | --- | --- |
| Onion | 3.46 | 47.8 |
| Potato | 0.05 | 25.6 |
| Tomato | 4.68 | 17.0 |
