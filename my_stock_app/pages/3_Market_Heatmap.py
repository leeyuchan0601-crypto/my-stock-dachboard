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

# --- 3. 코스피 확장 종목 데이터베이스 (약 50개 종목) ---
KOSPI_STOCKS = [
    # 반도체/IT/전자
    {"ticker": "005930.KS", "name": "삼성전자", "sector": "반도체/IT", "weight": 350},
    {"ticker": "000660.KS", "name": "SK하이닉스", "sector": "반도체/IT", "weight": 140},
    {"ticker": "042700.KS", "name": "한미반도체", "sector": "반도체/IT", "weight": 20},
    {"ticker": "009150.KS", "name": "삼성전기", "sector": "반도체/IT", "weight": 18},
    {"ticker": "011070.KS", "name": "LG이노텍", "sector": "반도체/IT", "weight": 12},
    {"ticker": "018260.KS", "name": "삼성SDS", "sector": "반도체/IT", "weight": 15},

    # 2차전지/화학/정유
    {"ticker": "373220.KS", "name": "LG에너지솔루션", "sector": "2차전지/화학/에너지", "weight": 80},
    {"ticker": "006400.KS", "name": "삼성SDI", "sector": "2차전지/화학/에너지", "weight": 25},
    {"ticker": "005490.KS", "name": "POSCO홀딩스", "sector": "2차전지/화학/에너지", "weight": 32},
    {"ticker": "051910.KS", "name": "LG화학", "sector": "2차전지/화학/에너지", "weight": 22},
    {"ticker": "003670.KS", "name": "포스코퓨처엠", "sector": "2차전지/화학/에너지", "weight": 20},
    {"ticker": "096770.KS", "name": "SK이노베이션", "sector": "2차전지/화학/에너지", "weight": 15},
    {"ticker": "010950.KS", "name": "S-Oil", "sector": "2차전지/화학/에너지", "weight": 12},

    # 제약/바이오
    {"ticker": "207940.KS", "name": "삼성바이오로직스", "sector": "제약/바이오", "weight": 65},
    {"ticker": "068270.KS", "name": "셀트리온", "sector": "제약/바이오", "weight": 45},
    {"ticker": "000100.KS", "name": "유한양행", "sector": "제약/바이오", "weight": 15},
    {"ticker": "128940.KS", "name": "한미약품", "sector": "제약/바이오", "weight": 12},
    {"ticker": "326030.KS", "name": "SK바이오팜", "sector": "제약/바이오", "weight": 10},

    # 자동차/모빌리티
    {"ticker": "005380.KS", "name": "현대차", "sector": "자동차/모빌리티", "weight": 55},
    {"ticker": "000270.KS", "name": "기아", "sector": "자동차/모빌리티", "weight": 50},
    {"ticker": "012330.KS", "name": "현대모비스", "sector": "자동차/모빌리티", "weight": 22},
    {"ticker": "204320.KS", "name": "HL만도", "sector": "자동차/모빌리티", "weight": 8},

    # 방산/조선/중공업
    {"ticker": "012450.KS", "name": "한화에어로스페이스", "sector": "방산/조선/중공업", "weight": 30},
    {"ticker": "064350.KS", "name": "현대로템", "sector": "방산/조선/중공업", "weight": 18},
    {"ticker": "079550.KS", "name": "LIG넥스원", "sector": "방산/조선/중공업", "weight": 15},
    {"ticker": "329180.KS", "name": "HD현대중공업", "sector": "방산/조선/중공업", "weight": 20},
    {"ticker": "042660.KS", "name": "한화오션", "sector": "방산/조선/중공업", "weight": 18},
    {"ticker": "010140.KS", "name": "삼성중공업", "sector": "방산/조선/중공업", "weight": 14},
    {"ticker": "034020.KS", "name": "두산에너빌리티", "sector": "방산/조선/중공업", "weight": 22},

    # 전력/전력기기
    {"ticker": "267260.KS", "name": "HD현대일렉트릭", "sector": "전력/전력기기", "weight": 25},
    {"ticker": "010120.KS", "name": "LS일렉트릭", "sector": "전력/전력기기", "weight": 18},
    {"ticker": "015760.KS", "name": "한국전력", "sector": "전력/전력기기", "weight": 16},

    # 금융/지주/증권
    {"ticker": "105560.KS", "name": "KB금융", "sector": "금융/지주", "weight": 35},
    {"ticker": "055550.KS", "name": "신한지주", "sector": "금융/지주", "weight": 30},
    {"ticker": "086790.KS", "name": "하나금융지주", "sector": "금융/지주", "weight": 20},
    {"ticker": "316140.KS", "name": "우리금융지주", "sector": "금융/지주", "weight": 16},
    {"ticker": "138040.KS", "name": "메리츠금융지주", "sector": "금융/지주", "weight": 18},
    {"ticker": "032830.KS", "name": "삼성생명", "sector": "금융/지주", "weight": 18},
    {"ticker": "000810.KS", "name": "삼성화재", "sector": "금융/지주", "weight": 16},
    {"ticker": "006800.KS", "name": "미래에셋증권", "sector": "금융/지주", "weight": 10},

    # 플랫폼/통신
    {"ticker": "035420.KS", "name": "NAVER", "sector": "플랫폼/통신", "weight": 30},
    {"ticker": "035720.KS", "name": "카카오", "sector": "플랫폼/통신", "weight": 22},
    {"ticker": "017670.KS", "name": "SK텔레콤", "sector": "플랫폼/통신", "weight": 15},
    {"ticker": "030200.KS", "name": "KT", "sector": "플랫폼/통신", "weight": 14},

    # 유통/소비재/뷰티
    {"ticker": "090430.KS", "name": "아모레퍼시픽", "sector": "소비재/유통/뷰티", "weight": 14},
    {"ticker": "051900.KS", "name": "LG생활건강", "sector": "소비재/유통/뷰티", "weight": 12},
    {"ticker": "033780.KS", "name": "KT&G", "sector": "소비재/유통/뷰티", "weight": 18},
    {"ticker": "097950.KS", "name": "CJ제일제당", "sector": "소비재/유통/뷰티", "weight": 10},

    # 철강/건설/지주
    {"ticker": "010130.KS", "name": "고려아연", "sector": "철강/건설/인프라", "weight": 20},
    {"ticker": "004020.KS", "name": "현대제철", "sector": "철강/건설/인프라", "weight": 10},
    {"ticker": "028260.KS", "name": "삼성물산", "sector": "철강/건설/인프라", "weight": 25}
]

