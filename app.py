import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="智慧選股與 ETF 決策助理（總經與趨勢預估版）", layout="wide")

st.title("🎯 智慧選股與 ETF 決策助理（專業總經與趨勢預估版）")
st.markdown("結合國際總經、產業護城河、精準族群策略與 **AI 趨勢預估線圖**，為你提供立體的投資決策評估！")

# 側邊欄設定
st.sidebar.header("設定你的投資條件")
ticker_input = st.sidebar.text_input("輸入台股代號 (個股如: 2330, 2317 ｜ ETF如: 00878, 0050)", value="00878").strip().upper()
taiwan_ticker = f"{ticker_input}.TW"

user_profile = st.sidebar.selectbox(
    "選擇你的資金族群", 
    [
        "小資新手族 (每月幾千元，喜歡買零股或定期定額)", 
        "穩健上班族 (有 10~30 萬積蓄，想穩穩配置)", 
        "高資產族 (資金較多，偏好大筆買進資產)"
    ]
)

# 判斷是否為 ETF (台股代號通常以 00 開頭)
is_etf = ticker_input.startswith("00")

# 完整台股與 ETF 中文名稱對照字典
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

# 同業與關聯族群推薦庫
PEER_GROUPS = {
    "00878": {"sector": "高股息 ETF 族群", "peers": [("0056", "元大高股息"), ("00919", "群益台灣精選高息"), ("00713", "元大台灣高息低波")]},
