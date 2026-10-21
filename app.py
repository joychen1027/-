import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

# 頁面基本設定 (預設展開邊欄、質感標題)
st.set_page_config(
    page_title="台股智慧選股與 ETF 決策助理", 
    page_icon="📈", 
    layout="wide"
)

# 隱藏預設的主選單與頁尾 Streamlit 標記，提升專業感
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    </style>
""", unsafe_allow_html=True)

# 主標題區塊
st.title("🎯 台股智慧選股與 ETF 決策助理")
st.caption("結合國際總經、產業護城河、客觀評級與 AI 趨勢模型，為你打造立體的投資決策系統。")

# 側邊欄設定
st.sidebar.header("⚙️ 條件設定")
ticker_input = st.sidebar.text_input("輸入台股代號", value="00878", help="個股如: 2330, 2317 ｜ ETF如: 00878, 0050").strip().upper()
taiwan_ticker = f"{ticker_input}.TW"

user_profile = st.sidebar.selectbox(
    "選擇你的資金族群", 
    [
        "小資新手族 (每月幾千元，定期定額為主)", 
        "穩健上班族 (有 10~30 萬積蓄，想穩穩配置)", 
        "高資產族 (資金充裕，注重資產防禦與效率)"
    ]
)

is_etf = ticker_input.startswith("00")

TAIWAN_NAMES_DICT = {
    "0050": "元大台灣50",
    "0056": "元大高股息",
    "00878": "國泰永續高股息",
    "00713": "元大台灣高息低波",
    "00919": "群益台灣精選高息",
    "006208": "富邦台50",
    "00881": "國泰台灣5G+",
    "2330": "台積電",
    "2317": "鴻海",
    "2454": "聯發科",
    "2308": "台達電",
    "3711": "日月光投控",
    "2303": "聯電",
    "2382": "廣達",
    "3231": "緯創",
    "6669": "緯穎",
    "2881": "富邦金",
    "2882": "國泰金",
    "2891": "中信金"
}

PEER_GROUPS = {
    "00878": {
        "sector": "高股息 ETF 族群", 
        "peers": [
            ("0056", "元大高股息", "老牌高股息，成分股涵蓋多元，可比較配息週期與填息能力。"),
            ("00919", "群益台灣精選高息", "主打精準高息與動能成分股，適合作為攻擊力對照組。"),
            ("00713", "元大台灣高息低波", "具低波動與防禦特質，震盪盤勢中的防守表現值得參考。")
        ]
    },
    "0050": {
        "sector": "市值型 ETF 族群", 
        "peers": [
            ("006208", "富邦台50", "追蹤相同指數但總費用率較低，是市值型 ETF 的重要替代標的。"),
            ("00881", "國泰台灣5G+", "聚焦半導體與 5G 權值股，適合與大盤市值型做成長互補。"),
            ("0056", "元大高股息", "從純追蹤大盤跨入高股息配置時的經典收益型指標。")
        ]
    },
    "2330": {
        "sector": "半導體晶圓代工", 
        "peers": [
            ("2303", "聯電", "成熟製程代表，可觀察成熟製程市況與半導體景氣輪動。"),
            ("3711", "日月光投控", "全球封測龍頭，與先進封裝供應鏈具高度連動觀察價值。"),
            ("6415", "矽力-KY", "高階 IC 設計代表，可作為高階電子族群資金人氣風向球。")
        ]
    },
    "3711": {
        "sector": "半導體封測", 
        "peers": [
            ("2330", "台積電", "晶圓代工龍頭，封測需求與先進製程擴張高度相關。"),
            ("2449", "京元電子", "AI 晶片測試重要供應鏈，具強烈族群連動性。"),
            ("3265", "台星科", "先進封裝測試特化廠，常因特殊技術題材受資金青睞。")
        ]
    },
    "2317": {
        "sector": "電子代工服務 (EMS)", 
        "peers": [
            ("2382", "廣達", "AI 伺服器代工龍頭，衡量伺服器出貨動能的關鍵對照組。"),
            ("3231", "緯創", "AI PC 與伺服器指標廠，適合觀察短線資金氣氛。"),
            ("6669", "緯穎", "專注雲端資料中心伺服器，毛利率與單價顯著較高。")
        ]
    }
}

@st.cache_data
def get_analysis(ticker, is_etf_flag):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")
        
        if hist.empty:
            return {"success": False, "error": f"找不到代號 {ticker} 的歷史價格資料。"}
            
        current_price = hist['Close'].iloc[-1]
        latest_date = hist.index[-1].strftime('%Y-%m-%d')
        fetch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        clean_code = ticker.replace(".TW", "").replace(".TWO", "")
        source_url = f"https://tw.stock.yahoo.com/quote/{clean_code}"
        
        name = TAIWAN_NAMES_DICT.get(clean_code) or info.get('longName') or info.get('shortName') or f"台股代號 {clean_code}"
        
        if is_etf_flag:
            fund_size = 6700 if clean_code == "00878" else 35
