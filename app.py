import streamlit as st
from supabase import create_client, Client
import yfinance as yf
import pandas as pd
from datetime import datetime

# 1. CONNECT TO SUPABASE
# Replace these with your actual Supabase URL and Anon Key found in your Supabase Settings -> API
SUPABASE_URL = st.secrets["SUPABASE_URL"]
SUPABASE_KEY = st.secrets["SUPABASE_KEY"]

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

st.set_page_config(page_title="Group Stock Pitch Tracker", layout="wide")
st.title("📈 Group Stock Pitch Tracker")
st.write("A shared dashboard to log, track, and analyze our investment theses.")

# Helper function to get historical price for a given date
def get_historical_price(ticker, date_obj):
    try:
        stock = yf.Ticker(ticker)
        # Fetch data for a 4-day window around the date to handle weekends/holidays
        start_date = date_obj.strftime('%Y-%m-%d')
        end_date = (pd.to_datetime(date_obj) + pd.Timedelta(days=4)).strftime('%Y-%m-%d')
        hist = stock.history(start=start_date, end=end_date)
        if not hist.empty:
            return round(hist['Close'].iloc[0], 2)
        return None
    except Exception:
        return None

# Helper function to get live/current price
def get_current_price(ticker):
    try:
        stock = yf.Ticker(ticker)
        # fast_info or history(period='1d') to get current close
        hist = stock.history(period="1d")
        if not hist.empty:
            return round(hist['Close'].iloc[-1], 2)
        return None
    except Exception:
        return None

# --- SIDEBAR: LOG A NEW PITCH ---
st.sidebar.header("🚀 Log a New Pitch")
with st.sidebar.form("new_pitch_form", clear_on_submit=True):
    name = st.text_input("Your Name")
    ticker = st.text_input("Stock Ticker (e.g., AAPL, NVDA)").upper().strip()
    buy_date = st.date_input("Date Bought", datetime.today())
    thesis = st.text_area("Investment Thesis / Reason why bought")
    submit_pitch = st.form_submit_button("Add Pitch to Dashboard")

    if submit_pitch and name and ticker:
        with st.spinner("Fetching historical buy price..."):
            buy_price = get_historical_price(ticker, buy_date)
            
        if buy_price:
            # Insert into Supabase
            data, count = supabase.table("stock_pitches").insert({
                "pitcher_name": name,
                "ticker": ticker,
                "buy_date": buy_date.strftime('%Y-%m-%d'),
                "buy_price": buy_price,
                "thesis": thesis
            }).execute()
            st.sidebar.success(f"Added {ticker} at ${buy_price}!")
            st.rerun()
        else:
            st.sidebar.error("Could not fetch a valid stock price for that date. Check the ticker symbol or date.")

# --- MAIN CONTENT: READ & UPDATE DATA ---
# Fetch all data from Supabase
response = supabase.table("stock_pitches").select("*").order("created_at", desc=True).execute()
pitches = response.data

if not pitches:
    st.info("No pitches logged yet. Use the sidebar to log the first one!")
else:
    # Convert database entries to a Pandas DataFrame for easy manipulation
    df = pd.DataFrame(pitches)
    
    # We need to calculate current price and total % gain dynamically
    current_prices = []
    gain_losses = []
    
    with st.spinner("Updating live market data..."):
        for index, row in df.iterrows():
            # If the stock has been sold, its "current tracking price" effectively stops at the sell price
            if pd.notna(row['sell_price']) and row['sell_price'] is not None:
                curr_p = row['sell_price']
            else:
                curr_p = get_current_price(row['ticker']) or row['buy_price']
            
            current_prices.append(curr_p)
            
            # Calculate % Gain/Loss: ((Current or Sell Price - Buy Price) / Buy Price) * 100
            gain_loss = ((curr_p - row['buy_price']) / row['buy_price']) * 100
            gain_losses.append(round(gain_loss, 2))
            
    df['Current/Final Price ($)'] = current_prices
    df['Total Return (%)'] = gain_losses

    # Clean up column names for display
    df_display = df.rename(columns={
        'pitcher_name': 'Name',
        'ticker': 'Ticker',
        'buy_date': 'Buy Date',
        'buy_price': 'Buy Price ($)',
        'thesis': 'Thesis',
        'sell_date': 'Sell Date',
        'sell_price': 'Sell Price ($)'
    })

    # Reorder columns logically
    cols = ['Name', 'Ticker', 'Buy Date', 'Buy Price ($)', 'Thesis', 'Current/Final Price ($)', 'Sell Date', 'Sell Price ($)', 'Total Return (%)']
    st.dataframe(df_display[cols], use_container_width=True)

    # --- UPDATE ACTION: ALLOW USERS TO LOG A SELL ---
    st.write("---")
    st.subheader("🏁 Log a Close/Sell Position")
    
    # Filter open positions (where sell_price is null)
    open_positions = df[df['sell_price'].isna()]
    
    if open_positions.empty:
        st.write("No active open positions to close.")
    else:
        # Create a dropdown selection text label
        open_positions['select_label'] = open_positions['pitcher_name'] + " | " + open_positions['ticker'] + " (Bought: " + open_positions['buy_date'] + ")"
        
        selected_position = st.selectbox("Select a position to close:", open_positions['select_label'].tolist())
        
        # Get the corresponding database ID of the selected row
        selected_id = open_positions[open_positions['select_label'] == selected_position]['id'].values[0]
        selected_ticker = open_positions[open_positions['select_label'] == selected_position]['ticker'].values[0]
        
        col1, col2 = st.columns(2)
        with col1:
            sell_date = st.date_input("Date Sold", datetime.today())
        with col2:
            submit_sell = st.button("Confirm Sell Execution")
            
        if submit_sell:
            with st.spinner("Fetching historical sell price..."):
                sell_price = get_historical_price(selected_ticker, sell_date)
                
            if sell_price:
                # Update the row in Supabase
                supabase.table("stock_pitches").update({
                    "sell_date": sell_date.strftime('%Y-%m-%d'),
                    "sell_price": sell_price
                }).eq("id", selected_id).execute()
                
                st.success(f"Successfully closed position for {selected_ticker} at ${sell_price}!")
                st.rerun()
            else:
                st.error("Could not fetch a valid stock price for that sell date.")