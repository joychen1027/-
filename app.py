import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
import re

# 頁面基本設定
st.set_page_config(
    page_title="智慧選股與跨國企業決策助理", 
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

st.title("🎯 智慧選股與跨國企業決策助理")
st.caption("支援台股與美國大型企業（如 Intel、台積電）財報智慧搜尋與動態波動率資金試算！")

# 側邊欄設定
st.sidebar.header("⚙️ 查閱與投資試算設定")
raw_input = st.sidebar.text_input("輸入股票名稱或代號", value="2330", help="例如：2330（台積電）、INTC（英特爾）、AAPL（蘋果）").strip()

# 1. 預計投資金額輸入框
investment_amount = st.sidebar.number_input(
    "預計投資金額", 
    min_value=1000, 
    max_value=100000000, 
    value=100000, 
    step=10000,
    help="輸入您預計要配置此標的的總金額，系統將協助計算可買入單位與精確的預估資產變化。"
)

# 2. 預估時間跨度選單
time_horizon_label = st.sidebar.selectbox(
    "選擇預估投資時間跨度",
    [
        "30 天 (約 1 個月)", 
        "60 天 (約 2 個月)", 
        "180 天 (約半年)", 
        "365 天 (約 1 年)", 
        "730 天 (約 2 年)"
    ],
    index=0,
    help="選擇您想要推演未來資產變化的時間長度。"
)

horizon_days_map = {
    "30 天 (約 1 個月)": 30,
    "60 天 (約 2 個月)": 60,
    "180 天 (約半年)": 180,
    "365 天 (約 1 年)": 365,
    "730 天 (約 2 年)": 730
}
future_days = horizon_days_map[time_horizon_label]

user_profile = st.sidebar.selectbox(
    "選擇你的資金族群", 
    [
        "小資新手族 (每月幾千元，適合零股交易或定期定額)", 
        "穩健上班族 (有 10~30 萬積蓄，著重資產穩健配置)", 
        "高資產族 (資金較多，偏好大筆資金配置與流動性)"
    ]
)

# 💡 終極深度智慧解析函式
def resolve_ticker(user_query):
    common_aliases = {
        "GG": "2330", "護國神山": "2330",
        "郭董": "2317",
        "發哥": "2454",
        "航海王": "2603",
        "鋼鐵人": "2002",
        "英特爾": "INTC",
        "蘋果": "AAPL",
        "輝達": "NVDA",
        "微軟": "MSFT"
    }
    
    cleaned_query = user_query.strip()
    upper_query = cleaned_query.upper()
    
    if cleaned_query in common_aliases:
        code = common_aliases[cleaned_query]
        if code.isalpha():
            return code, code, cleaned_query
        return f"{code}.TW", code, cleaned_query
    if upper_query in common_aliases:
        code = common_aliases[upper_query]
        if code.isalpha():
            return code, code, upper_query
        return f"{code}.TW", code, upper_query

    if re.match(r'^[a-zA-Z]{1,5}$', cleaned_query):
        ticker_candidate = upper_query
        try:
            test_df = yf.Ticker(ticker_candidate).history(period="2d")
            if not test_df.empty:
                info = yf.Ticker(ticker_candidate).info
                c_name = info.get('longName') or info.get('shortName') or f"美國企業 ({ticker_candidate})"
                return ticker_candidate, ticker_candidate, c_name
        except Exception:
            pass

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

    try:
        search_results = yf.Search(cleaned_query, max_results=10).quotes
        for item in search_results:
            symbol = item.get('symbol', '')
            if symbol.endswith('.TW') or symbol.endswith('.TWO') or symbol.isalpha():
                clean_code = symbol.replace('.TW', '').replace('.TWO', '')
                shortname = item.get('shortname') or item.get('longname') or cleaned_query
                return symbol, clean_code, shortname
    except Exception:
        pass

    return None, None, cleaned_query

resolved_ticker, clean_code, resolved_name = resolve_ticker(raw_input)
is_etf = clean_code.startswith("00") if (clean_code and not clean_code.isalpha()) else False

# 側邊欄新手引導與財經字典
with st.sidebar.expander("💡 第一次使用？新手 3 步驟指南"):
    st.markdown("1. **輸入代號/名稱**：可輸入台股（如 2330、中鋼）或美股大企業（如 INTC 英特爾、AAPL 蘋果）。")
    st.markdown("2. **設定金額與天數**：在側邊欄輸入預計投資金額與時間跨度。")
    st.markdown("3. **查看分析結果**：系統將自動計算考量歷史波動率後的預估區間。")

with st.sidebar.expander("📖 零基礎白話財經名詞字典"):
    st.markdown("""
    - **毛利率**：扣掉原料成本後，企業真正賺到的利潤比例。越高代表產品競爭力越強。
    - **本益比 (PE)**：買下這家公司，靠目前的賺錢速度需要幾年才能回本？
    - **營收年增率 (YoY)**：跟去年同期相比，公司的業務營收有沒有成長？
    - **歷史波動率**：過去價格起伏的劇烈程度，波動大代表潛在獲利與風險也較高。
    """)

PEER_GROUPS = {
    "INTC": {
        "sector": "全球半導體與處理器大廠", 
        "peers": [
            ("2330", "台積電", "全球晶圓代工龍頭，與美系半導體廠具高度產業上下游連動關係。"),
            ("NVDA", "輝達", "AI 運算與繪圖晶片龍頭，可觀察高效能運算市場需求。"),
            ("AMD", "超微", "高效能處理器競爭對手，與英特爾在 PC 及伺服器市佔互為消長。")
        ]
    },
    "2330": {
        "sector": "半導體晶圓代工", 
        "peers": [
            ("2303", "聯電", "成熟製程代表，可觀察成熟製程市況與半導體景氣輪動。"),
            ("INTC", "英特爾", "美國老牌半導體整合元件製造大廠，可比較晶圓製造與 IDM 模式。"),
            ("2454", "聯發科", "IC 設計龍頭，可作為高階電子族群人氣風向球。")
        ]
    }
}

@st.cache_data
def get_analysis(ticker, is_etf_flag, query_name, cached_name, inv_amount, days_ahead):
    try:
        clean_c = ticker.replace(".TW", "").replace(".TWO", "")
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
        if hist.empty:
            return {"success": False, "error": f"找不到與「{query_name}」對應的歷史資料，請確認代號或名稱是否正確。"}
            
        current_price = float(hist['Close'].iloc[-1])
        latest_date = hist.index[-1].strftime('%Y-%m-%d')
        fetch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        raw_name = cached_name or info.get('longName') or info.get('shortName') or query_name
        if re.search(r'[a-zA-Z]{8,}', raw_name) and not any('\u4e00' <= c <= '\u9fff' for c in raw_name):
            name = f"企業 ({clean_c})"
        else:
            name = raw_name
        
        shares_bought = int(inv_amount // current_price) if current_price > 0 else 0
        
        # 🌟 精進的趨勢與波動率計算模型
        if len(hist) > 20:
            # 計算每日對數報酬率以精準對齊複利成長特性
            hist['Log_Return'] = np.log(hist['Close'] / hist['Close'].shift(1))
            daily_volatility = hist['Log_Return'].std() # 日波動率
            annualized_volatility = daily_volatility * np.sqrt(250) # 年化波動率
            
            # 使用對數價格線性迴歸，避免單純用價格長直線失真
            hist['Log_Close'] = np.log(hist['Close'])
            x_idx = np.arange(len(hist))
            slope, intercept = np.polyfit(x_idx, hist['Log_Close'].values, 1)
            
            trade_days_ahead = int(days_ahead * (250 / 365))
            future_x = len(hist) + max(1, trade_days_ahead)
            
            # 預期價格（基於對數趨勢推演）
            predicted_log_price = slope * future_x + intercept
            predicted_price_future = max(0.01, np.exp(predicted_log_price))
            
            # 計算基於波動率的上下界（± 1 標準差信心區間）
            vol_factor = annualized_volatility * np.sqrt(days_ahead / 365.0)
            price_upper = predicted_price_future * np.exp(vol_factor)
            price_lower = predicted_price_future * np.exp(-vol_factor)
        else:
            predicted_price_future = current_price
            price_upper = current_price
            price_lower = current_price
            annualized_volatility = 0.20

        predicted_val_future = shares_bought * predicted_price_future
        est_profit = predicted_val_future - (shares_bought * current_price)
        est_return_pct = (est_profit / (shares_bought * current_price) * 100) if (shares_bought * current_price) > 0 else 0.0

        if is_etf_flag:
            fund_size = 6700
            dividend_yield = 6.2
            expense_ratio = 0.30
            score = 78.0
            pros = [
                "【資產防禦】ETF 在市場波動時，具備相對穩定的分散配置特性。",
                f"【規模流動性】基金規模龐大，交易流動性良好，可分散單一公司風險。"
            ]
            cons = ["【大盤連動】若整體市場下行，標的仍會隨大盤回檔。"]
            action = "建議分批承接（適合長期資產配置）"
            badge = "success"
        else:
            ma20 = float(hist['Close'].rolling(window=20).mean().iloc[-1]) if len(hist) >= 20 else current_price
            gross_margin = float(info.get('grossMargins') or 0.30) * 100
            pe_ratio = info.get('trailingPE') or info.get('forwardPE') or 20.0
            revenue_growth = float(info.get('revenueGrowth') or 0.05) * 100
            
            score = 60.0
            pros, cons = [], []
            if gross_margin > 25:
                score += 15
                pros.append(f"【獲利能力】毛利率達 {gross_margin:.1f}%，顯示企業具備一定的產品定價與獲利優勢。")
            else:
                cons.append(f"【利潤壓力】毛利率偏低 ({gross_margin:.1f}%)，需留意成本波動與市場競爭。")
                
            if revenue_growth > 0:
                score += 15
                pros.append(f"【營收成長】最新營收年增率達 {revenue_growth:.1f}%，核心業務維持成長動能。")
            else:
                cons.append(f"【動能趨緩】營收年增率表現保守，短期成長面臨考驗。")
                
            if current_price > ma20:
                score += 10
                pros.append("【技術趨勢】股價位於 20 日月線之上，短線市場買盤相對穩定。")
            else:
                cons.append("【技術壓力】股價位於月線之下，短線技術面偏向整理。")
                
            score = max(0.0, min(100.0, score))
            action = "財務結構穩健（可視個人規劃分批配置）" if score >= 70 else "區間震盪整理（建議列入觀察清單，審慎評估）"
            badge = "success" if score >= 70 else "info"
            pe_str = f"{pe_ratio:.1f} 倍" if isinstance(pe_ratio, (int, float)) else "N/A"

        return {
            "is_etf": is_etf_flag, "name": name, "clean_code": clean_c, "current_price": current_price,
            "latest_date": latest_date, "fetch_timestamp": fetch_timestamp,
            "metric1_name": "本益比 (PE)" if not is_etf_flag else "基金規模", 
            "metric1_val": pe_str if not is_etf_flag else "大型配置",
            "metric2_name": "毛利率", "metric2_val": f"{gross_margin:.1f}%" if not is_etf_flag else f"{dividend_yield}%",
            "metric3_name": "年化波動率", "metric3_val": f"{annualized_volatility*100:.1f}%",
            "score": score, "action": action, "badge": badge,
            "pros": pros, "cons": cons, "success": True, "hist": hist,
            "shares_bought": shares_bought, "predicted_price_future": predicted_price_future,
            "price_upper": price_upper, "price_lower": price_lower,
            "predicted_val_future": predicted_val_future, "est_profit": est_profit,
            "est_return_pct": est_return_pct
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# 執行分析按鈕
if st.sidebar.button("🚀 開始深度分析與資金試算", use_container_width=True):
    if not resolved_ticker:
        st.error(f"❌ 找不到與「{raw_input}」對應的標的，請嘗試輸入正確代號（如 2330 或 INTC）。")
    else:
        with st.spinner(f'正在向 Yahoo 股市資料庫聯動搜尋與試算「{raw_input}」...'):
            data = get_analysis(resolved_ticker, is_etf, raw_input, resolved_name, investment_amount, future_days)
            
        if not data.get("success", False):
            st.error(f"❌ 分析失敗：{data.get('error', '未知錯誤')}")
        else:
            target_type_str = "📦 ETF (一籃子分散資產)" if data["is_etf"] else "🏢 個股 (跨國企業營運)"
            
            st.info(f"💡 **系統智慧對應成功**：您輸入的「{raw_input}」已鎖定 👉 **{data['name']} ({data['clean_code']})**")

            # 1. 核心總結
            with st.container(border=True):
                st.markdown("### ⚡ 核心總結與風險檢視")
                if data['badge'] == 'success':
                    st.success(f"🎯 **綜合評語：{data['action']}** (綜合評分：{data['score']:.1f} 分)")
                else:
                    st.info(f"⚖️ **綜合評語：{data['action']}** (綜合評分：{data['score']:.1f} 分)")

            # 基本標題與當前價格
            with st.container(border=True):
                st.markdown(f"### **{data['name']} ({data['clean_code']})** ｜ {target_type_str}")
                st.markdown(f"最新價格：**{data['current_price']:.2f}** ｜ 資料日期：`{data['latest_date']}`")

            # 💰 動態時間預估資金變化卡片專區（加入波動區間提示）
            with st.container(border=True):
                st.markdown(f"### 💵 預計投資金額 ｜ **{time_horizon_label}** 後資金預估與波動區間")
                c_inv1, c_inv2, c_inv3, c_inv4 = st.columns(4)
                with c_inv1:
                    st.metric("可買入單位數", f"{data['shares_bought']:,} 股/單位")
                with c_inv2:
                    st.metric(f"預估期末均價", f"{data['predicted_price_future']:.2f}", f"區間: {data['price_lower']:.1f} ~ {data['price_upper']:.1f}")
                with c_inv3:
                    st.metric(f"預估期末總值", f"{data['predicted_val_future']:,.0f}")
                with c_inv4:
                    profit_color = "normal" if data['est_profit'] == 0 else ("inverse" if data['est_profit'] < 0 else "normal")
                    st.metric("預估期間損益", f"{data['est_profit']:+,.0f}", f"{data['est_return_pct']:+.2f}%", delta_color=profit_color)
                st.caption(f"⚠️ 註：系統透過對數複利趨勢結合標的「歷史年化波動率」計算出機率區間，提供您評估可能的波動風險。")

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

            # 2. 趨勢圖表（帶有波動區間通道）
            with st.container(border=True):
                st.markdown(f"### 📈 股價趨勢與機率區間預估模型 ({time_horizon_label})")
                hist_df = data['hist']
                fig = go.Figure()
                
                fig.add_trace(go.Scatter(
                    x=hist_df.index, y=hist_df['Close'],
                    mode='lines', name='歷史收盤價',
                    line=dict(color='#0052CC', width=2.5)
                ))
                
                if len(hist_df) > 20:
                    trade_days_ahead = int(future_days * (250 / 365))
                    last_date = hist_df.index[-1]
                    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=max(1, trade_days_ahead), freq='B')
                    
                    # 繪製預估中心線與上下波動邊界
                    center_line = np.linspace(hist_df['Close'].iloc[-1], data['predicted_price_future'], len(future_dates))
                    upper_line = np.linspace(hist_df['Close'].iloc[-1], data['price_upper'], len(future_dates))
                    lower_line = np.linspace(hist_df['Close'].iloc[-1], data['price_lower'], len(future_dates))
                    
                    fig.add_trace(go.Scatter(
                        x=future_dates, y=upper_line,
                        mode='lines', name='潛在樂觀上界 (+1SD)',
                        line=dict(color='rgba(54, 179, 126, 0.4)', width=1, dash='dot')
                    ))
                    fig.add_trace(go.Scatter(
                        x=future_dates, y=lower_line,
                        mode='lines', name='潛在保守下界 (-1SD)',
                        line=dict(color='rgba(255, 86, 48, 0.4)', width=1, dash='dot'),
                        fill='tonexty', fillcolor='rgba(54, 179, 126, 0.08)'
                    ))
                    fig.add_trace(go.Scatter(
                        x=future_dates, y=center_line,
                        mode='lines', name=f'對數趨勢預估中線',
                        line=dict(color='#36B37E', width=2, dash='dash')
                    ))
                    
                fig.update_layout(
                    xaxis_title="日期", yaxis_title="價格",
                    template="plotly_white", height=380,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)

            # 外部查證專區
            with st.container(border=True):
                st.markdown("### 🔍 獨立查證與交叉比對專區")
                code = data["clean_code"]
                c_link1, c_link2, c_link3 = st.columns(3)
                with c_link1:
                    st.link_button("📈 Yahoo 股市主頁", f"https://finance.yahoo.com/quote/{code}", use_container_width=True)
                with c_link2:
                    st.link_button("📊 財報細節搜尋", f"https://www.google.com/search?q={code}+stock+financials", use_container_width=True)
                with c_link3:
                    st.link_button("📉 TradingView 圖表", f"https://www.tradingview.com/symbols/{code}/", use_container_width=True)

            # 優勢與風險細節
            with st.container(border=True):
                st.markdown("### 💡 詳細優勢與潛在風險解析")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### ✅ **正向參考因素**")
                    for pro in data['pros']:
                        st.markdown(f"- {pro}")
                with c2:
                    st.markdown("##### ⚠️ **潛在風險考量**")
                    for con in data['cons']:
                        st.markdown(f"- {con}")

            # 同業與產業鏈標的（包含 Intel 跨國對比）
            sector_info = PEER_GROUPS.get(data['clean_code'], {
                "sector": "全球科技與產業鏈焦點標的", 
                "peers": [
                    ("2330", "台積電", "全球晶圓代工龍頭。"),
                    ("INTC", "英特爾", "美國 IDM 與處理器大廠。"),
                    ("NVDA", "輝達", "AI 晶片與運算龍頭。")
                ]
            })
            
            with st.container(border=True):
                st.markdown(f"### 🔗 同族群與產業鏈關聯標的（{sector_info['sector']}）")
                for p_code, p_name, p_reason in sector_info['peers']:
                    st.markdown(f"- **🏢 {p_name} (`{p_code}`)**：{p_reason}")

            st.caption(f"⏱️ 系統查詢時間：`{data['fetch_timestamp']}` ｜ 資料來源：Yahoo Finance")
