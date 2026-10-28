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
    help="輸入您預計要買入此標的的總金額，系統將幫您計算買入股數與預估 30 天後的資產變化。"
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
    st.markdown("1. **輸入代號/名稱**：打「中鋼」、「2002」或「台積電」皆可搜尋。")
    st.markdown("2. **輸入試算金額**：在側邊欄輸入您預計投入的資金。")
    st.markdown("3. **查看預估變化**：系統會以 AI 線性趨勢推算 30 天後的預估資產與損益。")

# 同業與產業鏈資料庫
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
    },
    "2002": {
        "sector": "傳統產業與原物料（鋼鐵與重工業）", 
        "peers": [
            ("1301", "台塑", "台灣塑膠工業龍頭，可觀察整體傳統產業與原物料需求景氣。"),
            ("1303", "南亞", "塑膠加工與電子材料大廠，與傳統製造業景氣高度連動。"),
            ("2603", "長榮", "航運與全球貿易代表，可觀察原物料運輸與景氣循環。")
        ]
    }
}

@st.cache_data
def get_analysis(ticker, is_etf_flag, query_name, cached_name, inv_amount):
    try:
        clean_c = ticker.replace(".TW", "").replace(".TWO", "")
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")
        
        if hist.empty:
            return {"success": False, "error": f"找不到與「{query_name}」對應的台股歷史資料，請確認代號或名稱是否正確。"}
            
        current_price = float(hist['Close'].iloc[-1])
        latest_date = hist.index[-1].strftime('%Y-%m-%d')
        fetch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        raw_name = cached_name or info.get('longName') or info.get('shortName') or query_name
        if re.search(r'[a-zA-Z]{6,}', raw_name) and not any('\u4e00' <= c <= '\u9fff' for c in raw_name):
            name = f"台股企業 ({clean_c})"
        else:
            name = raw_name
        
        # 💰 資金計算與 30 天後趨勢預估
        shares_bought = int(inv_amount // current_price) if current_price > 0 else 0
        
        if len(hist) > 10:
            x_idx = np.arange(len(hist))
            y_vals = hist['Close'].values
            slope, intercept = np.polyfit(x_idx, y_vals,
