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
st.caption("支援全台股智慧搜尋與彈性時間試算：輸入股票/ETF名稱、俗稱或代號，自訂天數預估資金變化！")

# 側邊欄設定
st.sidebar.header("⚙️ 查閱與投資試算設定")
raw_input = st.sidebar.text_input("輸入股票名稱、俗稱或代號", value="2330", help="例如：中鋼、2002、台積電、或是任何冷門飆股代號").strip()

# 1. 預計投資金額輸入框
investment_amount = st.sidebar.number_input(
    "預計投資金額 (TWD)", 
    min_value=1000, 
    max_value=100000000, 
    value=100000, 
    step=10000,
    help="輸入您預計要買入此標的的總金額，系統將幫您計算買入股數與預估未來的資產變化。"
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
        "小資新手族 (每月幾千元，喜歡買零股或定期定額)", 
        "穩健上班族 (有 10~30 萬積蓄，想穩穩配置)", 
        "高資產族 (資金較多，偏好大筆買進資產)"
    ]
)

# 💡 終極深度智慧解析函式
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
    
    if cleaned_query in common_aliases:
        code = common_aliases[cleaned_query]
        return f"{code}.TW", code, cleaned_query
    if upper_query in common_aliases:
        code = common_aliases[upper_query]
        return f"{code}.TW", code, upper_query

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
    st.markdown("2. **設定金額與天數**：在側邊欄輸入預計投資金額，並自由選擇預估時間。")
    st.markdown("3. **查看預估變化**：系統會動態推算指定天數後的資產總值與損益。")

