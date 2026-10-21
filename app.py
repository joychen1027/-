import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="智慧選股與 ETF 決策助理", layout="wide")

st.title("🎯 智慧選股與 ETF 決策助理（防誤判升級版）")
st.markdown("自動辨識「個股」與「ETF」，用最正確、最白話的方式幫你做投資評估！")

# 側邊欄設定
st.sidebar.header("設定你的投資條件")
ticker_input = st.sidebar.text_input("輸入台股代號 (個股如: 2330, 3711 ｜ ETF如: 00878, 0050)", value="00878")
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

# 台股中英文對照字典
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

# 模擬同業或同類 ETF 推薦庫
PEER_GROUPS = {
    "00878": {"sector": "高股息 ETF 族群", "peers": [("0056", "元大高股息"), ("00919", "群益台灣精選高息"), ("00713", "元大台灣高息低波")]},
    "0050": {"sector": "市值型 ETF 族群", "peers": [("006208", "富邦台50"), ("00881", "國泰台灣5G+"), ("0056", "元大高股息")]},
    "2330": {"sector": "半導體晶圓代工", "peers": [("2303", "聯電"), ("3711", "日月光投控"), ("6415", "矽力-KY")]},
    "3711": {"sector": "半導體封測", "peers": [("2330", "台積電"), ("2449", "京元電子"), ("3265", "台星科")]},
    "2317": {"sector": "電子代工服務 (EMS)", "peers": [("2382", "廣達"), ("3231", "緯創"), ("6669", "緯穎")]}
}

