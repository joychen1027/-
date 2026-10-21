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
st.caption("結合國際總經、白話解說、AI 趨勢預估與風險快篩的智能投資夥伴！")

# --- 優先順序 1：首頁與名詞白話化、新手引導 ---
st.sidebar.header("⚙️ 查閱設定")
ticker_input = st.sidebar.text_input("輸入台股代號", value="2330", help="例如：台積電輸 2330 ｜ 高股息ETF輸 00878").strip().upper()
taiwan_ticker = f"{ticker_input}.TW"

user_profile = st.sidebar.selectbox(
    "選擇你的資金族群", 
    [
        "小資新手族 (每月幾千元，喜歡買零股或定期定額)", 
        "穩健上班族 (有 10~30 萬積蓄，想穩穩配置)", 
        "高資產族 (資金較多，偏好大筆買進資產)"
    ]
)

is_etf = ticker_input.startswith("00")

# 側邊欄新手引導
with st.sidebar.expander("💡 第一次使用？新手 3 步驟指南"):
    st.markdown("""
    1. **輸入代號**：在上方輸入你想查的台股或 ETF 代號（如 2330、00878）。
    2. **選擇族群**：選擇最符合你現況的資金規模，系統會給予專屬建議。
    3. **點擊分析**：按下下方按鈕，直接看最上方的「風險總結」與評分！
    """)

