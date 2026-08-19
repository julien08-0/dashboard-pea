# Dashboard PEA

Multi-ETF PEA portfolio tracking dashboard: starting from a transaction
export, it computes performance metrics per ETF and for the overall
portfolio, and displays them in an interactive Streamlit interface.

## View the project

**Just one click:** [dashboard-pea-julien.streamlit.app](https://dashboard-pea-julien.streamlit.app/)

No installation, no configuration needed — the app is already live with
demo data *(anonymized — see below)*. The following sections
(architecture, running locally) are only useful for those who want to look
at the code in more detail.

## Features

- **Per-ETF metrics**: TWR, CAGR, MWR, volatility, Sharpe ratio, Sortino
  ratio, Max Drawdown
- **Overall portfolio**: capital allocation, risk contribution per asset,
  correlation matrix between ETFs
- **Efficient frontier**: simulation of random portfolios and computation of
  the optimal portfolio (max Sharpe) relative to the current portfolio
- **History**: price chart per ETF with purchase points, evolution of each
  position's value over time

## Architecture

- `new_code.py` — loads transactions, fetches historical prices (yfinance)
  and computes all metrics. A single configuration dictionary (`ETFS`)
  drives everything: adding a tracked ETF only requires editing this entry,
  nothing else in the rest of the code.
- `new_dashboard.py` — Streamlit interface, entirely generated from this
  same configuration (no ETF is hardcoded on the interface side).

## Tech stack

Python · Streamlit · pandas · numpy · yfinance · scipy · plotly

## Running locally

```bash
cd code_PEA
python -m venv venv
venv\Scripts\activate          # Windows
pip install -r requirements.txt
streamlit run new_dashboard.py
```

By default, the app uses the anonymized demo file
(`code_PEA/data/extraction_demo.xlsx`). To use your own PEA export, set the
`PEA_EXCEL_PATH` environment variable to point to your file before launching
Streamlit:

```bash
set PEA_EXCEL_PATH=path\to\my_export.xlsx   # Windows (cmd)
streamlit run new_dashboard.py
```

## About the demo data

The file `code_PEA/data/extraction_demo.xlsx` is an anonymized version of a
real PEA transaction history: the tracked ETFs and operation dates are real,
but the quantities and invested amounts have been randomized (and
deliberately amplified) so as not to represent any plausible real portfolio.
The displayed prices remain the real market prices of each ETF, so that the
charts stay consistent.
