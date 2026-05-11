import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots

# 頁面基本設定
st.set_page_config(page_title="五星共振量化系統", layout="wide")
st.title("🌟 五星共振量化選股系統")

# --- 修改處：將輸入框移出側邊欄，直接放在主畫面最上方 ---
symbol = st.text_input("🔍 請輸入股票代碼 (例: 2330.TW, 2308.TW, 0050.TW)", "2330.TW")

@st.cache_data
def get_data(ticker):
    # --- 修改處：period 改為正確的 "6mo" ---
    df = yf.download(ticker, period="6mo", interval="1d")
    
    # 指標手動計算邏輯
    df['MA5'] = df['Close'].rolling(window=5).mean()
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
    rs = gain / loss
    df['RSI'] = 100 - (100 / (1 + rs))
    exp1 = df['Close'].ewm(span=12, adjust=False).mean()
    exp2 = df['Close'].ewm(span=26, adjust=False).mean()
    df['DIF'] = exp1 - exp2
    df['MACD_Line'] = df['DIF'].ewm(span=9, adjust=False).mean()
    df['MACD_Hist'] = df['DIF'] - df['MACD_Line']
    return df

try:
    df = get_data(symbol)
    last = df.iloc[-1]
    prev = df.iloc[-2]
    
    score = 0
    results = []
    
    if last['Close'] > last['MA5']:
        score += 1
        results.append("✅ 股價在5日線上")
    
    if last['MACD_Hist'] > 0 and last['MACD_Hist'] > prev['MACD_Hist']:
        score += 1
        results.append("✅ MACD 紅柱增長")
    
    if 40 < last['RSI'] < 75:
        score += 1
        results.append(f"✅ RSI 分數 {last['RSI']:.1f} (強勢區)")
    
    if last['Close'] > last['Open']:
        score += 1
        results.append("✅ 當日量能收紅")
        
    if last['Volume'] > df['Volume'].tail(5).mean():
        score += 1
        results.append("✅ 量能超過5日均量")

    # 顯示評分儀表板
    st.subheader(f"📊 當前量化評分：{score} / 5")
    
    cols = st.columns(len(results))
    for i, res in enumerate(results):
        with cols[i]: st.info(res)
    
    if score >= 4:
        st.success("🔥 多頭共振確立：建議順勢操作！")
    elif score <= 1:
        st.error("⚠️ 趨勢走弱：建議觀望或停損。")

    # 繪製專業 K 線圖
    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, 
                        vertical_spacing=0.05, row_heights=[0.7, 0.3])
    
    fig.add_trace(go.Candlestick(x=df.index, open=df['Open'], high=df['High'], 
                                 low=df['Low'], close=df['Close'], name='K線'), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA5'], line=dict(color='orange'), name='5日線'), row=1, col=1)
    fig.add_trace(go.Bar(x=df.index, y=df['MACD_Hist'], name='MACD'), row=2, col=1)
    
    fig.update_layout(height=600, template='plotly_dark', xaxis_rangeslider_visible=False)
    st.plotly_chart(fig, use_container_width=True)

except Exception as e:
    st.error(f"⚠️ 無法讀取資料。請檢查代碼格式是否正確。")
    st.info("提示：台灣股票請務必加上 .TW 或 .TWO (例: 2330.TW)")
