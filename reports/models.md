# Models

Validation weeks 2019-01-01 to 2024-11-01, on the same points for every method. Numbers are mean absolute percent error, lower is better. `gain_pct` is LightGBM's reduction against `this_week`. Written by `python -m src.models`.

| crop | weeks_ahead | points | alpha | this_week | smoothing | lightgbm | gain_pct | without_source_state |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | 1 | 30,825 | 1.0 | 11.08 | 11.08 | 10.43 | 5.9 | 10.53 |
| Onion | 2 | 30,701 | 1.0 | 16.3 | 16.3 | 14.56 | 10.6 | 14.73 |
| Onion | 4 | 30,514 | 1.0 | 25.04 | 25.04 | 21.47 | 14.2 | 21.61 |
| Potato | 1 | 27,045 | 1.0 | 6.49 | 6.49 | 6.26 | 3.6 | 6.27 |
| Potato | 2 | 26,961 | 1.0 | 10.01 | 10.01 | 9.3 | 7.1 | 9.33 |
| Potato | 4 | 26,836 | 1.0 | 15.94 | 15.94 | 13.57 | 14.9 | 13.59 |
| Tomato | 1 | 26,031 | 1.0 | 16.01 | 16.01 | 15.17 | 5.2 | 15.19 |
| Tomato | 2 | 25,885 | 1.0 | 24.12 | 24.12 | 21.78 | 9.7 | 21.89 |
| Tomato | 4 | 25,672 | 1.0 | 37.44 | 37.44 | 31.49 | 15.9 | 31.65 |

## Years LightGBM beat next week equals this week

| crop | weeks_ahead | sum | size |
| --- | --- | --- | --- |
| Onion | 1 | 6 | 6 |
| Onion | 2 | 6 | 6 |
| Onion | 4 | 6 | 6 |
| Potato | 1 | 5 | 6 |
| Potato | 2 | 5 | 6 |
| Potato | 4 | 5 | 6 |
| Tomato | 1 | 6 | 6 |
| Tomato | 2 | 6 | 6 |
| Tomato | 4 | 6 | 6 |

## Error by year

| crop | weeks_ahead | year | this_week | lightgbm |
| --- | --- | --- | --- | --- |
| Onion | 1 | 2019 | 10.7 | 10.3 |
| Onion | 1 | 2020 | 14.0 | 12.5 |
| Onion | 1 | 2021 | 11.3 | 10.7 |
| Onion | 1 | 2022 | 9.3 | 9.0 |
| Onion | 1 | 2023 | 12.4 | 11.5 |
| Onion | 1 | 2024 | 8.7 | 8.4 |
| Onion | 2 | 2019 | 14.9 | 13.7 |
| Onion | 2 | 2020 | 22.1 | 17.8 |
| Onion | 2 | 2021 | 17.4 | 16.0 |
| Onion | 2 | 2022 | 13.6 | 12.7 |
| Onion | 2 | 2023 | 17.4 | 15.7 |
| Onion | 2 | 2024 | 12.6 | 11.5 |
| Onion | 4 | 2019 | 21.5 | 19.2 |
| Onion | 4 | 2020 | 37.4 | 26.5 |
| Onion | 4 | 2021 | 27.1 | 25.5 |
| Onion | 4 | 2022 | 20.9 | 19.4 |
| Onion | 4 | 2023 | 24.0 | 21.3 |
| Onion | 4 | 2024 | 20.5 | 17.2 |
| Potato | 1 | 2019 | 6.3 | 6.4 |
| Potato | 1 | 2020 | 8.0 | 7.4 |
| Potato | 1 | 2021 | 7.5 | 7.1 |
| Potato | 1 | 2022 | 6.2 | 6.0 |
| Potato | 1 | 2023 | 6.2 | 6.1 |
| Potato | 1 | 2024 | 4.9 | 4.7 |
| Potato | 2 | 2019 | 9.3 | 9.8 |
| Potato | 2 | 2020 | 13.0 | 11.0 |
| Potato | 2 | 2021 | 12.1 | 10.8 |
| Potato | 2 | 2022 | 9.3 | 8.6 |
| Potato | 2 | 2023 | 9.3 | 8.8 |
| Potato | 2 | 2024 | 7.4 | 6.8 |
| Potato | 4 | 2019 | 13.7 | 14.1 |
| Potato | 4 | 2020 | 20.9 | 17.2 |
| Potato | 4 | 2021 | 20.9 | 15.5 |
| Potato | 4 | 2022 | 14.2 | 12.4 |
| Potato | 4 | 2023 | 14.5 | 12.9 |
| Potato | 4 | 2024 | 11.9 | 9.5 |
| Tomato | 1 | 2019 | 14.7 | 14.4 |
| Tomato | 1 | 2020 | 14.4 | 14.1 |
| Tomato | 1 | 2021 | 15.2 | 15.1 |
| Tomato | 1 | 2022 | 17.0 | 16.0 |
| Tomato | 1 | 2023 | 18.2 | 16.2 |
| Tomato | 1 | 2024 | 16.5 | 15.1 |
| Tomato | 2 | 2019 | 21.7 | 20.5 |
| Tomato | 2 | 2020 | 20.8 | 20.0 |
| Tomato | 2 | 2021 | 22.0 | 21.7 |
| Tomato | 2 | 2022 | 26.6 | 23.2 |
| Tomato | 2 | 2023 | 29.0 | 23.9 |
| Tomato | 2 | 2024 | 24.4 | 21.2 |
| Tomato | 4 | 2019 | 31.1 | 27.8 |
| Tomato | 4 | 2020 | 30.3 | 28.4 |
| Tomato | 4 | 2021 | 32.1 | 32.0 |
| Tomato | 4 | 2022 | 44.9 | 33.6 |
| Tomato | 4 | 2023 | 50.4 | 38.7 |
| Tomato | 4 | 2024 | 35.1 | 28.2 |