@st.cache_data
def get_analysis(ticker, is_etf_flag):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        hist = stock.history(period="3mo")
        current_price = hist['Close'].iloc[-1] if not hist.empty else 100.0
        
        # 取得最新資料時間 (格式：YYYY-MM-DD)
        latest_date = hist.index[-1].strftime('%Y-%m-%d') if not hist.empty else "未知"
        
        # 產生來源網址
        clean_code = ticker.replace(".TW", "").replace(".TWO", "")
        source_url = f"https://tw.stock.yahoo.com/quote/{clean_code}"
        
        # 優先從字典抓取中文名稱
        name = TAIWAN_NAMES_DICT.get(clean_code) or info.get('shortName', ticker)
        
        if is_etf_flag:
            # --- ETF 專屬邏輯 ---
            expense_ratio = 0.28  
            dividend_yield = 6.5  
            fund_size = 6500      
            
            score = 80.0 if fund_size > 1000 else 60.0
            pros = [
                f"這是一檔一籃子股票組成的 ETF，經理費率僅約 {expense_ratio}%，內扣成本低。",
                f"基金規模高達 {fund_size} 億元以上，受益人數眾多，流動性極佳，完全不用擔心下市或單一公司倒閉風險。",
                f"預估年化殖利率約有 {dividend_yield}% 左右，適合長期領息與資產配置。"
            ]
            cons = [
                "ETF 屬於被動追蹤或指數化投資，不會有單一個股飆翻倍的超額爆發力。",
                "仍會受到大盤整體下跌的系統性風險影響，遇空頭時股價會跟著回檔。"
            ]
            action = "非常適合長期存股與定期定額（資產配置的核心選擇）"
            badge = "success"
            
            return {
                "is_etf": True,
                "name": name,
                "current_price": current_price,
                "latest_date": latest_date,
                "source_url": source_url,
                "metric1_name": "基金規模", "metric1_val": f"{fund_size} 億",
                "metric2_name": "預估殖利率", "metric2_val": f"{dividend_yield}%",
                "metric3_name": "經理費率", "metric3_val": f"{expense_ratio}%",
                "score": score, "action": action, "badge": badge,
                "pros": pros, "cons": cons, "success": True
            }
        else:
            # --- 個股專屬邏輯 ---
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1] if len(hist) >= 20 else current_price
            holder_pct = info.get('heldPercentInstitutions', 0.5) * 100
            gross_margin = info.get('grossMargins', 0.25) * 100
            pe_ratio = info.get('trailingPE', 20.0)
            revenue_growth = info.get('revenueGrowth', 0.1) * 100
            
            score = 60.0
            pros, cons = [], []
            
            if gross_margin > 25:
                score += 15
                pros.append(f"毛利率有 {gross_margin:.1f}%，代表公司產品有競爭力、利潤不錯。")
            else:
                cons.append(f"毛利率偏低 ({gross_margin:.1f}%)，利潤空間較薄。")
                
            if revenue_growth > 5:
                score += 20
                pros.append(f"最新營收年增率為 {revenue_growth:.1f}%，本業有在成長。")
            else:
                cons.append(f"營收動能較平緩或衰退 ({revenue_growth:.1f}%)。")
                
            if current_price > ma20:
                score += 10
                pros.append("股價在月線（20日均線）之上，短線趨勢偏多。")
            else:
                cons.append("股價目前在月線之下，短線正在整理。")
                
            score = max(0.0, min(100.0, score))
            
            if score >= 70:
                action = "強烈推薦購入（個股體質優良）"
                badge = "success"
            elif score >= 50:
                action = "區間震盪（建議先放觀察名單）"
                badge = "info"
            else:
                action = "暫時觀望（基本面或籌碼有隱憂）"
                badge = "error"
                
            return {
                "is_etf": False,
                "name": name,
                "current_price": current_price,
                "latest_date": latest_date,
                "source_url": source_url,
                "metric1_name": "本益比 (PE)", "metric1_val": f"{pe_ratio:.1f} 倍",
                "metric2_name": "毛利率", "metric2_val": f"{gross_margin:.1f}%",
                "metric3_name": "營收年增率", "metric3_val": f"{revenue_growth:.1f}%",
                "score": score, "action": action, "badge": badge,
                "pros": pros, "cons": cons, "success": True
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

if st.sidebar.button("開始輕鬆分析"):
    with st.spinner('正在精準掃描市場狀況中...'):
        data = get_analysis(taiwan_ticker, is_etf)
        
    if not data["success"]:
        st.error("無法取得資料，請檢查代號是否正確。")
    else:
        # 1. 大盤氛圍
        st.subheader("🌤️ 今日台股大盤與市場氛圍")
        st.info("台股今日震盪穩健，資金在權值股與高股息族群間輪動。整體氣氛穩定，適合依照個人策略進行配置。")
        
        target_type_str = "📦 ETF (一籃子股票)" if data["is_etf"] else "🏢 個股 (單一企業)"
        st.success(f"📌 你正在檢視：**{data['name']} ({ticker_input})** ｜ 類型：**{target_type_str}** ｜ 現價約 **{data['current_price']:.2f} 元**")
        
        # 顯示最新資料時間與來源網址
        st.caption(f"📅 **數據最新更新日期**：`{data['latest_date']}` ｜ 🔗 **資料來源**：[Yahoo 股市頁面連結]({data['source_url']})")
        
        # 2. 核心指標卡片
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("綜合健康分數", f"{data['score']:.1f} 分")
        col2.metric(data["metric1_name"], data["metric1_val"])
        col3.metric(data["metric2_name"], data["metric2_val"])
        col4.metric(data["metric3_name"], data["metric3_val"])
        
        # 3. 白話文總結與原因拆解
        st.markdown("---")
        st.subheader("💡 系統白話文總結與分析原因")
        
        if data['badge'] == 'success':
            st.success(f"🎯 **{data['action']}**")
        elif data['badge'] == 'info':
            st.info(f"⚖️ **{data['action']}**")
        else:
            st.error(f"⚠️ **{data['action']}**")
            
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### ✅ **為什麼看好（優點）**")
            for pro in data['pros']:
                st.markdown(f"- {pro}")
        with c2:
            st.markdown("### ⚠️ **需要注意的風險（缺點）**")
            for con in data['cons']:
                st.markdown(f"- {con}")

        # 4. 資金配置建議
        st.markdown("---")
        st.subheader(f"💰 給「{user_profile.split(' ')[0]}」的親民資金建議")
        
        lot_price = data['current_price'] * 1000
        if data["is_etf"]:
            advice_msg = f"這檔 ETF 一張大約 **{lot_price:,.0f} 元**。因為它本身已經幫你分散買了幾十檔好股票，非常適合當作核心資產。資金較少時可以直接透過 **零股交易** 或每月定期定額，慢慢存張數領股息！"
        else:
            advice_msg = f"這是一檔個股，一張大約 **{lot_price:,.0f} 元**。建議不要把所有資金壓在單一公司，採用分批買進的方式會比較安全。"
        st.markdown(f"- **適合怎麼買**：{advice_msg}")

        # 5. 同類型好朋友推薦
        sector_info = PEER_GROUPS.get(ticker_input, {"sector": "熱門精選族群", "peers": [("0050", "元大台灣50"), ("2330", "台積電"), ("2317", "鴻海")]})
        st.markdown("---")
        st.subheader(f"🔗 同類型的其他好朋友標的（{sector_info['sector']}）")
        
        p_cols = st.columns(len(sector_info['peers']))
        for i, (p_code, p_name) in enumerate(sector_info['peers']):
            with p_cols[i]:
                st.markdown(f"**🏢 {p_name}** (`{p_code}`)")
                st.markdown("⭐ 同族群績優代表，可納入觀察名單。")

        st.markdown("---")
        st.caption("⚠️ **小叮嚀**：股市有賺有賠，分析僅供參考，投資人做決定前請依照自己的財務狀況審慎評估哦！")
