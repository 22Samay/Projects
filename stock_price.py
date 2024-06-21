import yfinance as yf
import pandas as pd
import streamlit as st
from datetime import datetime
import plotly.graph_objects as go
import plotly.express as px

st.title("Advanced Stock Price Analysis App")

st.write("""
This app fetches and displays advanced stock analysis including closing price, volume, moving averages, candlestick chart, and RSI of selected stocks from the NIFTY 50.
Recommendations are provided based on SMA and RSI indicators.
""")

@st.cache_data
def get_nse_symbols():
    try:
        symbols = pd.read_html('https://en.wikipedia.org/wiki/NIFTY_50')[2]
        symbols = symbols[['Symbol']].dropna()
        symbols['Symbol'] = symbols['Symbol'] + '.NS'
        return symbols['Symbol'].tolist()
    except Exception as e:
        st.error("Failed to fetch stock symbols. Using default list.")
        return [
            'HDFCBANK.NS', 'RELIANCE.NS', 'TCS.NS', 'INFY.NS', 'WIPRO.NS',
            'ICICIBANK.NS', 'SBIN.NS', 'HINDUNILVR.NS', 'HDFC.NS', 'BHARTIARTL.NS'
        ]

@st.cache_data
def fetch_stock_data(symbol, start_date, end_date):
    try:
        data = yf.Ticker(symbol)
        data_df = data.history(start=start_date, end=end_date)
        return data_df
    except Exception as e:
        st.error(f"Failed to fetch data for {symbol}. Please try again.")
        return None
    
stock_symbols = get_nse_symbols()

selected_stock = st.selectbox("Select a stock symbol", stock_symbols)

start_date = st.date_input("Start date", datetime(2014, 6, 20))
end_date = st.date_input("End date", datetime(2024, 6, 21))

if start_date >= end_date:
    st.error("Error: End date must fall after start date.")
else:
    with st.spinner('Fetching data...'):
        data_df = fetch_stock_data(selected_stock, start_date, end_date)
    if data_df is not None and not data_df.empty:
        latest_data = data_df.iloc[-1]
        latest_close = latest_data['Close']
        st.write(f"Latest Closing Price: {latest_close:.2f}")

        highest_price = data_df['Close'].max()
        lowest_price = data_df['Close'].min()
        st.write(f" Highest Price in selected range: {highest_price:.2f}")
        st.write(f" Lowest Price in selected range: {lowest_price:.2f}")

        fig_close = px.line(data_df, x=data_df.index, y='Close', title='Closing Price')
        fig_close.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig_close)

        fig_volume = px.line(data_df, x=data_df.index, y='Volume', title='Volume')
        fig_volume.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig_volume)

        st.write(f"###### Moving Averages")
        data_df['SMA20'] = data_df['Close'].rolling(window=20).mean()
        data_df['SMA50'] = data_df['Close'].rolling(window=50).mean()
        data_df['SMA100'] = data_df['Close'].rolling(window=100).mean()
        fig_ma = px.line(data_df, x=data_df.index, y=['Close','SMA20','SMA50','SMA100'])
        fig_ma.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig_ma)

        st.write(f"###### Candlestick chart")
        fig = go.Figure(data=[go.Candlestick(x=data_df.index,
                              open=data_df['Open'],
                              high=data_df['High'],
                              low=data_df['Low'],
                              close=data_df['Close'])])
        fig.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig)

        delta = data_df['Close'].diff()
        gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
        loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
        rs = gain / loss
        data_df['RSI'] = 100 - (100 / (1 + rs))
        fig_rsi = px.line(data_df, x=data_df.index, y="RSI", title="Relative Strength Index")
        fig_rsi.update_xaxes(rangeslider_visible=True)
        st.plotly_chart(fig_rsi)

        st.write("Technical Indicators Summary")
        summary = {
            'Latest Close' : latest_close,
            'Highest Price' : highest_price,
            'Lowest Price' : lowest_price,
            'RSI' : data_df['RSI'].iloc[-1],
            'SMA20' : data_df['SMA20'].iloc[-1],
            'SMA50' : data_df['SMA50'].iloc[-1],
            'SMA100' : data_df['SMA100'].iloc[-1]
        }
        summary_df = pd.DataFrame(list(summary.items()), columns=['Indicator', 'Value'])
        st.dataframe(summary_df)

        # Recommendations based on SMA and RSI
        st.write(f"## Recommendations for {selected_stock.split(sep='.')[0]}")
        recommendation = ""
        if data_df['Close'].iloc[-1] > data_df['SMA20'].iloc[-1] > data_df['SMA50'].iloc[-1]:
            recommendation += "Potential Buy signal based on moving averages (Close > SMA20 > SMA50).\n"
        elif data_df['Close'].iloc[-1] < data_df['SMA20'].iloc[-1] < data_df['SMA50'].iloc[-1]:
            recommendation += "Potential Sell signal based on moving averages (Close < SMA20 < SMA50).\n"
        else:
            recommendation += "Hold signal based on moving averages.\n"

        if data_df['RSI'].iloc[-1] < 30:
            recommendation += "RSI indicates the stock is oversold. Potential buy opportunity.\n"
        elif data_df['RSI'].iloc[-1] > 70:
            recommendation += "RSI indicates the stock is overbought. Potential sell opportunity.\n"
        else:
            recommendation += "RSI is neutral.\n"

        st.write(recommendation)
        
    else:
        st.error("No data available for the selected stock and data range.")