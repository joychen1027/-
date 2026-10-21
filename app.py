import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

# 頁面基本設定 (質感標題與佈局)
st.set_page_config(
    page_title="台股智慧選股與 ETF 決策助理", 
    page_icon="📈", 
    layout="wide"
)

# 隱藏預設的主選單與頁尾 Streamlit 標記，提升視覺質感，符合上架標準
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .block-container {padding-top: 2rem; padding-bottom: 2rem;}
    </style>
""", unsafe_allow_html=True)

# 主標題區塊
st.title("🎯 台股智慧選股與 ETF 決策助理（完整旗艦版）")
st.caption("結合國際總經、產業護城河、精準族群策略、AI 趨勢預估線圖、同業觀察亮點與外部權威查證連結！")

# 側邊欄設定
st.sidebar.header("⚙️ 條件設定")
ticker_input = st.sidebar.text_input("輸入台股代號", value="00878", help="個股如: 2330, 2317 ｜ ETF如: 00878, 0050").strip().upper()
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

# 升級版同業與關聯族群推薦庫（含詳細觀察原因解析）
PEER_GROUPS = {
    "00878": {
        "sector": "高股息 ETF 族群", 
        "peers": [
            ("0056", "元大高股息", "台灣老牌高股息代表，成分股涵蓋多元，可與 00878 比較配息週期與填息表現。"),
            ("00919", "群益台灣精選高息", "主打精準高息與動能成分股，適合作為高股息 ETF 攻擊力與殖利率強弱的對照組。"),
            ("00713", "元大台灣高息低波", "具備低波動與抗跌防禦特質，在市場空頭或震盪盤勢中的防守表現值得參考。")
        ]
    },
    "0050": {
        "sector": "市值型 ETF 族群", 
        "peers": [
            ("006208", "富邦台50", "追蹤相同指數但經理費與內扣成本略低，是市值型 ETF 的重要替代與比較標的。"),
            ("00881", "國泰台灣5G+", "聚焦台廠半導體與 5G 權值股，科技股爆發力強，適合與大盤市值型做成長互補。"),
            ("0056", "元大高股息", "從純追蹤大盤的市值型跨入高股息資產配置時的經典收益型對比指標。")
        ]
    },
    "2330": {
        "sector
