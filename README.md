# Mandi Crop Price Forecasting

Forecast wholesale onion, tomato and potato prices across Indian mandis, and warn early when a price spike is likely. These three crops swing sharply in price, which hits farmers and households alike.

> Status: set up. No analysis yet; the results sections get filled in as the work is done.

## Data

Daily minimum, maximum and modal (most common) wholesale prices, plus arrival quantities where available, collected by Agmarknet.

| Source | Use | Note |
| --- | --- | --- |
| [Ashoka CEDA Agmarknet](https://agmarknet.ceda.ashoka.edu.in/README.html) | Main source of history | Says it covers data from 2001, 344 commodities, 650+ districts. Export limits and terms still need checking |
| [data.gov.in daily mandi prices](https://data.gov.in/resource/current-daily-price-various-commodities-various-markets-mandi) | Live prices for the app | Appears to cover current prices rather than history; needs a free API key |
| [`agmarknet` Python package](https://pypi.org/project/agmarknet/) | Fallback | Unofficial; not affiliated with the government |

Agmarknet data should be credited as the source wherever it's used. Weather data (rainfall, temperature) is an optional later addition.

## Plan

1. **Collect.** Start with one crop across about 20 large mandis, then add the others. Confirm how far back the data really goes, and record the source and date of each download.
2. **Clean.** Fix unit errors and impossible prices, match spelling differences in market names, and handle holidays and gaps.
3. **Explore.** Seasonality, harvest cycles, how a price move in one mandi spreads to others, and how arrivals relate to prices.
4. **Baselines first.** "Next week equals this week" and "same week last year". Every model must beat these.
5. **Models.** SARIMA or ETS per market, then one LightGBM model across all markets, using lagged prices, arrivals and calendar features.
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
