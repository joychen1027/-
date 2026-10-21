# 7. 外部專業圖表與數據交叉驗證專區
  import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

st.set_page_config(page_title="智慧選股與 ETF 決策助理（旗艦查證與趨勢解析版）", layout="wide")

st.title("🎯 智慧選股與 ETF 決策助理（旗艦總經與查證解析版）")
st.markdown("結合國際總經、產業護城河、精準族群策略、**AI 趨勢預估線圖**、**同業觀察亮點**與**外部權威查證連結**！")

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

# 升級版同業與關聯族群推薦庫（含觀察原因解析）
PEER_GROUPS = {
    "00878": {
        "sector": "高股息 ETF 族群", 
        "peers": [
            ("0056", "元大高股息", "台灣老牌高股息代表，成分股涵蓋多元，可與00878比較配息週期與填息表現。"),
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
        "sector": "半導體晶圓代工", 
        "peers": [
            ("2303", "聯電", "台灣成熟製程晶圓代工代表，可藉此觀察成熟製程市況與半導體族群的景氣輪動。"),
            ("3711", "日月光投控", "全球半導體封測龍頭，與護國神山在先進封裝供應鏈中具高度連動觀察價值。"),
            ("6415", "矽力-KY", "IC 設計高價股代表，可作為高階電子與 IC 設計族群資金人氣的風向球。")
        ]
    },
    "3711": {
        "sector": "半導體封測", 
        "peers": [
            ("2330", "台積電", "先進製程晶圓代工龍頭，封測需求與台積電產能擴張以及高階晶片出貨高度相關。"),
            ("2449", "京元電子", "AI 晶片測試重要供應鏈，常因 AI 封測訂單與產能吃緊題材而有強烈族群連動性。"),
            ("3265", "台星科", "先進封裝與測試特化廠，短線常因特殊封裝技術題材成為市場資金焦點。")
        ]
    },
    "2317": {
        "sector": "電子代工服務 (EMS)", 
        "peers": [
            ("2382", "廣達", "AI 伺服器代工雙雄之一，可作為衡量伺服器出貨動能與毛利表現的關鍵對照組。"),
            ("3231", "緯創", "AI PC 與伺服器指標廠，股價波動度與市場題材敏感度高，適合觀察短線資金氣氛。"),
            ("6669", "緯穎", "專注雲端資料中心伺服器，毛利率與單價顯著較高，是 AI 概念股中的獲利資優生。")
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
        
        # 絕對優先顯示中文名稱
        name = TAIWAN_NAMES_DICT.get(clean_code) or info.get('longName') or info.get('shortName') or f"台股代號 {clean_code}"
        
        if is
