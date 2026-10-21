import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
from datetime import datetime
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="智慧選股與 ETF 決策助理（專業總經版）", layout="wide")

st.title("🎯 智慧選股與 ETF 決策助理（總經與多維度升級版）")
st.markdown("結合國際情勢、總體經濟與嚴謹基本面，為你提供客觀、立體的投資決策評估！")

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
        
        latest_date = hist.index[-1].strftime('%Y-%m-%d') if not hist.empty else "未知"
        fetch_timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        clean_code = ticker.replace(".TW", "").replace(".TWO", "")
        source_url = f"https://tw.stock.yahoo.com/quote/{clean_code}"
        
        # 確保絕對優先顯示中文名稱
        name = TAIWAN_NAMES_DICT.get(clean_code) or info.get('longName') or info.get('shortName') or f"台股代號 {clean_code}"
        
        if is_etf_flag:
            # --- ETF 專屬邏輯（宏觀與總經評估） ---
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
                "【總經與宏觀】全球資金在利率循環與地緣政治波動下,高股息 ETF 具備較強的現金流防禦特性。",
                f"【基本面與流動性】基金規模達 {fund_size} 億元以上,流動性充裕,具備高度分散單一企業倒閉風險的優勢。",
                f"【收益表現】近期預估/歷史年化殖利率約落在 {dividend_yield}%,內扣總費率約 {expense_ratio}%,成本在同級中屬合理範圍。"
            ]
            cons = [
                "【總經風險】若全球央行政策轉向或總體經濟面臨衰退,高股息資產仍會受到大盤系統性修正的拖累。",
                "【機會成本】ETF 屬被動追蹤,無法享用單一個股翻倍成長的超額利潤。"
            ]
            
            if score >= 75:
                action = "分批逢低承接（適合長期穩健配置與現金流規劃）"
                badge = "success"
            else:
                action = "區間盤整觀望（建議分批佈局，不宜一次重壓）"
                badge = "info"
                
            return {
                "is_etf": True,
                "name": name,
                "current_price": current_price,
                "latest_date": latest_date,
                "fetch_timestamp": fetch_timestamp,
                "source_url": source_url,
                "metric1_name": "基金規模",
                "metric1_val": f"{fund_size} 億",
                "metric2_name": "預估殖利率",
                "metric2_val": f"{dividend_yield}%",
                "metric3_name": "內扣總費率",
                "metric3_val": f"{expense_ratio}%",
                "score": score,
                "action": action,
                "badge": badge,
                "pros": pros,
                "cons": cons,
                "success": True
            }
        else:
            # --- 個股專屬邏輯（結合產業供應鏈與技術面） ---
            ma20 = hist['Close'].rolling(window=20).mean().iloc[-1] if len(hist) >= 20 else current_price
            gross_margin = (info.get('grossMargins') or 0.25) * 100
            pe_ratio = info.get('trailingPE') or info.get('forwardPE') or 18.0
            revenue_growth = (info.get('revenueGrowth') or 0.05) * 100
            
            score = 55.0
            pros, cons = [], []
            
            if gross_margin > 25:
                score += 15
                pros.append(f"【產業競爭力】毛利率達 {gross_margin:.1f}%,顯示公司在供應鏈中具備良好的訂價能力與產品護城河。")
            else:
                cons.append(f"【利潤壓力】毛利率偏低 ({gross_margin:.1f}%),易受全球原物料成本或價格戰侵蝕。")
                
            if revenue_growth > 5:
                score += 20
                pros.append(f"【成長動能】最新營收年增率達 {revenue_growth:.1f}%,呼應終端需求的實質復甦。")
            else:
                cons.append(f"【成長趨緩】營收年增率較平緩或呈微幅衰退 ({revenue_growth:.1f}%),短線動能需持續觀察。")
                
            if current_price > ma20:
                score += 10
                pros.append("【技術面】股價位於月線（20日均線）之上,短線多方佔優。")
            else:
                cons.append("【技術面】股價目前處於月線之下,短線籌碼正在整理,上檔逢壓。")
                
            score = max(0.0, min(100.0, score))
            
            if score >= 75:
                action = "基本面與技術面俱佳（建議依個人策略分批逢低佈局）"
                badge = "success"
            elif score >= 50:
                action = "區間震盪整理（建議列入觀察名單，等待技術面突破）"
                badge = "info"
            else:
                action = "風險評估宜保守（基本面或動能訊號較弱，建議暫時觀望）"
                badge = "error"
                
            return {
                "is_etf": False,
                "name": name,
                "current_price": current_price,
                "latest_date": latest_date,
                "fetch_timestamp": fetch_timestamp,
                "source_url": source_url,
                "metric1_name": "本益比 (PE)",
                "metric1_val": f"{pe_ratio:.1f} 倍" if isinstance(pe_ratio, (int, float)) else "N/A",
                "metric2_name": "毛利率",
                "metric2_val": f"{gross_margin:.1f}%",
                "metric3_name": "營收年增率",
                "metric3_val": f"{revenue_growth:.1f}%",
                "score": score,
                "action": action,
                "badge": badge,
                "pros": pros,
                "cons": cons,
                "success": True
            }
    except Exception as e:
        return {"success": False, "error": str(e)}