US_MARKET_DATA = [
    # Semiconductors & Hardware
    {"ticker": "NVDA", "name": "NVIDIA", "sector": "Semiconductors", "weight": 310},
    {"ticker": "AVGO", "name": "Broadcom", "sector": "Semiconductors", "weight": 85},
    {"ticker": "AMD", "name": "AMD", "sector": "Semiconductors", "weight": 25},
    {"ticker": "QCOM", "name": "Qualcomm", "sector": "Semiconductors", "weight": 22},
    {"ticker": "INTC", "name": "Intel", "sector": "Semiconductors", "weight": 12},
    {"ticker": "MU", "name": "Micron", "sector": "Semiconductors", "weight": 15},
    {"ticker": "AMAT", "name": "Applied Materials", "sector": "Semiconductors", "weight": 18},
    {"ticker": "LRCX", "name": "Lam Research", "sector": "Semiconductors", "weight": 16},

    # Consumer Tech & Software/Cloud
    {"ticker": "AAPL", "name": "Apple", "sector": "Consumer Tech", "weight": 330},
    {"ticker": "MSFT", "name": "Microsoft", "sector": "Software/Cloud", "weight": 310},
    {"ticker": "ORCL", "name": "Oracle", "sector": "Software/Cloud", "weight": 45},
    {"ticker": "CRM", "name": "Salesforce", "sector": "Software/Cloud", "weight": 30},
    {"ticker": "PLTR", "name": "Palantir", "sector": "Software/Cloud", "weight": 20},
    {"ticker": "ADBE", "name": "Adobe", "sector": "Software/Cloud", "weight": 22},
    {"ticker": "NOW", "name": "ServiceNow", "sector": "Software/Cloud", "weight": 18},
    {"ticker": "INTU", "name": "Intuit", "sector": "Software/Cloud", "weight": 17},

    # Communication & Search & Social
    {"ticker": "GOOGL", "name": "Alphabet (Google)", "sector": "Communication/Search", "weight": 210},
    {"ticker": "META", "name": "Meta", "sector": "Communication/Social", "weight": 140},
    {"ticker": "NFLX", "name": "Netflix", "sector": "Communication/Media", "weight": 38},
    {"ticker": "DIS", "name": "Disney", "sector": "Communication/Media", "weight": 20},
    {"ticker": "TMUS", "name": "T-Mobile", "sector": "Communication/Telecom", "weight": 22},

    # E-Commerce & Retail & Auto
    {"ticker": "AMZN", "name": "Amazon", "sector": "E-Commerce/Cloud", "weight": 190},
    {"ticker": "TSLA", "name": "Tesla", "sector": "Automotive/EV", "weight": 75},
    {"ticker": "WMT", "name": "Walmart", "sector": "Consumer Retail", "weight": 55},
    {"ticker": "COST", "name": "Costco", "sector": "Consumer Retail", "weight": 42},
    {"ticker": "HD", "name": "Home Depot", "sector": "Consumer Retail", "weight": 38},
    {"ticker": "TGT", "name": "Target", "sector": "Consumer Retail", "weight": 10},

    # Financial
    {"ticker": "JPM", "name": "JPMorgan Chase", "sector": "Financial", "weight": 60},
    {"ticker": "BRK-B", "name": "Berkshire Hathaway", "sector": "Financial", "weight": 90},
    {"ticker": "V", "name": "Visa", "sector": "Financial", "weight": 55},
    {"ticker": "MA", "name": "Mastercard", "sector": "Financial", "weight": 45},
    {"ticker": "BAC", "name": "Bank of America", "sector": "Financial", "weight": 30},
    {"ticker": "GS", "name": "Goldman Sachs", "sector": "Financial", "weight": 18},
    {"ticker": "MS", "name": "Morgan Stanley", "sector": "Financial", "weight": 18},

    # Healthcare & Pharma
    {"ticker": "LLY", "name": "Eli Lilly", "sector": "Healthcare", "weight": 80},
    {"ticker": "UNH", "name": "UnitedHealth", "sector": "Healthcare", "weight": 50},
    {"ticker": "JNJ", "name": "Johnson & Johnson", "sector": "Healthcare", "weight": 38},
    {"ticker": "ABBV", "name": "AbbVie", "sector": "Healthcare", "weight": 32},
    {"ticker": "MRK", "name": "Merck", "sector": "Healthcare", "weight": 28},
    {"ticker": "PFE", "name": "Pfizer", "sector": "Healthcare", "weight": 16},

    # Consumer Defensive
    {"ticker": "PG", "name": "Procter & Gamble", "sector": "Consumer Defensive", "weight": 40},
    {"ticker": "KO", "name": "Coca-Cola", "sector": "Consumer Defensive", "weight": 28},
    {"ticker": "PEP", "name": "PepsiCo", "sector": "Consumer Defensive", "weight": 24},

    # Industrial & Defense & Energy
    {"ticker": "GE", "name": "GE Aerospace", "sector": "Industrial/Defense", "weight": 22},
    {"ticker": "CAT", "name": "Caterpillar", "sector": "Industrial/Defense", "weight": 20},
    {"ticker": "RTX", "name": "RTX (Raytheon)", "sector": "Industrial/Defense", "weight": 18},
    {"ticker": "LMT", "name": "Lockheed Martin", "sector": "Industrial/Defense", "weight": 15},
    {"ticker": "XOM", "name": "ExxonMobil", "sector": "Energy", "weight": 50},
    {"ticker": "CVX", "name": "Chevron", "sector": "Energy", "weight": 28}
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
