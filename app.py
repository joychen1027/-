import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
import re

# 頁面基本設定
st.set_page_config(
    page_title="台股智慧選股與 ETF 決策助理", 
    page_icon="📈", 
    layout="wide"
)

# 隱藏預設選單與頁尾
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    </style>
""", unsafe_allow_html=True)

# 主標題區塊
st.title("🎯 台股智慧選股與 ETF 決策助理")
st.caption("輸入股票或 ETF 名稱，幫你整理價格變化、投資特色與主要風險，學習看懂投資資訊。")

# 雙向對照字典（支援中文名稱直接反查代號）
STOCK_MAPPING = {
    # ETF
    "0050": "元大台灣50", "元大台灣50": "0050",
    "0056": "元大高股息", "元大高股息": "0056",
    "00878": "國泰永續高股息", "國泰永續高股息": "00878",
    "00713": "元大台灣高息低波", "元大台灣高息低波": "00713",
    "00919": "群益台灣精選高息", "群益台灣精選高息": "00919",
    "006208": "富邦台50", "富邦台50": "006208",
    # 個股
    "2330": "台積電", "台積電": "2330",
    "2317": "鴻海", "鴻海": "2317",
    "2454": "聯發科", "聯發科": "2454",
    "2308": "台達電", "台達電": "2308",
    "3711": "日月光投控", "日月光投控": "3711",
    "2303": "聯電", "聯電": "2303",
    "2382": "廣達", "廣達": "2382",
    "3231": "緯創", "緯創": "3231",
    "6669": "緯穎", "緯穎": "6669",
    "2881": "富邦金", "富邦金": "2881",
    "2882": "國泰金", "國泰金": "2882",
    "2891": "中信金", "中信金": "2891",
    "2603": "長榮", "長榮": "2603"
}

# 側邊欄設定
st.sidebar.header("⚙️ 查閱設定")
raw_input = st.sidebar.text_input("輸入台股名稱或代號", value="台積電", help="例如：可輸入「台積電」或「2330」｜ ETF可輸入「國泰永續高股息」或「00878」").strip()

clean_input = STOCK_MAPPING.get(raw_input, raw_input).upper()
taiwan_ticker = f"{clean_input}.TW"

user_profile = st.sidebar.selectbox(
    "選擇你的資金族群", 
    [
        "小資新手族 (每月幾千元，喜歡買零股或定期定額)", 
        "穩健上班族 (有 10~30 萬積蓄，想穩穩配置)", 
        "高資產族 (資金較多，偏好大筆買進資產)"
    ]
)

is_etf = clean_input.startswith("00")

# 側邊欄新手引導
with st.sidebar.expander("💡 第一次使用？新手 3 步驟指南"):
    st.markdown("""
    1. **輸入名稱或代號**：直接打「台積電」或「2330」皆可查詢。
    2. **選擇族群**：選擇最符合你現況的資金規模，系統會給予專屬建議。
    3. **點擊分析**：按下下方按鈕，直接看最上方的「風險總結」與評分！
    """)

PEER_GROUPS = {
    "00878": {
        "sector": "高股息 ETF 族群", 
        "peers": [
            ("0056", "元大高股息", "台灣老牌高股息代表，可比較配息週期與填息表現。"),
            ("00919", "群益台灣精選高息", "主打精準高息與動能成分股，適合作為攻擊力對照組。"),
            ("00713", "元大台灣高息低波", "具備低波動與抗跌防禦特質，防守表現值得參考。")
        ]
    },
    "2330": {
        "sector": "半導體晶圓代工", 
        "peers": [
            ("2303", "聯電", "成熟製程代表，可觀察成熟製程市況與半導體景氣輪動。"),
            ("3711", "日月光投控", "全球封測龍頭，與先進封裝供應鏈具高度連動觀察價值。"),
            ("2454", "聯發科", "IC 設計龍頭，可作為高階電子族群人氣風向球。")
        ]
    }
}

@st.cache_data
def get_analysis(ticker, is_etf_flag, query_name):
    try:
        clean_code = ticker.replace(".TW", "").replace(".TWO", "")
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")
        
        if hist.empty:
            return {"success": False, "error": f"找不到代號或名稱「{query_name}」的歷史價格資料，請確認輸入是否正確。"}
            
        current_price = float(hist['Close'].iloc[-1])
        latest_date = hist.index[-1].strftime('%Y-%m-%d')
        fetch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        source_url = f"https://tw.stock.yahoo.com/quote/{clean_code}"
        
        raw_name = info.get('longName') or info.get('shortName') or ""
        
        if clean_code in STOCK_MAPPING:
            name = STOCK_MAPPING[clean_code]
        elif raw_name and not re.search(r'[a-zA-Z]{5,}', raw_name):
            name = raw_name
        else:
            name = f"台股企業 ({clean_code})"
        
        if is_etf_flag:
            fund_size = 6700 if clean_code == "00878" else 3500
            dividend_yield = 7.8 if clean_code
