
import streamlit as st
import yfinance as yf
import time
import requests
import threading

# --- Telegram Message Function ---
def send_telegram(bot_token, chat_id, message):
    url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
    data = {'chat_id': chat_id, 'text': message}
    requests.post(url, data=data)

# --- Signal Checking Function ---
def check_signal(symbol, bot_token, chat_id, interval):
    while st.session_state.running:
        try:
            df = yf.download(symbol, period='1d', interval='5m')
            latest = df.iloc[-1]
            close = latest['Close']
            open_price = latest['Open']
            volume = latest['Volume']

            # RSI Calculation
            delta = df['Close'].diff()
            gain = delta.where(delta > 0, 0)
            loss = -delta.where(delta < 0, 0)
            avg_gain = gain.rolling(window=14).mean()
            avg_loss = loss.rolling(window=14).mean()
            rs = avg_gain / avg_loss
            rsi = 100 - (100 / (1 + rs))
            current_rsi = rsi.iloc[-1]

            if current_rsi < 30 and close > open_price:
                signal = f"📈 BUY SIGNAL: RSI={current_rsi:.2f}, Close={close:.2f}"
                send_telegram(bot_token, chat_id, signal)
                st.session_state.log.append(signal)
            elif current_rsi > 70 and close < open_price:
                signal = f"📉 SELL SIGNAL: RSI={current_rsi:.2f}, Close={close:.2f}"
                send_telegram(bot_token, chat_id, signal)
                st.session_state.log.append(signal)
            else:
                st.session_state.log.append("No Signal")

        except Exception as e:
            error_msg = f"Error: {e}"
            send_telegram(bot_token, chat_id, error_msg)
            st.session_state.log.append(error_msg)

        time.sleep(interval)

# --- Streamlit UI ---
st.title("🤖 AI Trading Signal Bot with Telegram")

# User inputs
bot_token = st.text_input("Enter your Telegram Bot Token")
chat_id = st.text_input("Enter your Telegram Chat ID")
symbol = st.text_input("Enter symbol (e.g. ^NSEI, RELIANCE.NS)", value="^NSEI")
interval = st.slider("Check Interval (seconds)", 60, 600, step=60, value=300)

# Initialize log and running flag
if "log" not in st.session_state:
    st.session_state.log = []

if "running" not in st.session_state:
    st.session_state.running = False

# Start/Stop button logic
col1, col2 = st.columns(2)

if col1.button("▶️ Start Bot") and not st.session_state.running:
    st.session_state.running = True
    threading.Thread(target=check_signal, args=(symbol, bot_token, chat_id, interval), daemon=True).start()

if col2.button("⏹ Stop Bot"):
    st.session_state.running = False

# Log Display
st.subheader("📋 Signal Log")
for entry in st.session_state.log[-10:][::-1]:  # Show last 10 logs
    st.write(entry)
