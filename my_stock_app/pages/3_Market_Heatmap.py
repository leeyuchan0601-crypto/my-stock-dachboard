import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
from PIL import Image
import os

# --- 1. 페이지 설정 및 아이콘 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Market Heatmap", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Market Heatmap", page_icon="🗺️", layout="wide")

# --- 2. 하이테크 스타일링 CSS ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(0, 212, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.2);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 프리셋 시장 데이터 메타정보 ---
KOSPI_MARKET_DATA = [
    {"ticker": "005930.KS", "name": "삼성전자", "sector": "반도체/IT", "weight": 350},
    {"ticker": "000660.KS", "name": "SK하이닉스", "sector": "반도체/IT", "weight": 130},
    {"ticker": "373220.KS", "name": "LG에너지솔루션", "sector": "2차전지", "weight": 80},
    {"ticker": "207940.KS", "name": "삼성바이오로직스", "sector": "제약/바이오", "weight": 60},
    {"ticker": "005380.KS", "name": "현대차", "sector": "자동차", "weight": 55},
    {"ticker": "000270.KS", "name": "기아", "sector": "자동차", "weight": 45},
    {"ticker": "068270.KS", "name": "셀트리온", "sector": "제약/바이오", "weight": 40},
    {"ticker": "105560.KS", "name": "KB금융", "sector": "금융/지주", "weight": 35},
    {"ticker": "055550.KS", "name": "신한지주", "sector": "금융/지주", "weight": 28},
    {"ticker": "035420.KS", "name": "NAVER", "sector": "인터넷/플랫폼", "weight": 27},
    {"ticker": "035720.KS", "name": "카카오", "sector": "인터넷/플랫폼", "weight": 18},
    {"ticker": "006400.KS", "name": "삼성SDI", "sector": "2차전지", "weight": 25},
    {"ticker": "012450.KS", "name": "한화에어로스페이스", "sector": "방산/조선", "weight": 20},
    {"ticker": "009540.KS", "name": "HD한국조선해양", "sector": "방산/조선", "weight": 18},
    {"ticker": "015760.KS", "name": "한국전력", "sector": "유틸리티", "weight": 15}
]

US_MARKET_DATA = [
    {"ticker": "NVDA", "name": "NVIDIA", "sector": "Semiconductors", "weight": 310},
    {"ticker": "AAPL", "name": "Apple", "sector": "Consumer Tech", "weight": 330},
    {"ticker": "MSFT", "name": "Microsoft", "sector": "Software/Cloud", "weight": 310},
    {"ticker": "GOOGL", "name": "Alphabet (Google)", "sector": "Communication/Search", "weight": 210},
    {"ticker": "AMZN", "name": "Amazon", "sector": "E-Commerce/Cloud", "weight": 190},
    {"ticker": "META", "name": "Meta", "sector": "Communication/Social", "weight": 140},
    {"ticker": "TSLA", "name": "Tesla", "sector": "Automotive/EV", "weight": 70},
    {"ticker": "AVGO", "name": "Broadcom", "sector": "Semiconductors", "weight": 80},
    {"ticker": "AMD", "name": "AMD", "sector": "Semiconductors", "weight": 25},
    {"ticker": "JPM", "name": "JPMorgan Chase", "sector": "Financial", "weight": 55},
    {"ticker": "LLY", "name": "Eli Lilly", "sector": "Healthcare", "weight": 80},
    {"ticker": "WMT", "name": "Walmart", "sector": "Consumer Defensive", "weight": 50}
]

# --- 4. 데이터 페칭 함수 (캐싱 적용) ---
@st.cache_data(ttl=300)
def fetch_heatmap_data(market_list):
    tickers = [item["ticker"] for item in market_list]
    try:
        data = yf.download(tickers, period="5d", progress=False)
        if isinstance(data.columns, pd.MultiIndex):
            close_data = data["Close"]
        else:
            close_data = data

        results = []
        for item in market_list:
            tk = item["ticker"]
            if tk in close_data.columns:
                series = close_data[tk].dropna()
                if len(series) >= 2:
                    curr_price = series.iloc[-1]
                    prev_price = series.iloc[-2]
                    pct_change = ((curr_price - prev_price) / prev_price) * 100
                else:
                    pct_change = 0.0
            else:
                pct_change = 0.0

            results.append({
                "Ticker": tk,
                "Name": item["name"],
                "Sector": item["sector"],
                "Weight": item["weight"],
                "Change": round(pct_change, 2),
                "ChangeText": f"{pct_change:+.2f}%"
            })
        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"데이터 연동 중 오류 발생: {e}")
        return pd.DataFrame()

# --- 5. UI 및 대시보드 렌더링 ---
st.title("🛰️ ZION : MARKET MAP TERMINAL")
st.write("시가총액 규모 및 당일 등락률을 트리맵 형태로 시각화합니다.")
st.write("---")

col_market, _ = st.columns([2, 3])
with col_market:
    selected_market = st.radio("분석 시장 선택", ["대한민국 KOSPI 주요 종목", "미국 S&P 500 빅테크"], horizontal=True)

target_dataset = KOSPI_MARKET_DATA if "KOSPI" in selected_market else US_MARKET_DATA

with st.spinner("📡 시장 데이터 수집 및 비주얼 매핑 중..."):
    df_heatmap = fetch_heatmap_data(target_dataset)

if not df_heatmap.empty:
    # Plotly Treemap 생성
    fig = px.treemap(
        df_heatmap,
        path=[px.Constant("ALL MARKET"), "Sector", "Name"],
        values="Weight",
        color="Change",
        color_continuous_scale=[
            [0.0, "#ff0055"],    # 하락 (붉은색)
            [0.5, "#1a1a1a"],    # 보합 (어두운 회색)
            [1.0, "#00ff66"]     # 상승 (녹색)
        ],
        color_continuous_midpoint=0,
        custom_data=["Ticker", "ChangeText"]
    )

    # 텍스트 레이아웃 및 툴팁 서식 지정
    fig.update_traces(
        texttemplate="<b>%{label}</b><br>%{customdata[1]}",
        hovertemplate="<b>종목:</b> %{label} (%{customdata[0]})<br><b>변동률:</b> %{customdata[1]}<br><b>비중 지수:</b> %{value}"
    )

    fig.update_layout(
        template="plotly_dark",
        height=750,
        margin=dict(l=10, r=10, t=30, b=10),
        coloraxis_colorbar=dict(
            title="등락률 (%)",
            ticksuffix="%",
            dtick=2
        )
    )

    st.plotly_chart(fig, use_container_width=True)

    # 하단 시장 요약 메트릭
    st.write("---")
    st.subheader("📊 섹터별 동향 요약")
    
    gainers = df_heatmap[df_heatmap["Change"] > 0]
    losers = df_heatmap[df_heatmap["Change"] < 0]
    
    m1, m2, m3 = st.columns(3)
    m1.metric("상승 종목 수", f"{len(gainers)} 개")
    m2.metric("하락 종목 수", f"{len(losers)} 개")
    m3.metric("최대 상승 종목", f"{df_heatmap.loc[df_heatmap['Change'].idxmax()]['Name']} ({df_heatmap['Change'].max():+.2f}%)" if not df_heatmap.empty else "-")

else:
    st.error("히트맵 데이터를 구성하지 못했습니다.")