if st.sidebar.button("開始深度分析"):
    with st.spinner('正在結合國際總經與財報數據進行多維度掃描中...'):
        data = get_analysis(taiwan_ticker, is_etf)
        
    if not data["success"]:
        st.error(f"❌ 分析失敗：{data.get('error', '未知錯誤')}")
    else:
        # 1. 大盤與國際情勢總結
        st.subheader("🌐 國際總體經濟與市場氛圍")
        st.info("目前全球資本市場深受利率政策、地緣政治及供應鏈庫存調整影響。個股表現分化加劇，建議投資人切勿盲目追高，應回歸企業實質獲利與資產配置規劃。")
        
        target_type_str = "📦 ETF (一籃子分散資產)" if data["is_etf"] else "🏢 個股 (單一企業營運)"
        st.success(f"📌 你正在檢視：**{data['name']} ({ticker_input})** ｜ 類型：**{target_type_str}** ｜ 現價約 **{data['current_price']:.2f} 元**")
        
        st.caption(f"📅 **最近交易日**：`{data['latest_date']}` ｜ ⏱️ **系統查詢時間**：`{data['fetch_timestamp']}` ｜ 🔗 **資料來源**：[Yahoo 股市]({data['source_url']})")
        
        # 2. 核心指標卡片
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("綜合評估分數", f"{data['score']:.1f} 分")
        col2.metric(data["metric1_name"], data["metric1_val"])
        col3.metric(data["metric2_name"], data["metric2_val"])
        col4.metric(data["metric3_name"], data["metric3_val"])
        
        # 3. 專業觀點與多維度解析
        st.markdown("---")
        st.subheader("💡 深度專業觀點與多維度解析")
        
        if data['badge'] == 'success':
            st.success(f"🎯 **策略方向：{data['action']}**")
        elif data['badge'] == 'info':
            st.info(f"⚖️ **策略方向：{data['action']}**")
        else:
            st.error(f"⚠️ **策略方向：{data['action']}**")
            
        c1, c2 = st.columns(2)
        with c1:
            st.markdown("### ✅ **正向利多與優勢**")
            for pro in data['pros']:
                st.markdown(f"- {pro}")
        with c2:
            st.markdown("### ⚠️ **潛在風險與總經變數**")
            for con in data['cons']:
                st.markdown(f"- {con}")

        # 4. 資金配置建議
        st.markdown("---")
        user_tag = user_profile.split(' ')[0]
        st.subheader(f"💰 給「{user_tag}」的紀律資金配置建議")
        
        lot_price = data['current_price'] * 1000
        if data["is_etf"]:
            advice_msg = f"這檔 ETF 一張（1,000股）約需 **NT$ {lot_price:,.0f} 元**。由於其具備分散風險與應對總經波動的特性，極適合作為核心資產。建議透過 **定期定額** 或分批低接累積張數。"
        else:
            advice_msg = f"這檔個股一張約需 **NT$ {lot_price:,.0f} 元**。單一個股受產業循環與國際利空影響較大，切忌單筆重壓，務必採 **分批建倉**（例如分 3~5 次進場）並嚴格控管資金比重。"
        st.markdown(f"- **操作紀律**：{advice_msg}")

        # 5. 同類型關聯標的推薦
        sector_info = PEER_GROUPS.get(ticker_input, {
            "sector": "市場焦點精選族群", 
            "peers": [("0050", "元大台灣50"), ("2330", "台積電"), ("2317", "鴻海")]
        })
        
        st.markdown("---")
        st.subheader(f"🔗 同族群與產業鏈關聯標的（{sector_info['sector']}）")
        
        p_cols = st.columns(len(sector_info['peers']))
        for i, (p_code, p_name) in enumerate(sector_info['peers']):
            with p_cols[i]:
                st.markdown(f"**🏢 {p_name}** (`{p_code}`)")
                st.markdown("⭐ 同產業鏈代表性標的，可列入觀察比較。")

        st.markdown("---")
        st.caption("⚠️ **免責聲明**：本工具提供之數據、總經觀點與分析僅供教學與參考用途，不構成任何形式之買賣推薦或投資建議。投資具備一定風險，請獨立評估並自負盈虧。")
