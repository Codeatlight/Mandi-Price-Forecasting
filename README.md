# Mandi Crop Price Forecasting

Forecast wholesale onion, tomato and potato prices across Indian mandis, and warn early when a price spike is likely. These three crops swing sharply in price, which hits farmers and households alike.

> Status: data collected (step 1 done). Results get filled in as the work is done.

## Data

Daily minimum, maximum and modal (most common) wholesale prices by market, from the [Variety-wise Daily Market Prices Data of Commodity](https://www.data.gov.in/resource/variety-wise-daily-market-prices-data-commodity) dataset on data.gov.in. It is published by the Directorate of Marketing and Inspection from [Agmarknet](https://agmarknet.gov.in), under the Open Government License India.

Collected so far: the 20 busiest districts for each crop in 2024, with their full histories.

| Crop | Rows | First record | Last record | Markets (as spelled in the data) |
| --- | --- | --- | --- | --- |
| Onion | 559,485 | 2001-03-30 | 2026-10-31 | 420 |
| Potato | 518,068 | 2001-03-30 | 2026-10-31 | 318 |
| Tomato | 481,160 | 2002-01-09 | 2026-10-31 | 357 |

Records are thin before about 2007 and fuller from 2010. This dataset has prices only, with no arrival quantities.

**To get it:** create a free key on data.gov.in and put `DATA_GOV_IN_API_KEY=your_key` in a `.env` file, which stays out of git. Then run `python -m src.collect --rank` and `python -m src.collect`. The data stays out of git too.

**Known problems for step 2:** about 106,000 exact duplicate rows, impossible prices (up to 917,588,483 per quintal, and 299 rows with minimum above maximum), and market names whose spelling changes over time, such as `APMC Chandwad` and `AGRICULTURE PRODUCE MARKET COMITEE CHANDWAD`.

Agmarknet data should be credited as the source wherever it's used. Weather and arrivals are optional later additions.

## Plan

1. **Collect.** The busiest 20 districts for each of the three crops, with the source and date of each download recorded in `data/raw/manifest.json`.
2. **Clean.** Fix unit errors and impossible prices, match spelling differences in market names, and handle holidays and gaps.
3. **Explore.** Seasonality, harvest cycles, how a price move in one mandi spreads to others, and how storable crops differ from perishable ones.
4. **Baselines first.** "Next week equals this week" and "same week last year". Every model must beat these.
5. **Models.** SARIMA or ETS per market, then one LightGBM model across all markets, using lagged prices and calendar features.
6. **Validate.** Rolling-origin backtests, never random splits. Report MAPE and error against the baselines at 1, 2 and 4 weeks ahead.
7. **Uncertainty.** Prediction intervals with quantile models, checked for how often the real price falls inside them.
8. **Spike alerts.** Define a spike clearly, then measure how many were flagged in advance, and how many alerts were false.
9. **App.** A Streamlit page: pick a crop and market to see history, the forecast range and any spike warning.

## Project layout

```
data/raw/          Downloads from Agmarknet sources (not in git)
data/processed/    Cleaned tables (not in git)
notebooks/         Exploration and experiments, numbered in order
src/               Reusable code: collection, cleaning, features, backtesting
models/            Saved models (not in git)
app/               Streamlit app
reports/figures/   Charts for the README
```

## Setup

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

## Results

To be filled in from the backtests.
