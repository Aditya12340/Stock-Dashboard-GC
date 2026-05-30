# Stock-Dashboard-GC

A shared **Streamlit** dashboard to **log, track, and analyze group stock pitches**.  
Users can record a buy thesis and buy date, and the app will fetch the historical buy price. The dashboard then updates live (current) prices and computes total return. Users can also “close” (sell) a position by selecting an open pitch and logging a sell date—then the app fetches the historical sell price and locks in the final return.

---

## Features

- **Log a new pitch** from the sidebar:
  - Pitcher name
  - Ticker symbol (auto uppercased)
  - Buy date
  - Thesis / reasoning
  - Automatically fetches **historical buy price** using `yfinance`

- **Dashboard view**:
  - Pulls all pitches from **Supabase**
  - Computes:
    - **Current/Final Price ($)**  
      - If sold → uses `sell_price`
      - If not sold → uses live/current market data
    - **Total Return (%)** based on buy price vs current/final price
  - Displays everything in a Streamlit dataframe

- **Close / Sell a position**:
  - Shows only open positions (where `sell_price` is null)
  - User selects a position, enters sell date
  - App fetches **historical sell price** via `yfinance`
  - Updates Supabase row with `sell_date` and `sell_price`

---

## Tech Stack

- **Python**
- **Streamlit** (UI)
- **Supabase** (hosted Postgres + API)
- **yfinance** (historical & current pricing)
- **pandas** (data manipulation)

---

## Project Structure

- `app.py` — main Streamlit application
- `README.md` — project documentation

---

## Supabase Setup

### 1) Create a Supabase project
Create a project in Supabase and get:
- `SUPABASE_URL`
- `SUPABASE_KEY` (Anon public key)

### 2) Create the table

Create a table named: `stock_pitches`

Recommended columns (based on how `app.py` reads/writes data):

- `id` (int / bigint, primary key, auto-increment)
- `created_at` (timestamp, default `now()` in Supabase)
- `pitcher_name` (text)
- `ticker` (text)
- `buy_date` (date or text; app writes `YYYY-MM-DD`)
- `buy_price` (numeric)
- `thesis` (text)
- `sell_date` (date or text, nullable)
- `sell_price` (numeric, nullable)

> Note: the app orders by `created_at` descending and expects `sell_date` / `sell_price` to exist (nullable).

---

## Configuration (Streamlit Secrets)

This app reads Supabase credentials from Streamlit secrets:

- `st.secrets["SUPABASE_URL"]`
- `st.secrets["SUPABASE_KEY"]`

### Local development: `.streamlit/secrets.toml`

Create a file at `.streamlit/secrets.toml`:

```toml
SUPABASE_URL = "https://YOURPROJECT.supabase.co"
SUPABASE_KEY = "YOUR_ANON_PUBLIC_KEY"
```

---

## Install & Run Locally

### 1) Create and activate a virtual environment (optional but recommended)

```bash
python -m venv .venv
source .venv/bin/activate   # macOS/Linux
# .venv\Scripts\activate    # Windows
```

### 2) Install dependencies

```bash
pip install streamlit supabase yfinance pandas
```

### 3) Run the app

```bash
streamlit run app.py
```

---

## Notes / Behavior Details

- **Historical price lookup**:  
  The app fetches a small window (buy/sell date through ~4 days ahead) to handle weekends/market holidays, then uses the first available close.

- **Current price**:  
  For open positions, the app fetches the latest close using `yfinance` (`history(period="1d")`). If it fails, it falls back to `buy_price`.

- **Return calculation**:
  \[
  \text{Total Return (\%)} = \frac{(\text{Current or Sell Price} - \text{Buy Price})}{\text{Buy Price}} \times 100
  \]

---

## Deployment

You can deploy on **Streamlit Community Cloud**:
1. Push this repo to GitHub
2. Create a new Streamlit app pointing at `app.py`
3. Add the same `SUPABASE_URL` and `SUPABASE_KEY` in Streamlit Cloud Secrets

---

## Future Improvements (Optional Ideas)

- Add validation for ticker symbols
- Add per-user authentication
- Add charts (price over time, group performance by pitcher, etc.)
- Cache yfinance calls to reduce rate limits and speed up loading
- Add “quantity” and compute P/L in dollars, not just %
