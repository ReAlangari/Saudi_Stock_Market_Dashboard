# Saudi Stock Market Dashboard

A real-time financial dashboard for the Saudi Stock Exchange (Tadawul), built with **Python** and **Streamlit**. Covers all **223 TASI-listed stocks** across **21 sectors**. Powered by the [SAHMK API](https://app.sahmk.sa) for live market data.

## Live Demo

```bash
streamlit run app_fundamental.py
```

## Features

- **Market Summary** — TASI index, market mood, top dividend yielders, sector ROE heatmap
- **Valuation Multiples** — P/E vs P/B scatter plot with quadrant analysis, comparative table
- **Shariah Compliance** — Debt screening (<33% threshold), compliant vs non-compliant breakdown
- **Solvency** — Debt-to-Equity and Current Ratio analysis (banks excluded)
- **Profitability** — ROE comparison, net profit margin, revenue vs net income
- **Stock Deep Dive** — Individual stock lookup with 10 KPIs, radar chart, sector peer comparison
- **Jupyter Notebook** — Full analysis with charts (valuation, dividends, correlation matrix, sectors)

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| Framework | Streamlit |
| Charts | Plotly, Matplotlib, Seaborn |
| Data | Pandas, 223 stocks CSV |
| API | SAHMK API (REST) |

## Setup

```bash
# Install dependencies
pip install -r requirements.txt

# Add your API key
echo 'SAHMK_API_KEY="your_api_key_here"' > .env

# Run the dashboard
streamlit run app_fundamental.py
```

## Project Structure

```
saudi-market-dashboard/
├── app.py                      # Market dashboard
├── app_fundamental.py          # Fundamental analysis dashboard
├── analysis.ipynb              # Jupyter notebook
├── data/
│   └── saudi_stocks_fundamentals.csv   # 223 stocks, 18 columns
├── requirements.txt
├── .env
└── README.md
```

## Author

**Reema** — Data Analyst
