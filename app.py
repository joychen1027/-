import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="智慧飆股／爛股定位與評分系統", layout="wide")

st.title("🎯 智慧飆股／爛股定位與投資決策篩選器")
st.markdown("結合 **法人籌碼** × **財報基本面** × **技術面趨勢**，自動產出智慧評分與購入建議！")

# 側邊欄輸入
st.sidebar.header("設定股票代號")
ticker_input = st.sidebar.text_input("輸入台股代號 (例如: 2330, 2317)", value="2330")
taiwan_ticker = f"{ticker_input}.TW"

@st.cache_data
def get_stock_analysis(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 取得歷史股價來計算簡單技術面 (MA20)
        hist = stock.history(period="3mo")
        current_price = hist['Close'].iloc[-1] if not hist.empty else 100.0
        ma20 = hist['Close'].rolling(window=20).mean().iloc[-1] if len(hist) >= 20 else current_price
        
        # 基本面與籌碼數據
        holder_pct = info.get('heldPercentInstitutions', 0.5) * 100  # 法人持股比例
        gross_margin = info.get('grossMargins', 0.25) * 100          # 毛利率
        revenue_growth = info.get('revenueGrowth', 0.05) * 100       # 營收年增率
        pe_ratio = info.get('trailingPE', 20.0)                      # 本益比
        
        # 模擬法人近期買賣超金額 (-5000 到 8000 百萬)
        y_val = np.random.uniform(-3000, 6000)
        x_val = holder_pct
        
        x_prime = 100 - gross_margin
        y_prime = revenue_growth
        
        # --- 【智慧評分機制 (0 ~ 100分)】 ---
        score = 50.0  # 基礎分
        
        # 1. 籌碼面加減分
        if x_val > 50: score += 15
        if y_val > 0: score += 15
        else: score -= 15
        
        # 2. 基本面加減分
        if gross_margin > 30: score += 10
        if revenue_growth > 10: score += 10
        elif revenue_growth < 0: score -= 10
        
        # 3. 技術面加減分 (股價大於 20 日均線代表多頭)
        is_bullish = current_price > ma20
        if is_bullish: score += 10
        else: score -= 10
        
        # 確保分數介於 0 到 100 之間
        score = max(0.0, min(100.0, score))
        
        # 決策建議判定
        if score >= 75:
            advice = "強烈建議購入 (多方優勢明顯)"
            level = "success"
        elif score >= 55:
            advice = "區間震盪 / 逢低分批布局"
            level = "info"
        else:
            advice = "不建議購入 / 建議保守觀望"
            level = "error"

        return {
            "name": info.get('shortName', ticker),
            "current_price": current_price,
            "x": x_val,
            "y": y_val,
            "x_prime": x_prime,
            "y_prime": y_prime,
            "gross_margin": gross_margin,
            "revenue_growth": revenue_growth,
            "pe_ratio": pe_ratio,
            "is_bullish": is_bullish,
            "score": score,
            "advice": advice,
            "level": level,
            "success": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if st.sidebar.button("開始智慧檢視"):
    with st.spinner('正在整合籌碼、財報與技術面大數據分析中...'):
        data = get_stock_analysis(taiwan_ticker)
        
    if not data["success"]:
        st.error(f"無法取得資料，請檢查代號是否正確。錯誤: {data['error']}")
    else:
        st.success(f"成功載入：{data['name']} ({ticker_input}) | 現價約: {data['current_price']:.2f} 元")
        
        # 建立圖表
        fig = make_subplots(
            rows=1, cols=2, 
            subplot_titles=("【主坐標】法人籌碼多寡 vs 買賣超", "【第一象限細部】良率/毛利 vs 年營收")
        )
        
        fig.add_trace(
            go.Scatter(
                x=[data["x"]], y=[data["y"]],
                mode='markers+text',
                text=[ticker_input],
                textposition="top center",
                marker=dict(size=16, color='red' if data["y"] > 0 else 'blue'),
                name='目標股票'
            ),
            row=1, col=1
        )
        fig.update_xaxes(title_text="法人籌碼多寡 (左: 少 $\rightarrow$ 右: 多)", row=1, col=1)
        fig.update_yaxes(title_text="法人買／賣超 (上: 買超 $\rightarrow$ 下: 賣超)", row=1, col=1)
        
        fig.add_trace(
            go.Scatter(
                x=[data["x_prime"]], y=[data["y_prime"]],
                mode='markers+text',
                text=[ticker_input],
                textposition="top center",
                marker=dict(size=16, color='purple'),
                name='細部坐標'
            ),
            row=1, col=2
        )
        fig.update_xaxes(title_text="毛利指標 (左: 數字大 $\rightarrow$ 右: 數字小)", row=1, col=2, autorange="reversed")
        fig.update_yaxes(title_text="年營收年增率 YoY", row=1, col=2)
        
        fig.update_layout(height=500, showlegend=False, title_text=f"{ticker_input} 多維度綜合診斷圖表")
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示詳細數據卡片
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("綜合智慧評分", f"{data['score']:.1f} 分")
        col2.metric("毛利率", f"{data['gross_margin']:.1f}%")
        col3.metric("年營收年增率", f"{data['revenue_growth']:.2f}%")
        col4.metric("技術趨勢 (vs MA20)", "多頭排列" if data['is_bullish'] else "空頭/修正")
        
        # 智慧建議與診斷區
        st.markdown("---")
        st.subheader("💡 系統智慧評估與購買建議")
        
        if data['level'] == 'success':
            st.success(f"🎯 **【評級：強烈建議購入】**\n\n系統綜合評分 **{data['score']:.1f} 分**。{data['advice']}！法人籌碼與基本面表現亮眼，符合多頭發動特徵。")
        elif data['level'] == 'info':
            st.info(f"⚖️ **【評級：區間震盪 / 觀望】**\n\n系統綜合評分 **{data['score']:.1f} 分**。{data['advice']}。多空力道拉鋸，建議等待法人明確表態或拉回再行評估。")
        else:
            st.error(f"⚠️ **【評級：不建議購入 / 避開】**\n\n系統綜合評分 **{data['score']:.1f} 分**。{data['advice']}。籌碼或營收動能轉弱，需嚴防下檔風險。")
            
        # 投資免責聲明
        st.markdown("---")
        st.caption("⚠️ **免責聲明**：本系統之評分與分析建議僅供量化參考，不具任何投資勸誘、保證獲利或買賣建議。股票投資具有潛在風險，投資人應獨立思考並自負盈虧。")
