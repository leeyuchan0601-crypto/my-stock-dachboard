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

# 아까 발생했던 NameError 방지를 위한 동기화
KOSPI_MARKET_DATA = KOSPI_STOCKS

US_MARKET_DATA = [
    # --- Technology (Software, Semi, Hardware, Comm Tech) ---
    {"ticker": "MSFT", "name": "MSFT", "sector": "Tech - Software Infra", "weight": 320},
    {"ticker": "ORCL", "name": "ORCL", "sector": "Tech - Software Infra", "weight": 55},
    {"ticker": "PLTR", "name": "PLTR", "sector": "Tech - Software Infra", "weight": 25},
    {"ticker": "PANW", "name": "PANW", "sector": "Tech - Software Infra", "weight": 18},
    {"ticker": "CRWD", "name": "CRWD", "sector": "Tech - Software Infra", "weight": 16},
    {"ticker": "SNPS", "name": "SNPS", "sector": "Tech - Software Infra", "weight": 14},
    {"ticker": "CDNS", "name": "CDNS", "sector": "Tech - Software Infra", "weight": 14},
    {"ticker": "FTNT", "name": "FTNT", "sector": "Tech - Software Infra", "weight": 12},

    {"ticker": "AAPL", "name": "AAPL", "sector": "Tech - Consumer Electronics", "weight": 340},
    {"ticker": "HPQ", "name": "HPQ", "sector": "Tech - Consumer Electronics", "weight": 10},

    {"ticker": "NVDA", "name": "NVDA", "sector": "Tech - Semiconductors", "weight": 310},
    {"ticker": "AVGO", "name": "AVGO", "sector": "Tech - Semiconductors", "weight": 90},
    {"ticker": "AMD", "name": "AMD", "sector": "Tech - Semiconductors", "weight": 28},
    {"ticker": "QCOM", "name": "QCOM", "sector": "Tech - Semiconductors", "weight": 26},
    {"ticker": "TXN", "name": "TXN", "sector": "Tech - Semiconductors", "weight": 22},
    {"ticker": "MU", "name": "MU", "sector": "Tech - Semiconductors", "weight": 18},
    {"ticker": "INTC", "name": "INTC", "sector": "Tech - Semiconductors", "weight": 14},
    {"ticker": "ADI", "name": "ADI", "sector": "Tech - Semiconductors", "weight": 16},
    {"ticker": "AMAT", "name": "AMAT", "sector": "Tech - Semi Equipment", "weight": 22},
    {"ticker": "LRCX", "name": "LRCX", "sector": "Tech - Semi Equipment", "weight": 18},
    {"ticker": "KLAC", "name": "KLAC", "sector": "Tech - Semi Equipment", "weight": 16},

    {"ticker": "CRM", "name": "CRM", "sector": "Tech - Software Apps", "weight": 32},
    {"ticker": "ADBE", "name": "ADBE", "sector": "Tech - Software Apps", "weight": 24},
    {"ticker": "NOW", "name": "NOW", "sector": "Tech - Software Apps", "weight": 22},
    {"ticker": "INTU", "name": "INTU", "sector": "Tech - Software Apps", "weight": 20},
    {"ticker": "UBER", "name": "UBER", "sector": "Tech - Software Apps", "weight": 22},
    {"ticker": "SHOP", "name": "SHOP", "sector": "Tech - Software Apps", "weight": 18},

    {"ticker": "IBM", "name": "IBM", "sector": "Tech - IT Services & Comm", "weight": 26},
    {"ticker": "ACN", "name": "ACN", "sector": "Tech - IT Services & Comm", "weight": 24},
    {"ticker": "CSCO", "name": "CSCO", "sector": "Tech - IT Services & Comm", "weight": 28},
    {"ticker": "ANET", "name": "ANET", "sector": "Tech - IT Services & Comm", "weight": 18},

    # --- Communication Services ---
    {"ticker": "GOOGL", "name": "GOOGL", "sector": "Comm - Internet Content", "weight": 220},
    {"ticker": "META", "name": "META", "sector": "Comm - Internet Content", "weight": 150},
    {"ticker": "NFLX", "name": "NFLX", "sector": "Comm - Entertainment", "weight": 40},
    {"ticker": "DIS", "name": "DIS", "sector": "Comm - Entertainment", "weight": 22},
    {"ticker": "SPOT", "name": "SPOT", "sector": "Comm - Entertainment", "weight": 12},
    {"ticker": "TMUS", "name": "TMUS", "sector": "Comm - Telecom", "weight": 24},
    {"ticker": "VZ", "name": "VZ", "sector": "Comm - Telecom", "weight": 20},
    {"ticker": "T", "name": "T", "sector": "Comm - Telecom", "weight": 18},

    # --- Consumer Cyclical (Retail, Auto, Restaurants, Apparel) ---
    {"ticker": "AMZN", "name": "AMZN", "sector": "Cyclical - Internet Retail", "weight": 200},
    {"ticker": "BABA", "name": "BABA", "sector": "Cyclical - Internet Retail", "weight": 25},
    {"ticker": "PDD", "name": "PDD", "sector": "Cyclical - Internet Retail", "weight": 20},
    {"ticker": "MELI", "name": "MELI", "sector": "Cyclical - Internet Retail", "weight": 15},
    {"ticker": "DASH", "name": "DASH", "sector": "Cyclical - Internet Retail", "weight": 12},

    {"ticker": "TSLA", "name": "TSLA", "sector": "Cyclical - Auto Manufacturers", "weight": 85},
    {"ticker": "TM", "name": "TM", "sector": "Cyclical - Auto Manufacturers", "weight": 30},
    {"ticker": "F", "name": "F", "sector": "Cyclical - Auto Manufacturers", "weight": 12},
    {"ticker": "GM", "name": "GM", "sector": "Cyclical - Auto Manufacturers", "weight": 12},
    {"ticker": "RACE", "name": "RACE", "sector": "Cyclical - Auto Manufacturers", "weight": 15},

    {"ticker": "MCD", "name": "MCD", "sector": "Cyclical - Restaurants & Retail", "weight": 26},
    {"ticker": "SBUX", "name": "SBUX", "sector": "Cyclical - Restaurants & Retail", "weight": 16},
    {"ticker": "HD", "name": "HD", "sector": "Cyclical - Home Improvement", "weight": 42},
    {"ticker": "LOW", "name": "LOW", "sector": "Cyclical - Home Improvement", "weight": 20},
    {"ticker": "NKE", "name": "NKE", "sector": "Cyclical - Apparel & Travel", "weight": 16},
    {"ticker": "TJX", "name": "TJX", "sector": "Cyclical - Apparel & Travel", "weight": 18},
    {"ticker": "BKNG", "name": "BKNG", "sector": "Cyclical - Apparel & Travel", "weight": 22},
    {"ticker": "ABNB", "name": "ABNB", "sector": "Cyclical - Apparel & Travel", "weight": 14},

    # --- Consumer Defensive (Stores, Beverage, Tobacco) ---
    {"ticker": "WMT", "name": "WMT", "sector": "Defensive - Discount Stores", "weight": 60},
    {"ticker": "COST", "name": "COST", "sector": "Defensive - Discount Stores", "weight": 45},
    {"ticker": "TGT", "name": "TGT", "sector": "Defensive - Discount Stores", "weight": 12},

    {"ticker": "PG", "name": "PG", "sector": "Defensive - Household & Personal", "weight": 45},
    {"ticker": "CL", "name": "CL", "sector": "Defensive - Household & Personal", "weight": 12},

    {"ticker": "KO", "name": "KO", "sector": "Defensive - Beverages", "weight": 30},
    {"ticker": "PEP", "name": "PEP", "sector": "Defensive - Beverages", "weight": 26},
    {"ticker": "MNST", "name": "MNST", "sector": "Defensive - Beverages", "weight": 10},

    {"ticker": "PM", "name": "PM", "sector": "Defensive - Tobacco & Food", "weight": 22},
    {"ticker": "MO", "name": "MO", "sector": "Defensive - Tobacco & Food", "weight": 14},
    {"ticker": "MDLZ", "name": "MDLZ", "sector": "Defensive - Tobacco & Food", "weight": 15},

    # --- Financial (Banks, Credit, Asset Management, Insurance) ---
    {"ticker": "JPM", "name": "JPM", "sector": "Financial - Diversified Banks", "weight": 65},
    {"ticker": "BAC", "name": "BAC", "sector": "Financial - Diversified Banks", "weight": 32},
    {"ticker": "WFC", "name": "WFC", "sector": "Financial - Diversified Banks", "weight": 26},
    {"ticker": "C", "name": "C", "sector": "Financial - Diversified Banks", "weight": 18},
    {"ticker": "HSBC", "name": "HSBC", "sector": "Financial - Diversified Banks", "weight": 20},

    {"ticker": "V", "name": "V", "sector": "Financial - Credit Services", "weight": 60},
    {"ticker": "MA", "name": "MA", "sector": "Financial - Credit Services", "weight": 50},
    {"ticker": "AXP", "name": "AXP", "sector": "Financial - Credit Services", "weight": 24},
    {"ticker": "COF", "name": "COF", "sector": "Financial - Credit Services", "weight": 12},

    {"ticker": "BRK-B", "name": "BRK-B", "sector": "Financial - Insurance & Holdings", "weight": 95},
    {"ticker": "PGR", "name": "PGR", "sector": "Financial - Insurance & Holdings", "weight": 20},
    {"ticker": "CB", "name": "CB", "sector": "Financial - Insurance & Holdings", "weight": 16},

    {"ticker": "BX", "name": "BX", "sector": "Financial - Asset Mgmt & Capital", "weight": 28},
    {"ticker": "KKR", "name": "KKR", "sector": "Financial - Asset Mgmt & Capital", "weight": 20},
    {"ticker": "BLK", "name": "BLK", "sector": "Financial - Asset Mgmt & Capital", "weight": 22},
    {"ticker": "MS", "name": "MS", "sector": "Financial - Asset Mgmt & Capital", "weight": 20},
    {"ticker": "GS", "name": "GS", "sector": "Financial - Asset Mgmt & Capital", "weight": 20},
    {"ticker": "SCHW", "name": "SCHW", "sector": "Financial - Asset Mgmt & Capital", "weight": 18},
    {"ticker": "SPGI", "name": "SPGI", "sector": "Financial - Asset Mgmt & Capital", "weight": 22},

    # --- Healthcare (Pharma, Medical Devices, Biotech, Services) ---
    {"ticker": "LLY", "name": "LLY", "sector": "Healthcare - Drug Mfrs", "weight": 85},
    {"ticker": "JNJ", "name": "JNJ", "sector": "Healthcare - Drug Mfrs", "weight": 40},
    {"ticker": "ABBV", "name": "ABBV", "sector": "Healthcare - Drug Mfrs", "weight": 35},
    {"ticker": "MRK", "name": "MRK", "sector": "Healthcare - Drug Mfrs", "weight": 30},
    {"ticker": "PFE", "name": "PFE", "sector": "Healthcare - Drug Mfrs", "weight": 18},
    {"ticker": "AZN", "name": "AZN", "sector": "Healthcare - Drug Mfrs", "weight": 22},
    {"ticker": "NVS", "name": "NVS", "sector": "Healthcare - Drug Mfrs", "weight": 24},
    {"ticker": "NVO", "name": "NVO", "sector": "Healthcare - Drug Mfrs", "weight": 50},

    {"ticker": "ABT", "name": "ABT", "sector": "Healthcare - Medical Devices", "weight": 24},
    {"ticker": "SYK", "name": "SYK", "sector": "Healthcare - Medical Devices", "weight": 18},
    {"ticker": "MDT", "name": "MDT", "sector": "Healthcare - Medical Devices", "weight": 16},
    {"ticker": "BSX", "name": "BSX", "sector": "Healthcare - Medical Devices", "weight": 20},
    {"ticker": "ISRG", "name": "ISRG", "sector": "Healthcare - Medical Devices", "weight": 25},

    {"ticker": "TMO", "name": "TMO", "sector": "Healthcare - Diagnostics & Research", "weight": 26},
    {"ticker": "DHR", "name": "DHR", "sector": "Healthcare - Diagnostics & Research", "weight": 22},

    {"ticker": "UNH", "name": "UNH", "sector": "Healthcare - Healthcare Plans", "weight": 55},
    {"ticker": "CVS", "name": "CVS", "sector": "Healthcare - Healthcare Plans", "weight": 14},
    {"ticker": "CI", "name": "CI", "sector": "Healthcare - Healthcare Plans", "weight": 16},

    # --- Industrials (Aerospace, Machinery, Railroads) ---
    {"ticker": "GE", "name": "GE", "sector": "Industrials - Aerospace & Defense", "weight": 24},
    {"ticker": "BA", "name": "BA", "sector": "Industrials - Aerospace & Defense", "weight": 16},
    {"ticker": "LMT", "name": "LMT", "sector": "Industrials - Aerospace & Defense", "weight": 18},
    {"ticker": "RTX", "name": "RTX", "sector": "Industrials - Aerospace & Defense", "weight": 22},
    {"ticker": "GD", "name": "GD", "sector": "Industrials - Aerospace & Defense", "weight": 14},

    {"ticker": "CAT", "name": "CAT", "sector": "Industrials - Farm & Construction", "weight": 24},
    {"ticker": "DE", "name": "DE", "sector": "Industrials - Farm & Construction", "weight": 18},
    {"ticker": "UNP", "name": "UNP", "sector": "Industrials - Railroads & Logistics", "weight": 20},
    {"ticker": "HON", "name": "HON", "sector": "Industrials - Conglomerates & Elec", "weight": 18},
    {"ticker": "ETN", "name": "ETN", "sector": "Industrials - Conglomerates & Elec", "weight": 22},

    # --- Energy (Oil, Gas, Services) ---
    {"ticker": "XOM", "name": "XOM", "sector": "Energy - Oil & Gas Integrated", "weight": 55},
    {"ticker": "CVX", "name": "CVX", "sector": "Energy - Oil & Gas Integrated", "weight": 32},
    {"ticker": "SHEL", "name": "SHEL", "sector": "Energy - Oil & Gas Integrated", "weight": 24},
    {"ticker": "TTE", "name": "TTE", "sector": "Energy - Oil & Gas Integrated", "weight": 20},
    {"ticker": "COP", "name": "COP", "sector": "Energy - E&P", "weight": 18},
    {"ticker": "SLB", "name": "SLB", "sector": "Energy - Services", "weight": 14},

    # --- Utilities, Real Estate, Basic Materials ---
    {"ticker": "NEE", "name": "NEE", "sector": "Utilities", "weight": 20},
    {"ticker": "DUK", "name": "DUK", "sector": "Utilities", "weight": 12},
    {"ticker": "SO", "name": "SO", "sector": "Utilities", "weight": 12},

    {"ticker": "AMT", "name": "AMT", "sector": "Real Estate - REITs", "weight": 16},
    {"ticker": "PLD", "name": "PLD", "sector": "Real Estate - REITs", "weight": 16},

    {"ticker": "LIN", "name": "LIN", "sector": "Basic Materials - Chemicals & Gold", "weight": 25},
    {"ticker": "SHW", "name": "SHW", "sector": "Basic Materials - Chemicals & Gold", "weight": 14},
    {"ticker": "NEM", "name": "NEM", "sector": "Basic Materials - Chemicals & Gold", "weight": 12},
    {"ticker": "FCX", "name": "FCX", "sector": "Basic Materials - Chemicals & Gold", "weight": 12}
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

target_dataset = KOSPI_STOCKS if "KOSPI" in selected_market else US_MARKET_DATA

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
        custom_data=["Ticker", "ChangeText", "Name"]
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

    # on_select="rerun"을 활성화하여 클릭 이벤트를 감지
    event = st.plotly_chart(
        fig, 
        use_container_width=True, 
        on_select="rerun", 
        key="heatmap_chart"
    )

    # 클릭된 종목이 있을 경우 세션에 티커 저장 후 Analyzer 페이지로 즉시 이동
    if event and "selection" in event and event["selection"]["points"]:
        point = event["selection"]["points"][0]
        if "customdata" in point and len(point["customdata"]) > 0:
            clicked_ticker = point["customdata"][0]
            
            # 상위 분류(루트 및 섹터) 클릭 제외하고 실제 종목 티커인 경우만 이동
            if clicked_ticker and clicked_ticker != "ALL MARKET":
                # Analyzer 세션 상태 업데이트
                st.session_state.ticker_val = clicked_ticker
                st.session_state.ticker_input_key = clicked_ticker
                st.session_state.run_analysis = True
                
                # 1_ZION_Analyzer.py 페이지로 이동
                st.switch_page("pages/1_ZION_Analyzer.py")

    # 하단 시장 요약 메트릭
    st.write("---")
    st.subheader("📊 섹터별 동향 요약")
    
    gainers = df_heatmap[df_heatmap["Change"] > 0]
    losers = df_heatmap[df_heatmap["Change"] < 0]
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("상승 종목 수", f"{len(gainers)} 개")
    m2.metric("하락 종목 수", f"{len(losers)} 개")
    m3.metric("최대 상승 종목", f"{df_heatmap.loc[df_heatmap['Change'].idxmax()]['Name']} ({df_heatmap['Change'].max():+.2f}%)" if not df_heatmap.empty else "-")
    m4.metric("최대 하락 종목", f"{df_heatmap.loc[df_heatmap['Change'].idxmin()]['Name']} ({df_heatmap['Change'].min():+.2f}%)" if not df_heatmap.empty else "-")

else:
    st.error("히트맵 데이터를 구성하지 못했습니다.")
