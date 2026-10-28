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

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    </style>
""", unsafe_allow_html=True)

st.title("🎯 台股智慧選股與 ETF 決策助理")
st.caption("支援全台股智慧搜尋與試算：輸入股票/ETF名稱、俗稱或代號，即時預估 30 天後資金變化！")

# 側邊欄設定
st.sidebar.header("⚙️ 查閱與投資試算設定")
raw_input = st.sidebar.text_input("輸入股票名稱、俗稱或代號", value="2330", help="例如：中鋼、2002、台積電、或是任何冷門飆股代號").strip()

# 新增資金計算與試算輸入框
investment_amount = st.sidebar.number_input(
    "預計投資金額 (TWD)", 
    min_value=1000, 
    max_value=100000000, 
    value=100000, 
    step=10000,
    help="輸入您預計要買入此標的總金額，系統將幫您計算買入股數與預估 30 天後的資產變化。"
)

user_profile = st.sidebar.selectbox(
    "選擇你的資金族群", 
    [
        "小資新手族 (每月幾千元，喜歡買零股或定期定額)", 
        "穩健上班族 (有 10~30 萬積蓄，想穩穩配置)", 
        "高資產族 (資金較多，偏好大筆買進資產)"
    ]
)

# 💡 終極深度智慧解析函式（強化搜尋深度與中文名稱過濾）
def resolve_ticker(user_query):
    common_aliases = {
        "GG": "2330", "護國神山": "2330",
        "郭董": "2317",
        "發哥": "2454",
        "航海王": "2603",
        "鋼鐵人": "2002"
    }
    
    cleaned_query = user_query.strip()
    upper_query = cleaned_query.upper()
    
    # 1. 檢查口語俗稱
    if cleaned_query in common_aliases:
        code = common_aliases[cleaned_query]
        return f"{code}.TW", code, cleaned_query
    if upper_query in common_aliases:
        code = common_aliases[upper_query]
        return f"{code}.TW", code, upper_query

    # 2. 如果使用者直接輸入 4-5 位數代號
    if re.match(r'^\d{4,5}$', cleaned_query):
        for suffix in ['.TW', '.TWO']:
            ticker_candidate = f"{cleaned_query}{suffix}"
            try:
                test_df = yf.Ticker(ticker_candidate).history(period="2d")
                if not test_df.empty:
                    info = yf.Ticker(ticker_candidate).info
                    c_name = info.get('chineseName') or info.get('longName') or info.get('shortName') or f"台股企業 ({cleaned_query})"
                    if re.search(r'[a-zA-Z]{6,}', c_name) and not any('\u4e00' <= c <= '\u9fff' for c in c_name):
                        c_name = f"台股企業 ({cleaned_query})"
                    return ticker_candidate, cleaned_query, c_name
            except Exception:
                continue

    # 3. 深度線上模糊搜尋
    try:
        search_results = yf.Search(cleaned_query, max_results=10).quotes
        for item in search_results:
            symbol = item.get('symbol', '')
            if symbol.endswith('.TW') or symbol.endswith('.TWO'):
                clean_code = symbol.replace('.TW', '').replace('.TWO', '')
                shortname = item.get('shortname') or item.get('longname') or cleaned_query
                
                if re.search(r'[a-zA-Z]{8,}', shortname) and not any('\u4e00' <= c <= '\u9fff' for c in shortname):
                    shortname = f"台股企業 ({clean_code})"
                    
                return symbol, clean_code, shortname
    except Exception:
        pass

    return None, None, cleaned_query

resolved_ticker, clean_code, resolved_name = resolve_ticker(raw_input)
is_etf = clean_code.startswith("00") if clean_code else False

# 側邊欄新手引導
with st.sidebar.expander("💡 第一次使用？新手 3 步驟指南"):
    st.markdown("1. **輸入