## Weeks already in a spike

| crop | weeks_ahead | this_week | lightgbm |
| --- | --- | --- | --- |
| Onion | 1 | 15.3 | 13.8 |
| Onion | 2 | 22.2 | 18.8 |
| Onion | 4 | 33.6 | 26.8 |
| Potato | 1 | 7.7 | 7.7 |
| Potato | 2 | 12.5 | 13.0 |
| Potato | 4 | 19.3 | 20.4 |
| Tomato | 1 | 18.9 | 17.7 |
| Tomato | 2 | 27.9 | 26.1 |
| Tomato | 4 | 41.1 | 38.5 |

## Check with shuffled training targets

A model with nothing to learn should show no real gain.

| crop | real_gain_pct | shuffled_targets_gain_pct |
| --- | --- | --- |
| Onion | 14.2 | -1.0 |
| Potato | 14.9 | -0.3 |
| Tomato | 15.9 | 0.2 |

## Features doing the most work

- Onion 1w: {'source_change_1': 0.12, 'source_change_4': 0.097, 'crop_change_1': 0.069, 'state_change_4': 0.068, 'above_year_median': 0.068}
- Onion 2w: {'source_change_4': 0.129, 'crop_change_1': 0.099, 'source_change_1': 0.092, 'source_change_2': 0.078, 'above_year_median': 0.074}
- Onion 4w: {'week_cos': 0.134, 'source_change_4': 0.11, 'source_change_2': 0.102, 'week_sin': 0.096, 'crop_change_1': 0.087}
- Potato 1w: {'state_code': 0.114, 'state_change_1': 0.098, 'crop_change_1': 0.082, 'crop_change_4': 0.061, 'state_change_4': 0.059}
- Potato 2w: {'week_cos': 0.123, 'crop_change_1': 0.091, 'state_code': 0.089, 'above_year_median': 0.08, 'week_sin': 0.073}
- Potato 4w: {'week_cos': 0.155, 'week_sin': 0.123, 'above_year_median': 0.091, 'crop_change_4': 0.084, 'source_change_4': 0.08}
- Tomato 1w: {'above_year_median': 0.113, 'state_change_4': 0.101, 'crop_change_1': 0.095, 'source_change_1': 0.089, 'state_change_1': 0.082}
- Tomato 2w: {'above_year_median': 0.132, 'state_change_4': 0.101, 'week_cos': 0.092, 'crop_change_1': 0.083, 'source_change_1': 0.072}
- Tomato 4w: {'above_year_median': 0.17, 'week_cos': 0.11, 'week_sin': 0.094, 'source_change_4': 0.077, 'state_change_1': 0.075}
