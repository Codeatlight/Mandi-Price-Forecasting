# Forecast ranges

Target: the real price falls inside the range 80% of the time. Validation years from 2020. `inside` is the percent of real prices inside the range. `width` is the median range as a percent of the price, so lower is more useful if coverage holds. Written by `python -m src.intervals`.

| crop | weeks_ahead | points | raw_inside | calibrated_inside | calibrated_width | simple_band_inside | simple_band_width |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | 1 | 25,567 | 78.2 | 81.3 | 30.4 | 81.1 | 36.7 |
| Onion | 2 | 25,427 | 75.7 | 81.2 | 44.2 | 79.6 | 53.9 |
| Onion | 4 | 25,239 | 70.4 | 81.9 | 69.0 | 79.5 | 82.7 |
| Potato | 1 | 22,271 | 79.6 | 80.4 | 18.7 | 83.4 | 24.5 |
| Potato | 2 | 22,200 | 78.9 | 81.0 | 27.2 | 83.8 | 36.7 |
| Potato | 4 | 22,089 | 77.8 | 81.9 | 40.2 | 83.4 | 56.1 |
| Tomato | 1 | 21,289 | 77.6 | 80.0 | 45.0 | 80.9 | 55.3 |
| Tomato | 2 | 21,163 | 75.3 | 80.1 | 64.9 | 80.1 | 83.1 |
| Tomato | 4 | 20,986 | 71.8 | 80.4 | 97.4 | 79.1 | 125.8 |

## Weeks already in a spike

| crop | weeks_ahead | calibrated_inside | simple_band_inside |
| --- | --- | --- | --- |
| Onion | 1 | 74.0 | 68.8 |
| Onion | 2 | 72.8 | 64.7 |
| Onion | 4 | 66.1 | 53.8 |
| Potato | 1 | 74.2 | 79.7 |
| Potato | 2 | 68.9 | 79.4 |
| Potato | 4 | 60.7 | 79.6 |
| Tomato | 1 | 69.1 | 72.8 |
| Tomato | 2 | 63.0 | 67.8 |
| Tomato | 4 | 51.6 | 55.3 |

## Calibrated coverage by year

| crop | weeks_ahead | year | calibrated_inside |
| --- | --- | --- | --- |
| Onion | 1 | 2020 | 80.1 |
| Onion | 1 | 2021 | 80.8 |
| Onion | 1 | 2022 | 83.2 |
| Onion | 1 | 2023 | 76.3 |
| Onion | 1 | 2024 | 86.5 |
| Onion | 2 | 2020 | 78.4 |
| Onion | 2 | 2021 | 79.3 |
| Onion | 2 | 2022 | 86.9 |
| Onion | 2 | 2023 | 75.5 |
| Onion | 2 | 2024 | 85.9 |
| Onion | 4 | 2020 | 76.4 |
| Onion | 4 | 2021 | 79.2 |
| Onion | 4 | 2022 | 91.3 |
| Onion | 4 | 2023 | 75.8 |
| Onion | 4 | 2024 | 86.3 |
| Potato | 1 | 2020 | 79.2 |
| Potato | 1 | 2021 | 81.2 |
| Potato | 1 | 2022 | 80.1 |
| Potato | 1 | 2023 | 80.8 |
| Potato | 1 | 2024 | 80.6 |
| Potato | 2 | 2020 | 81.3 |
| Potato | 2 | 2021 | 80.7 |
| Potato | 2 | 2022 | 81.7 |
| Potato | 2 | 2023 | 80.9 |
| Potato | 2 | 2024 | 80.2 |
| Potato | 4 | 2020 | 79.6 |
| Potato | 4 | 2021 | 81.6 |
| Potato | 4 | 2022 | 83.8 |
| Potato | 4 | 2023 | 82.6 |
| Potato | 4 | 2024 | 81.5 |
| Tomato | 1 | 2020 | 83.4 |
| Tomato | 1 | 2021 | 76.3 |
| Tomato | 1 | 2022 | 79.6 |
| Tomato | 1 | 2023 | 81.9 |
| Tomato | 1 | 2024 | 78.6 |
| Tomato | 2 | 2020 | 82.8 |
| Tomato | 2 | 2021 | 75.9 |
| Tomato | 2 | 2022 | 80.5 |
| Tomato | 2 | 2023 | 81.4 |
| Tomato | 2 | 2024 | 79.8 |
| Tomato | 4 | 2020 | 85.0 |
| Tomato | 4 | 2021 | 72.9 |
| Tomato | 4 | 2022 | 80.8 |
| Tomato | 4 | 2023 | 77.0 |
| Tomato | 4 | 2024 | 86.9 |
