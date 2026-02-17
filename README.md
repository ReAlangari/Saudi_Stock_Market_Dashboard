# Saudi Stock Market Dashboard

A real-time financial dashboard and fundamental analysis platform for the Saudi Stock Exchange (Tadawul), built with **Python** and **Streamlit**. Covers all **223 TASI-listed stocks** across **21 sectors**. Powered by the [SAHMK API](https://app.sahmk.sa) for live market data.

## Live Demo

[View Dashboard](https://saudi-market-dashboard.streamlit.app)

## Features

### Dashboard 1: Live Market (`app.py`)

#### Market Overview
- **TASI Index** — Live index value with change and percentage
- **Market Mood Gauge** — Visual sentiment indicator (Bullish to Bearish)
- **Market Breadth** — Advancing vs Declining vs Unchanged stocks (donut chart)
- **Quick Movers** — Top 5 Gainers and Losers at a glance

#### Top Movers
- Gainers, Losers, Volume Leaders, Value Leaders
- Interactive bar charts with color-coded performance
- Adjustable result count (5-50)

#### Sector Performance
- **Sector Heatmap (Treemap)** — All 20 TASI sectors sized by volume, colored by performance
- **Horizontal Bar Chart** — Sector ranking by average change %

#### Stock Lookup & Liquidity Analysis
- Search any stock by symbol (e.g., `2222` for Aramco)
- Full quote data: Price, Open, High, Low, Volume, Bid/Ask
- Money inflow vs outflow, net flow indicator, buy vs sell comparison

#### Blue-Chip Watchlist
- Pre-configured watchlist of top TASI stocks
- Real-time price cards with net liquidity flow chart

---

### Dashboard 2: Fundamental Analysis (`app_fundamental.py`)

#### Market Summary & Dividends
- TASI index with market mood indicator
- Top 10 dividend yielders bar chart
- Sector ROE heatmap

#### Valuation Multiples
- P/E vs P/B scatter plot with quadrant analysis
- Bubble size = dividend yield, color = ROE
- Comparative valuation table for all 223 stocks

#### Shariah Compliance & Solvency
- Shariah screening (interest-bearing debt < 33% threshold)
- Compliant vs non-compliant breakdown
- Debt-to-Equity ratio comparison (banks excluded)
- Current Ratio analysis

#### Profitability & Efficiency
- ROE comparison (top performers + worst 10)
- Net profit margin ranking
- Revenue vs Net Income (top 12 companies)

#### Stock Deep Dive
- Individual stock selector with live price
- 10 fundamental KPIs (P/E, P/B, ROE, margin, D/E, current ratio)
- Radar chart — risk/return profile
- Balance sheet breakdown (revenue, debt, equity)
- Sector peer comparison table

---

### Jupyter Notebook Analysis

#### `analysis.ipynb` (Arabic company names)
- Full fundamental analysis with Arabic names on charts
- Uses `arabic_reshaper` + `python-bidi` for correct RTL rendering in matplotlib

#### `analysis_en.ipynb` (English)
- Same analysis, fully in English
- 10 sections: valuation, profitability, Shariah compliance, solvency, dividends, revenue, correlation matrix, sector comparison

## Tech Stack

| Component | Technology |
|-----------|-----------|
| Language | Python 3.13 |
| Framework | Streamlit |
| Charts | Plotly (dashboard), Matplotlib + Seaborn (notebook) |
| Data | Pandas, 223 stocks CSV |
| API | SAHMK API (REST, batched 50/request) |
| Arabic RTL | arabic-reshaper, python-bidi |
| Fonts | IBM Plex Sans Arabic, IBM Plex Mono, Tajawal |

## Installation

### Prerequisites
- Python 3.9 or higher
- A SAHMK API key ([Get one free](https://app.sahmk.sa))

### Setup

```bash
# Clone the repository
git clone https://github.com/YOUR_USERNAME/saudi-market-dashboard.git
cd saudi-market-dashboard

# Create virtual environment
python -m venv venv
source venv/Scripts/activate  # Windows
# source venv/bin/activate    # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Add your API key
echo 'SAHMK_API_KEY="your_api_key_here"' > .env

# Run live market dashboard
streamlit run app.py

# Run fundamental analysis dashboard
streamlit run app_fundamental.py --server.port 8502
```

## Project Structure

```
saudi-market-dashboard/
├── app.py                      # Live market dashboard
├── app_fundamental.py          # Fundamental analysis dashboard
├── analysis.ipynb           # Jupyter notebook 
├── data/
│   ├── saudi_stocks_fundamentals.csv   # 223 stocks, 18 columns
│   └── saudi_stocks_enriched.csv       # Enriched with live prices
├── requirements.txt
├── .env                        # API key (not committed)
├── .streamlit/
│   └── config.toml             # Streamlit theme
├── venv/                       # Python virtual environment
├── .gitignore
└── README.md
```

## API Endpoints Used

| Endpoint | Purpose |
|----------|---------|
| `GET /market/summary/` | TASI index, mood, breadth |
| `GET /market/gainers/` | Top gaining stocks |
| `GET /market/losers/` | Top losing stocks |
| `GET /market/volume/` | Volume leaders |
| `GET /market/value/` | Value leaders |
| `GET /market/sectors/` | Sector performance |
| `GET /quote/{symbol}/` | Individual stock quote |
| `GET /quotes/` | Batch stock quotes (max 50/call) |
| `GET /company/{symbol}/` | Company information |

## Key Insights

1. **Shariah Compliance** — Majority of TASI stocks are Shariah-compliant, suitable for Islamic investment portfolios
2. **Top Dividends** — REITs lead with 7%+ yields, followed by Saudi Aramco (6.8%) and Luberef
3. **Best ROE** — Jarir Marketing (62%), Bahr Al Arab (34.5%), Bupa Arabia (32.5%)
4. **Strongest Sector** — Banks lead profitability with avg ROE ~16%
5. **Liquidity Flow** — Dashboard analyzes money inflow vs outflow to identify institutional buying/selling pressure
6. **Market Mood** — Real-time sentiment indicator from bullish to bearish

## Deployment

Deploy on [Streamlit Community Cloud](https://streamlit.io/cloud):

1. Push the repository to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub repo
4. Add `SAHMK_API_KEY` in Streamlit secrets
5. Deploy

## Author

**Reema** — Data Analyst | Tarmeez Capital Assessment

## License

This project is built for assessment purposes.
