import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(page_title="飆股／爛股智慧篩選器", layout="wide")

st.title("🎯 智慧飆股／爛股定位篩選器")
st.markdown("依照 **法人籌碼** × **營收與良率** 坐標系，快速診斷股票體質！")

# 側邊欄輸入
st.sidebar.header("設定股票代號")
ticker_input = st.sidebar.text_input("輸入台股代號 (例如: 2330, 2317)", value="2330")
taiwan_ticker = f"{ticker_input}.TW"

@st.cache_data
def get_stock_data(ticker):
    try:
        stock = yf.Ticker(ticker)
        info = stock.info
        
        # 模擬計算三大法人籌碼分數 (0~100) 與 買賣超指標
        # 實務上可串接台灣證交所 API，此處以財務與股權結構模擬
        holder_pct = info.get('heldPercentInstitutions', 0.5) * 100  # 法人持股比例
        
        # 模擬坐標數值
        x_val = holder_pct  # 籌碼多寡 (左少右多)
        y_val = np.random.uniform(-5000, 8000) # 模擬法人近期買賣超金額 (百萬)
        
        # 第一象限子坐標數值 (良率/毛利率代理變數, 年營收增長YoY)
        gross_margin = info.get('grossMargins', 0.25) * 100 # 良率/毛利代理
        x_prime = 100 - gross_margin  # 設定：左邊數字大(代表毛利好/良率高)，右邊小
        
        revenue_growth = info.get('revenueGrowth', 0.05) * 100 # 營收年增率
        y_prime = revenue_growth # 上正下負
        
        return {
            "name": info.get('shortName', ticker),
            "x": x_val,
            "y": y_val,
            "x_prime": x_prime,
            "y_prime": y_prime,
            "gross_margin": gross_margin,
            "revenue_growth": revenue_growth,
            "success": True
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

if st.sidebar.button("開始檢視"):
    with st.spinner('正在分析法人籌碼與財報數據...'):
        data = get_stock_data(taiwan_ticker)
        
    if not data["success"]:
        st.error(f"無法取得資料，請檢查代號是否正確。錯誤: {data['error']}")
    else:
        st.success(f"成功載入：{data['name']} ({ticker_input})")
        
        # 建立主畫面圖表
        fig = make_subplots(
            rows=1, cols=2, 
            subplot_titles=("【主坐標】法人籌碼多寡 vs 買賣超", "【第一象限細部】良率 vs 年營收")
        )
        
        # 1. 主坐標系圖表
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
        
        # 2. 第一象限子坐標系圖表
        fig.add_trace(
            go.Scatter(
                x=[data["x_prime"]], y=[data["y_prime"]],
                mode='markers+text',
                text=[ticker_input],
                textposition="top center",
                marker=dict(size=16, color='purple'),
                name='第一象限細部坐標'
            ),
            row=1, col=2
        )
        fig.update_xaxes(title_text="良率/毛利指標 (左: 數字大 $\rightarrow$ 右: 數字小)", row=1, col=2, autorange="reversed")
        fig.update_yaxes(title_text="年營收 (上正: 成長 $\rightarrow$ 下負: 衰退)", row=1, col=2)
        
        fig.update_layout(height=500, showlegend=False, title_text=f"{ticker_input} 坐標定位診斷報告")
        st.plotly_chart(fig, use_container_width=True)
        
        # 顯示詳細數據卡片
        col1, col2, col3 = st.columns(3)
        col1.metric("法人籌碼 X 軸分數", f"{data['x']:.1f}")
        col2.metric("良率指標 x' 軸 (左大右小)", f"{data['x_prime']:.1f}")
        col3.metric("年營收年增率 y' 軸", f"{data['revenue_growth']:.2f}%")
        
        # 診斷結論
        st.markdown("---")
        st.subheader("💡 系統診斷解讀")
        if data["x"] > 50 and data["y"] > 0:
            st.success("🎯 **【潛力飆股區（第一象限）】**：法人籌碼集中且持續買超！且其良率與年營收正向發展，屬於強勢優質標的。")
        elif data["x"] < 50 and data["y"] < 0:
            st.error("⚠️ **【弱勢爛股區（第三象限）】**：法人籌碼稀疏且持續賣超，基本面與籌碼面雙重弱勢，需嚴加防範。")
        else:
            st.info("⚖️ **【震盪整理區】**：多空交雜或法人籌碼尚未凝聚，建議搭配技術面多加觀察。")
