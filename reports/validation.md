# Validation

Validation weeks only. Written by `python -m src.validate`. Prices are rupees per quintal.

## Gain over next week equals this week

Intervals resample whole weeks. Typical error is the median, which big misses affect less.

| crop | weeks_ahead | gain_pct | interval_95 | error_rupees_base | error_rupees_model | typical_error_pct_base | typical_error_pct_model |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | 1 | 5.9 | 3.9 to 7.8 | 277 | 259 | 6.7 | 6.5 |
| Onion | 2 | 10.6 | 7.5 to 13.5 | 401 | 357 | 10.7 | 10.1 |
| Onion | 4 | 14.2 | 9.7 to 18.7 | 594 | 513 | 17.6 | 16.0 |
| Potato | 1 | 3.6 | 1.9 to 5.4 | 97 | 94 | 3.4 | 3.4 |
| Potato | 2 | 7.1 | 4.2 to 10.0 | 144 | 135 | 6.0 | 5.7 |
| Potato | 4 | 14.9 | 10.9 to 19.0 | 218 | 189 | 10.0 | 8.9 |
| Tomato | 1 | 5.2 | 3.3 to 7.2 | 402 | 378 | 10.4 | 10.0 |
| Tomato | 2 | 9.7 | 6.8 to 12.8 | 590 | 530 | 16.7 | 15.5 |
| Tomato | 4 | 15.9 | 11.8 to 19.9 | 876 | 739 | 25.0 | 23.3 |

## Gain by target month, 4 weeks ahead (percent)

| month | Onion | Potato | Tomato |
| --- | --- | --- | --- |
| 1 | 25 | 37 | 32 |
| 2 | 36 | 25 | 13 |
| 3 | 18 | 6 | -4 |
| 4 | 24 | 14 | 7 |
| 5 | 8 | 9 | 3 |
| 6 | 18 | 7 | 10 |
| 7 | -28 | 5 | 19 |
| 8 | 0 | -1 | 28 |
| 9 | 5 | 5 | 31 |
| 10 | 11 | 3 | -5 |
| 11 | 1 | 4 | 5 |
| 12 | 22 | 16 | 29 |

## Markets, 4 weeks ahead

| Commodity | markets | beat_baseline | worst | best |
| --- | --- | --- | --- | --- |
| Onion | 116 | 110 | -125.2 | 33.0 |
| Potato | 99 | 96 | -39.7 | 28.9 |
| Tomato | 102 | 97 | -26.8 | 27.6 |

Hardest markets:

| Commodity | State | market | gain |
| --- | --- | --- | --- |
| Onion | Uttar Pradesh | GULAVATI | -125.2 |
| Potato | Uttar Pradesh | DIVAI | -39.7 |
| Tomato | Kerala | KOLLAM | -26.8 |
| Onion | Punjab | BHUCHO | -23.6 |
| Potato | Uttar Pradesh | GULAVATI | -17.6 |
| Onion | Kerala | KOLLENGODE | -17.3 |