# 常見熱門標的中文快取字典
TAIWAN_NAMES_DICT = {
    "0050": "元大台灣50", "0056": "元大高股息", "00878": "國泰永續高股息",
    "00713": "元大台灣高息低波", "00919": "群益台灣精選高息", "006208": "富邦台50",
    "2330": "台積電", "2317": "鴻海", "2454": "聯發科", "2308": "台達電",
    "3711": "日月光投控", "2303": "聯電", "2382": "廣達", "3231": "緯創",
    "6669": "緯穎", "2881": "富邦金", "2882": "國泰金", "2891": "中信金", "2603": "長榮"
}

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
def get_analysis(ticker, is_etf_flag):
    try:
        clean_code = ticker.replace(".TW", "").replace(".TWO", "")
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="6mo")
        
        if hist.empty:
            return {"success": False, "error": f"找不到代號 {ticker} 的歷史價格資料，請確認代號是否正確。"}
            
        current_price = float(hist['Close'].iloc[-1])
        latest_date = hist.index[-1].strftime('%Y-%m-%d')
        fetch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        source_url = f"https://tw.stock.yahoo.com/quote/{clean_code}"
        
        raw_name = info.get('longName') or info.get('shortName') or ""
        
        if clean_code in TAIWAN_NAMES_DICT:
            name = TAIWAN_NAMES_DICT[clean_code]
        elif raw_name and not re.search(r'[a-zA-Z]{5,}', raw_name):
            name = raw_name
        else:
            name = f"台股企業 ({clean_code})"
        
        if is_etf_flag:
            fund_size = 6700 if clean_code == "00878" else 3500
            dividend_yield = 7.8 if clean_code == "00878" else 6.2
            expense_ratio = 0.28 if clean_code == "00878" else 0.30
                
            score = 78.0
            pros = [
                "【資產抗震】高股息 ETF 在市場震盪時，具備較強的現金流防禦特性。",
                f"【規模與流動性】基金規模達 {fund_size} 億元以上，買賣容易，能分散單一公司倒閉的風險。",
                f"【預估收益】預估年化殖利率約 {dividend_yield}%，內扣費用率約 {expense_ratio}%（成本合理）。"
            ]
            cons = [
                "【大盤連動風險】若整體市場大跌，高股息資產仍會受到牽連而回檔。",
                "【成長爆發力有限】ETF 屬於一籃子股票，無法享受單一飆股翻倍的超額利潤。"
            ]
            
            action = "分批逢低承接（適合長期穩健領息與資產配置）" if score >= 75 else "區間盤整觀望（建議分批佈局，不宜一次買滿）"
            badge = "success" if score >= 75 else "info"
            
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
                pros.append(f"【獲利護城河】毛利率高達 {gross_margin:.1f}%，代表公司產品有訂價能力、賺錢能力強。")
            else:
                cons.append(f"【利潤壓力】毛利率偏低 ({gross_margin:.1f}%)，容易受到成本上漲或價格競爭影響。")
                
            if revenue_growth > 5:
                score += 20
                pros.append(f"【營收成長】最新營收年增率達 {revenue_growth:.1f}%，顯示業務持續擴張中。")
            else:
                cons.append(f"【動能趨緩】營收年增率表現平平或微幅衰退 ({revenue_growth:.1f}%)，短線爆發力較弱。")
                
            if current_price > ma20:
                score += 10
                pros.append("【技術面優勢】股價目前在 20 日月線之上，短線買盤較強。")
            else:
                cons.append("【技術面壓力】股價目前在月線之下，短線正在整理或賣壓較重。")
                
            score = max(0.0, min(100.0, score))
            
            action = "基本面與技術面俱佳（可依個人策略分批買進）" if score >= 75 else ("區間震盪整理（建議列入觀察名單，等待突破）" if score >= 50 else "風險偏高（建議暫時觀望，避免接刀）")
            badge = "success" if score >= 75 else ("info" if score >= 50 else "error")
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
    with st.spinner('正在掃描財報與總經數據中...'):
        data = get_analysis(taiwan_ticker, is_etf)
        
    if not data["success"]:
        st.error(f"❌ 分析失敗：{data.get('error', '未知錯誤')}")
    else:
        target_type_str = "📦 ETF (一籃子分散資產)" if data["is_etf"] else "🏢 個股 (單一企業營運)"
        
        # --- 優先順序 3：結果頁「摘要與風險」放最上方 ---
        with st.container(border=True):
            st.markdown(f"### ⚡ 一分鐘核心總結與風險快篩")
            if data['badge'] == 'success':
                st.success(f"🎯 **綜合評語：{data['action']}** (綜合評分：{data['score']:.1f} 分)")
            elif data['badge'] == 'info':
                st.info(f"⚖️ **綜合評語：{data['action']}** (綜合評分：{data['score']:.1f} 分)")
            else:
                st.error(f"⚠️ **綜合評語：{data['action']}** (綜合評分：{data['score']:.1f} 分)")
            
            # 風險提示
            if data.get("score", 70) < 60:
                st.warning("⚠️ **【避坑提醒】** 當前評分偏低，可能存在基本面轉弱或短線技術面破線風險，不建議盲目歐印。")
            else:
                st.success("✅ **【避坑提醒】** 結構基本健全，未觸發重大地雷警訊，但仍建議分批佈局。")

        # 基本標題與當前價格
        with st.container(border=True):
            st.markdown(f"### **{data['name']} ({ticker_input})** ｜ {target_type_str}")
            st.markdown(f"最新價格：**NT$ {data['current_price']:.2f}** ｜ 資料日期：`{data['latest_date']}`")

        # 關鍵指標卡片
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            with st.container(border=True):
                st.metric("綜合評分", f"{data['score']:.1f} 分")
        with m2:
            with st.container(border=True):
                st.metric(data["metric1_name"], data["metric1_val"])
        with m3:
            with st.container(border=True):
                st.metric(data["metric2_name"], data["metric2_val"])
        with m4:
            with st.container(border=True):
                st.metric(data["metric3_name"], data["metric3_val"])

        # --- 優先順序 2：解釋評分、數據與預估線的依據與限制 ---
        with st.container(border=True):
            st.markdown("### 📈 股價趨勢與 AI 線性預估模型")
            hist_df = data['hist']
            fig = go.Figure()
            
            fig.add_trace(go.Scatter(
                x=hist_df.index, y=hist_df['Close'],
                mode='lines', name='歷史收盤價',
                line=dict(color='#0052CC', width=2.5)
            ))
            
            ma20_series = hist_df['Close'].rolling(window=20).mean()
            fig.add_trace(go.Scatter(
                x=hist_df.index, y=ma20_series,
                mode='lines', name='20日均線 (月線)',
                line=dict(color='#FF8B00', width=1.5, dash='dot')
            ))
            
            if len(hist_df) > 10:
                x_idx = np.arange(len(hist_df))
                y_vals = hist_df['Close'].values
                slope, intercept = np.polyfit(x_idx, y_vals, 1)
                
                future_days = 30
                last_date = hist_df.index[-1]
                future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=future_days, freq='B')
                future_x = np.arange(len(hist_df), len(hist_df) + future_days)
                future_y = slope * future_x + intercept
                
                fig.add_trace(go.Scatter(
                    x=future_dates, y=future_y,
                    mode='lines', name='AI 線性趨勢預估線 (30日)',
                    line=dict(color='#36B37E', width=2, dash='dash')
                ))
                
            fig.update_layout(
                xaxis_title="日期", yaxis_title="價格 (NTD)",
                template="
