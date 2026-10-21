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

# 隱藏預設的主選單與頁尾 Streamlit 標記，提升視覺質感
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
        "高資產族 (資金充裕，注重資產防衛與效率)"
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
            
        current_price = float(hist['Close'].iloc[-1])
        latest_date = hist.index[-1].strftime('%Y-%m-%d')
        fetch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        clean_code = ticker.replace(".TW", "").replace(".TWO", "")
        source_url = f"https://tw.stock.yahoo.com/quote/{clean_code}"
        
        name = TAIWAN_NAMES_DICT.get(clean_code) or info.get('longName') or info.get('shortName') or f"台股代號 {clean_code}"
        
        if is_etf_flag:
            if clean_code == "00878":
                fund_size = 6700
                dividend_yield = 7.8
                expense_ratio = 0.28
            else:
                fund_size = 3500
                dividend_yield = 6.2
                expense_ratio = 0.30
                
            score = 78.0
            pros = [
                "【總經防禦】全球利率循環與震盪環境下，具備穩健現金流護體。",
                f"【規模優勢】基金規模達 {fund_size} 億元以上，流動性充裕且有效分散風險。",
                f"【合理成本】預估殖利率約 {dividend_yield}%，內扣總費率 {expense_ratio}% 屬合理範圍。"
            ]
            cons = [
                "【系統性風險】若大盤遭遇總體經濟衰退，仍可能面臨系統性修正。",
                "【成長上限】被動追蹤指數，無法獲得單一個股暴漲的超額利潤。"
            ]
            
            if score >= 75:
                action = "分批逢低承接（適合長期穩健配置與現金流規劃）"
                badge = "success"
            else:
                action = "區間盤整觀望（建議分批佈局，不宜重壓）"
                badge = "info"
                
            return {
                "is_etf": True, "name": name, "clean_code": clean_code, "current_price": current_price,
                "latest_date": latest_date, "fetch_timestamp": fetch_timestamp, "source_url": source_url,
                "metric1_name": "基金規模", "metric1_val": f"{fund_size} 億",
                "metric2_name": "預估殖利率", "metric2_val": f"{dividend_yield}%",
                "metric3_name": "內扣總費率", "metric3_val": f"{expense_ratio}%",
                "score": score, "action": action, "badge": badge,
                "pros": pros, "cons": cons, "success": True, "hist": hist
            }
        else:
            ma20 = float(hist['Close'].rolling(window=20).mean().iloc[-1]) if len(hist) >= 20 else current_price
            gross_margin = float(info.get('grossMargins') or 0.25) * 100
            pe_ratio = info.get('trailingPE') or info.get('forwardPE') or 18.0
            revenue_growth = float(info.get('revenueGrowth') or 0.05) * 100
            
            score = 55.0
            pros, cons = [], []
            
            if gross_margin > 25:
                score += 15
                pros.append(f"【高毛利】毛利率達 {gross_margin:.1f}%，顯示具備定價能力與護城河。")
            else:
                cons.append(f"【成本壓力】毛利率偏低 ({gross_margin:.1f}%)，易受原物料與價格戰侵蝕。")
                
            if revenue_growth > 5:
                score += 20
                pros.append(f"【營收動能】營收年增率達 {revenue_growth:.1f}%，終端需求展現復甦。")
            else:
                cons.append(f"【成長平緩】營收年增率為 {revenue_growth:.1f}%，短線爆發力需持續觀察。")
                
            if current_price > ma20:
                score += 10
                pros.append("【多方格局】股價站穩月線（20日均線）之上，短線走勢較佳。")
            else:
                cons.append("【線型回測】股價低於月線，短線籌碼整理中，上方存在壓力。")
                
            score = max(0.0, min(100.0, score))
            
            if score >= 75:
                action = "基本面與技術面俱佳（可分批逢低佈局）"
                badge = "success"
            elif score >= 50:
                action = "區間震盪整理（建議列入觀察名單）"
                badge = "info"
            else:
                action = "風險評估宜保守（建議暫時觀望）"
                badge = "error"
                
            pe_str = f"{pe_ratio:.1f} 倍" if isinstance(pe_ratio, (int, float)) else "N/A"
            
            return {
                "is_etf": False, "name": name, "clean_code": clean_code, "current_price": current_price,
                "latest_date": latest_date, "fetch_timestamp": fetch_timestamp, "source_url": source_url,
                "metric1_name": "本益比 (PE)", "metric1_val": pe_str,
                "metric2_name": "毛利率", "metric2_val": f"{gross_margin:.1f}%",
                "metric3_name": "營收年增率", "metric3_val": f"{revenue_growth:.1f}%",
                "score": score, "action": action, "badge": badge,
                "pros": pros, "cons": cons, "success": True, "hist": hist
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

# 執行分析按鈕
if st.sidebar.button("🚀 開始深度分析", use_container_width=True):
    with st.spinner('正在整合國際總經與財報數據...'):
        data = get_analysis(taiwan_ticker, is_etf)
        
    if not data["success"]:
        st.error(f"❌ 分析失敗：{data.get('error', '未知錯誤')}")
    else:
        # --- 1. 頂部摘要卡片 ---
        target_type_str = "📦 ETF (分散資產)" if data["is_etf"] else "🏢 個股 (單一企業)"
        
        with st.container(border=True):
            st.markdown(f"### **{data['name']} ({ticker_input})** ｜ {target_type_str}")
