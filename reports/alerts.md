# Spike alerts

Question: at a market not in a spike, will a price of at least 2 times its previous-year median begin within 4 weeks? Scored on 2020 to October 2024. Written by `python -m src.alerts`.

`alerts_correct_pct` is the share of alerts followed by a spike. `spikes_warned_pct` is the share of spikes with an alert in the 4 weeks before. The rule alerts when a market is at least 1.5 times normal and rose about 10% in four weeks.

| crop | method | alerts | alerts_correct_pct | spikes | spikes_warned_pct | median_warning_weeks | false_alerts_per_market_year |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Onion | model | 2,332 | 28.2 | 310 | 79.7 | 4.0 | 2.9 |
| Onion | rule | 1,744 | 26.9 | 310 | 73.9 | 2.0 | 2.2 |
| Potato | model | 2,475 | 10.3 | 121 | 75.2 | 4.0 | 4.5 |
| Potato | rule | 1,883 | 9.5 | 121 | 63.6 | 3.0 | 3.4 |
| Tomato | model | 2,829 | 35.6 | 474 | 88.6 | 3.0 | 3.6 |
| Tomato | rule | 1,300 | 34.8 | 474 | 60.3 | 2.0 | 1.7 |

## Ranking quality

Average precision, where the share with a spike coming is what guessing scores. The calendar score uses only how often spikes came in each month in earlier years, so beating it shows the model does more than recognise the season.

| crop | share_with_spike_coming_pct | model_precision_score | calendar_only_score | rule_ratio_only_score | shuffled_targets_score |
| --- | --- | --- | --- | --- | --- |
| Onion | 4.82 | 32.8 | 8.0 | 21.5 | 3.2 |
| Potato | 1.93 | 14.6 | 2.2 | 15.6 | 1.9 |
| Tomato | 9.66 | 44.5 | 21.0 | 18.3 | 9.6 |