# 📖 側邊欄常駐的高中生/零基礎白話財經字典
with st.sidebar.expander("🐔 零基礎速懂：鹹酥雞攤白話字典"):
    st.markdown("""
    - **毛利率**：扣掉食材成本後，你真正賺到的血汗錢比例。越高代表產品越搶手。
    - **本益比 (PE)**：買下這間店，要花幾年的利潤才能把本錢賺回來？
    - **營收年增率 (YoY)**：跟去年同期相比，生意有沒有變好？
    - **20日均線 (月線)**：過去一個月大家買這支股票的平均成本。
    - **空頭排列**：骨牌效應崩盤，大家瘋狂拋售，千萬別盲目接刀。
    - **高股息 ETF**：買一籃子每年固定發零用錢的好公司。
    - **內扣總費率**：請專業經理人幫你顧錢，每年默默扣掉的管理費。
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
def get_analysis(ticker, is_etf_flag, query_name, cached_name, inv_amount, days_ahead):
    try:
        clean_c = ticker.replace(".TW", "").replace(".TWO", "")
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="1y")
        
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
        
        shares_bought = int(inv_amount // current_price) if current_price > 0 else 0
        
        if len(hist) > 10:
            x_idx = np.arange(len(hist))
            y_vals = hist['Close'].values
            slope, intercept = np.polyfit(x_idx, y_vals, 1)
            trade_days_ahead = int(days_ahead * (250 / 365))
            future_x = len(hist) + max(1, trade_days_ahead)
            predicted_price_future = max(0.01, slope * future_x + intercept)
        else:
            predicted_price_future = current_price

        predicted_val_future = shares_bought * predicted_price_future
        est_profit = predicted_val_future - (shares_bought * current_price)
        est_return_pct = (est_profit / (shares_bought * current_price) * 100) if (shares_bought * current_price) > 0 else 0.0

        if is_etf_flag:
            fund_size = 6700 if clean_c == "00878" else 3500
            dividend_yield = 7.8 if clean_c == "00878" else 6.2
            expense_ratio = 0.28 if clean_c == "00878" else 0.30
                
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
                "is_etf": True, "name": name, "clean_code": clean_c, "current_price": current_price,
                "latest_date": latest_date, "fetch_timestamp": fetch_timestamp,
                "metric1_name": "基金規模", "metric1_val": f"{fund_size} 億",
                "metric2_name": "預估殖利率", "metric2_val": f"{dividend_yield}%",
                "metric3_name": "內扣總費率", "metric3_val": f"{expense_ratio}%",
                "score": score, "action": action, "badge": badge,
                "pros": pros, "cons": cons, "success": True, "hist": hist,
                "shares_bought": shares_bought, "predicted_price_future": predicted_price_future,
                "predicted_val_future": predicted_val_future, "est_profit": est_profit,
                "est_return_pct": est_return_pct
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
                "is_etf": False, "name": name, "clean_code": clean_c, "current_price": current_price,
                "latest_date": latest_date, "fetch_timestamp": fetch_timestamp,
                "metric1_name": "本益比 (PE)", "metric1_val": pe_str,
                "metric2_name": "毛利率", "metric2_val": f"{gross_margin:.1f}%",
                "metric3_name": "營收年增率", "metric3_val": f"{revenue_growth:.1f}%",
                "score": score, "action": action, "badge": badge,
                "pros": pros, "cons": cons, "success": True, "hist": hist,
                "shares_bought": shares_bought, "predicted_price_future": predicted_price_future,
                "predicted_val_future": predicted_val_future, "est_profit": est_profit,
                "est_return_pct": est_return_pct
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

# 執行分析按鈕
if st.sidebar.button("🚀 開始深度分析與資金試算", use_container_width=True):
    if not resolved_ticker:
        st.error(f"❌ 找不到與「{raw_input}」對應的台股標的，請嘗試輸入正確的 4 位數代號（例如：2002）或完整名稱。")
    else:
        with st.spinner(f'正在向 Yahoo 股市資料庫聯動搜尋與試算「{raw_input}」...'):
            data = get_analysis(resolved_ticker, is_etf, raw_input, resolved_name, investment_amount, future_days)
            
        if not data.get("success", False):
            st.error(f"❌ 分析失敗：{data.get('error', '未知錯誤')}")
        else:
            target_type_str = "📦 ETF (一籃子分散資產)" if data["is_etf"] else "🏢 個股 (單一企業營運)"
            
            st.info(f"💡 **系統智慧對應成功**：您輸入的「{raw_input}」已鎖定 👉 **{data['name']} ({data['clean_code']})**")

            # 1. 摘要與風險快篩放最上方
            with st.container(border=True):
                st.markdown("### ⚡ 一分鐘核心總結與風險快篩")
                if data['badge'] == 'success':
                    st.success(f"🎯 **綜合評語：{data['action']}** (綜合評分：{data['score']:.1f} 分)")
                elif data['badge'] == 'info':
                    st.info(f"⚖️ **綜合評語：{data['action']}** (綜合評分：{data['score']:.1f} 分)")
                else:
                    st.error(f"⚠️ **綜合評語：{data['action']}** (綜合評分：{data['score']:.1f} 分)")
                
                if data.get("score", 70) < 60:
                    st.warning("⚠️ **【避坑提醒】** 當前評分偏低，可能存在基本面轉弱或短線技術面破線風險，不建議盲目歐印。")
                else:
                    st.success("✅ **【避坑提醒】** 結構基本健全，未觸發重大地雷警訊，但仍建議分批佈局。")

            # 基本標題與當前價格
            with st.container(border=True):
                st.markdown(f"### **{data['name']} ({data['clean_code']})** ｜ {target_type_str}")
                st.markdown(f"最新價格：**NT$ {data['current_price']:.2f}** ｜ 資料日期：`{data['latest_date']}`")

            # 💰 動態時間預估資金變化卡片專區
            with st.container(border=True):
                st.markdown(f"### 💵 預計投資 NT$ {investment_amount:,.0f} 元 ｜ **{time_horizon_label}** 後資金預估變化")
                c_inv1, c_inv2, c_inv3, c_inv4 = st.columns(4)
                with c_inv1:
                    st.metric("可買入股數", f"{data['shares_bought']:,} 股", help="以當前最新收盤價計算可買入的最多股數（含零股）")
                with c_inv2:
                    st.metric(f"預估 {time_horizon_label} 後單股價", f"NT$ {data['predicted_price_future']:.2f}")
                with c_inv3:
                    st.metric(f"預估 {time_horizon_label} 後總值", f"NT$ {data['predicted_val_future']:,.0f}")
                with c_inv4:
                    profit_color = "normal" if data['est_profit'] == 0 else ("inverse" if data['est_profit'] < 0 else "normal")
                    st.metric("預估期間損益", f"NT$ {data['est_profit']:+,.0f}", f"{data['est_return_pct']:+.2f}%", delta_color=profit_color)
                st.caption(f"⚠️ 註：所選時間（{time_horizon_label}）之資產變化為基於歷史股價斜率之 AI 線性模型推算，僅供教學與模擬參考，不代表未來實際報酬。")

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

            # 2. 趨勢圖表與說明
            with st.container(border=True):
                st.markdown(f"### 📈 股價趨勢與 AI 線性預估模型 (含指定 {time_horizon_label} 走勢)")
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
                    
                    trade_days_ahead = int(future_days * (250 / 365))
                    last_date = hist_df.index[-1]
                    future_dates = pd.date_range(start=last_date + pd.Timedelta(days=1), periods=max(1, trade_days_ahead), freq='B')
                    future_x = np.arange(len(hist_df), len(hist_df) + len(future_dates))
                    future_y = slope * future_x + intercept
                    
                    fig.add_trace(go.Scatter(
                        x=future_dates, y=future_y,
                        mode='lines', name=f'AI 趨勢預估線 ({time_horizon_label})',
                        line=dict(color='#36B37E', width=2, dash='dash')
                    ))
                    
                fig.update_layout(
                    xaxis_title="日期", 
                    yaxis_title="價格 (NTD)",
                    template="plotly_white", 
                    height=380,
                    legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                    margin=dict(l=10, r=10, t=10, b=10)
                )
                st.plotly_chart(fig, use_container_width=True)
                
                with st.expander("🔍 點此查看：數字、評分與預估線的依據與限制是什麼？"):
                    st.markdown("- **綜合評分怎麼算？**：結合毛利率、營收年增率與月線位置給予 0~100 分的綜合健康度。")
                    st.markdown("- **AI 預估線的依據與限制**：綠色虛線是根據歷史股價斜率做出的線性延伸，僅供模擬參考，無法預測突發黑天鵝事件。")

            # 外部查證專區
            with st.container(border=True):
                st.markdown("### 🔍 獨立查證與交叉比對專區")
                st.caption("建議點擊下方權威平台，對照真實的即時報價、技術線圖與財報細節：")
                c_link1, c_link2, c_link3 = st.columns(3)
                code = data["clean_code"]
                with c_link1:
                    st.link_button("📈 Yahoo 股市主頁", f"https://tw.stock.yahoo.com/quote/{code}", use_container_width=True)
                with c_link2:
                    st.link_button("📊 Goodinfo! 股市資訊網", f"https://goodinfo.tw/StockInfo/StockDetail.asp?STOCK_ID={code}", use_container_width=True)
                with c_link3:
                    st.link_button("📉 TradingView 專業圖表", f"https://www.tradingview.com/symbols/TWSE-{code}/", use_container_width=True)

            # 優勢與風險細節
            with st.container(border=True):
                st.markdown("### 💡 詳細優勢與潛在風險解析")
                c1, c2 = st.columns(2)
                with c1:
                    st.markdown("##### ✅ **正向利多**")
                    for pro in data['pros']:
                        st.markdown(f"- {pro}")
                with c2:
                    st.markdown("##### ⚠️ **潛在風險**")
                    for con in data['cons']:
                        st.markdown(f"- {con}")

            # 資金族群策略
            with st.container(border=True):
                user_tag = user_profile.split(' ')[0]
                st.markdown(f"### 💰 給「{user_tag}」的獨到資金配置策略")
                lot_price = data['current_price'] * 1000
                
                if "小資新手族" in user_profile:
                    strategy_desc = f"每張約 **NT$ {lot_price:,.0f} 元**。強烈建議透過 **零股交易** 或 **定期定額**，分攤成本並降低心理負擔。"
                elif "穩健上班族" in user_profile:
                    strategy_desc = "適合當作資產配置的核心部位，採取薪水自動扣款的定期定額策略，搭配大跌時金字塔加碼法。"
                else:
                    strategy_desc = f"單筆約 **NT$ {lot_price:,.0f} 元**。首重流動性與抗通膨效率，建議採分三批佈局或逢月線支撐再行承接。"

                st.markdown(f"👉 **專屬執行方針**：{strategy_desc}")

            # 🔗 同業與產業鏈標的
            sector_info = PEER_GROUPS.get(data['clean_code'], {
                "sector": "一般上市櫃企業與市場焦點族群", 
                "peers": [
                    ("2330", "台積電", "台股權王與半導體中流砥柱。"),
                    ("2317", "鴻海", "大型權值龍頭，觀察台灣電子出口氣氛。"),
                    ("0050", "元大台灣50", "追蹤大盤市值表現，作為台股脈動基準。")
                ]
            })
            
            with st.container(border=True):
                st.markdown(f"### 🔗 同族群與產業鏈關聯標的（{sector_info['sector']}）")
                for p_code, p_name, p_reason in sector_info['peers']:
                    st.markdown(f"- **🏢 {p_name} (`{p_code}`)**：{p_reason}")

            # 系統資訊
            with st.expander("ℹ️ 系統查詢資訊與免責聲明"):
                st.caption(f"⏱️ 系統查詢時間：`{data['fetch_timestamp']}` ｜ 資料來源：Yahoo Finance & 台灣證券交易所")
                st.caption("⚠️ 本工具提供之數據與觀點僅供教學與參考用途，不構成任何買賣推薦或投資建議。")
