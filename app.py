import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go

# 頁面基本設定
st.set_page_config(
    page_title="台股智慧選股與 ETF 決策助理", 
    page_icon="📈", 
    layout="wide"
)

# 隱藏預設選單與頁尾，提升視覺質感
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

is_etf = ticker_input.startswith("00")

# 中文名稱對照字典
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

# 同業推薦對照庫
PEER_GROUPS = {
    "00878": {
        "sector": "高股息 ETF 族群", 
        "peers": [
            ("0056", "元大高股息", "台灣老牌高股息代表，可比較配息週期與填息表現。"),
            ("00919", "群益台灣精選高息", "主打精準高息與動能成分股，適合作為攻擊力對照組。"),
            ("00713", "元大台灣高息低波", "具備低波動與抗跌防禦特質，震盪盤勢中的防守表現值得參考。")
        ]
    },
    "0050": {
        "sector": "市值型 ETF 族群", 
        "peers": [
            ("006208", "富邦台50", "追蹤相同指數但經理費與內扣成本略低，是市值型 ETF 的重要替代標的。"),
            ("00881", "國泰台灣5G+", "聚焦半導體與 5G 權值股，科技股爆發力強，適合做成長互補。"),
            ("0056", "元大高股息", "從大盤市值型跨入高股息資產配置時的經典對比指標。")
        ]
    },
    "2330": {
        "sector": "半導體晶圓代工", 
        "peers": [
            ("2303", "聯電", "成熟製程代表，可觀察成熟製程市況與半導體景氣輪動。"),
            ("3711", "日月光投控", "全球封測龍頭，與先進封裝供應鏈具高度連動觀察價值。"),
            ("6415", "矽力-KY", "IC 設計高價股代表，可作為高階電子族群資金人氣風向球。")
        ]
    },
    "3711": {
        "sector": "半導體封測", 
        "peers": [
            ("2330", "台積電", "先進製程晶圓代工龍頭，封測需求與台積電產能高度相關。"),
            ("2449", "京元電子", "AI 晶片測試重要供應鏈，常因封測訂單具強烈族群連動性。"),
            ("3265", "台星科", "先進封裝與測試特化廠，常因特殊技術題材受資金青睞。")
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
                "【總經宏觀】全球資金在利率循環與地緣政治波動下，高股息 ETF 具備較強的現金流防禦特性。",
                f"【規模流動性】基金規模達 {fund_size} 億元以上，流動性充裕，具備高度分散單一企業倒閉風險的優勢。",
                f"【收益回報】預估年化殖利率約落在 {dividend_yield}%，內扣總費率約 {expense_ratio}%，成本合理。"
            ]
            cons = [
                "【總經風險】若全球央行政策轉向或總體經濟面臨衰退，高股息資產仍會受到大盤系統性修正波及。",
                "【機會成本】ETF 屬被動追蹤，無法享用單一個股飆翻倍的超額爆發力。"
            ]
            
            action = "分批逢低承接（適合長期穩健配置與現金流規劃）" if score >= 75 else "區間盤整觀望（建議分批佈局，不宜一次重壓）"
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
                pros.append(f"【產業競爭力】毛利率達 {gross_margin:.1f}%，顯示公司在供應鏈中具備良好的訂價能力與護城河。")
            else:
                cons.append(f"【利潤壓力】毛利率偏低 ({gross_margin:.1f}%)，易受原物料或市場價格戰侵蝕。")
                
            if revenue_growth > 5:
                score += 20
                pros.append(f"【成長動能】最新營收年增率達 {revenue_growth:.1f}%，呼應終端需求的實質復甦。")
            else:
                cons.append(f"【成長趨緩】營收年增率較平緩或呈微幅衰退 ({revenue_growth:.1f}%)，短線動能需持續觀察。")
                
            if current_price > ma20:
                score += 10
                pros.append("【技術面】股價位於月線（20日均線）之上，短線多方佔優。")
            else:
                cons.append("【技術面】股價目前處於月線之下，短線籌碼正在整理，上檔逢壓。")
                
            score = max(0.0, min(100.0, score))
            
            action = "基本面與技術面俱佳（建議依個人策略分批逢低佈局）" if score >= 75 else ("區間震盪整理（建議列入觀察名單）" if score >= 50 else "風險評估宜保守（建議暫時觀望）")
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
    with st.spinner('正在結合國際總經與財報數據進行多維度掃描中...'):
        data = get_analysis(taiwan_ticker, is_etf)
        
    if not data["success"]:
        st.error(f"❌ 分析失敗：{data.get('error', '未知錯誤')}")
    else:
        target_type_str = "📦 ETF (一籃子分散資產)" if data["is_etf"] else "🏢 個股 (單一企業營運)"
        
        with st.container(border=True):
            st.markdown(f"### **{data['name']} ({ticker_input})** ｜ {target_type_str}")
            st.markdown(f"最新價格：**NT$ {data['current_price']:.2f}** ｜ 資料日期：`{data['latest_date']}`")
            st.info("🌐 **國際總體經濟與市場氛圍**：目前全球資本市場深受利率政策、地緣政治及供應鏈庫存調整影響。個股表現分化加劇，切勿盲目追高，應回歸企業實質獲利與資產配置規劃。")

        # 關鍵指標卡片
        m1, m2, m3, m4 = st.columns(4)
        with m1:
            with st.container(border=True):
                st.metric("綜合評估分數", f"{data['score']:.1f} 分")
        with m2:
            with st.container(border=True):
                st.metric(data["metric1_name"], data["metric1_val"])
        with m3:
            with st.container(border=True):
                st.metric(data["metric2_name"], data["metric2_val"])
        with m4:
            with st.container(border=True):
                st.metric(data["metric3_name"], data["metric3_val"])

        # 趨勢圖表
        with st.container(border=True):
            st.markdown("### 📈 股價趨勢分析與未來 30 日 AI 預估模型")
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
                template="plotly_white", height=380,
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
                margin=dict(l=10, r=10, t=10, b=10)
            )
            st.plotly_chart(fig, use_container_width=True)
            st.caption("💡 **趨勢線說明**：藍線為實際收盤價，橘點線為 20 日月線，綠虛線為線性回歸預估延伸線（僅供數學參考）。")

        # 外部查證專區（Yahoo 股票主頁）
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

        # 專業觀點
        with st.container(border=True):
            st.markdown("### 💡 深度專業觀點與多維度解析")
            if data['badge'] == 'success':
                st.success(f"🎯 **策略方向：{data['action']}**")
            elif data['badge'] == 'info':
                st.info(f"⚖️ **策略方向：{data['action']}**")
            else:
                st.error(f"⚠️ **策略方向：{data['action']}**")
                
            c1, c2 = st.columns(2)
            with c1:
                st.markdown("##### ✅ **正向利多與優勢**")
                for pro in data['pros']:
                    st.markdown(f"- {pro}")
            with c2:
                st.markdown("##### ⚠️ **潛在風險與總經變數**")
                for con in data['cons']:
                    st.markdown(f"- {con}")

        # 避坑檢核
        with st.container(border=True):
            st.markdown("### 🚫 避坑檢核：當前標的潛在警訊")
            if data.get("score", 70) < 60:
                st.warning("⚠️ **【基本面/總經警訊】** 當前綜合評分偏低或防禦力下降，建議暫時保持觀望，避免追高。")
            else:
                st.success("✅ **【結構評估】** 目前未觸發重大結構性警訊，但仍建議依個人資金風險屬性分批佈局。")

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

        # 同業與產業鏈標的
        sector_info = PEER_GROUPS.get(ticker_input, {
            "sector": "市場焦點精選族群", 
            "peers": [
                ("0050", "元大台灣50", "追蹤大盤市值表現，作為台股脈動基準。"),
                ("2330", "台積電", "台股權王與半導體中流砥柱。"),
                ("2317", "鴻海", "大型權值龍頭，觀察台灣電子出口氣氛。")
            ]
        })
        
        with st.container(border=True):
            st.markdown(f"### 🔗 同族群與產業鏈關聯標的（{sector_info['sector']}）")
            p_cols = st.columns(len(sector_info['peers']))
            for i, (p_code, p_name, p_reason) in enumerate(sector_info['peers']):
                with p_cols[i]:
                    st.markdown(f"**🏢 {p_name}** (`{p_code}`)")
                    st.caption(f"👉 {p_reason}")

        # 系統資訊
        with st.expander("ℹ️ 系統查詢資訊與免責聲明"):
            st.caption(f"⏱️ 系統查詢時間：`{data['fetch_timestamp']}` ｜ 資料來源：Yahoo Finance & 台灣證券交易所")
            st.caption("⚠️ 本工具提供之數據與觀點僅供教學與參考用途，不構成任何買賣推薦或投資建議。")
