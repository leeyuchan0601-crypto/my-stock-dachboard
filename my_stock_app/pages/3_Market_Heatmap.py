import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import os
from streamlit_plotly_events import plotly_events

# --- 1. 페이지 설정 및 아이콘 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Market Heatmap", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Market Heatmap", page_icon="🗺️", layout="wide")

# --- 2. Finviz 클래식(화이트) 테마 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #ffffff; }
    h1, h2, h3, p, span, label { color: #111111 !important; }
    div[data-testid="metric-container"] {
        background-color: #f5f5f7;
        border: 1px solid #e0e0e0;
        padding: 15px;
        border-radius: 8px;
    }
    div[data-testid="metric-container"] label, div[data-testid="metric-container"] div { color: #111111 !important; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 주식 데이터 리스트 (Finviz 표준 섹터 체계 + 종목 대폭 확충) ---
KOSPI_STOCKS = [
    # 반도체/IT
    {"ticker": "005930.KS", "name": "삼성전자", "sector": "반도체/IT", "weight": 350},
    {"ticker": "000660.KS", "name": "SK하이닉스", "sector": "반도체/IT", "weight": 140},
    {"ticker": "042700.KS", "name": "한미반도체", "sector": "반도체/IT", "weight": 20},
    {"ticker": "009150.KS", "name": "삼성전기", "sector": "반도체/IT", "weight": 18},
    {"ticker": "011070.KS", "name": "LG이노텍", "sector": "반도체/IT", "weight": 12},
    {"ticker": "018260.KS", "name": "삼성SDS", "sector": "반도체/IT", "weight": 15},
    {"ticker": "058470.KQ", "name": "리노공업", "sector": "반도체/IT", "weight": 8},
    {"ticker": "240810.KQ", "name": "원익IPS", "sector": "반도체/IT", "weight": 6},
    {"ticker": "036930.KQ", "name": "주성엔지니어링", "sector": "반도체/IT", "weight": 5},
    {"ticker": "403870.KQ", "name": "HPSP", "sector": "반도체/IT", "weight": 6},
    # 2차전지/화학/에너지
    {"ticker": "373220.KS", "name": "LG에너지솔루션", "sector": "2차전지/화학/에너지", "weight": 80},
    {"ticker": "006400.KS", "name": "삼성SDI", "sector": "2차전지/화학/에너지", "weight": 25},
    {"ticker": "005490.KS", "name": "POSCO홀딩스", "sector": "2차전지/화학/에너지", "weight": 32},
    {"ticker": "051910.KS", "name": "LG화학", "sector": "2차전지/화학/에너지", "weight": 22},
    {"ticker": "003670.KS", "name": "포스코퓨처엠", "sector": "2차전지/화학/에너지", "weight": 20},
    {"ticker": "096770.KS", "name": "SK이노베이션", "sector": "2차전지/화학/에너지", "weight": 15},
    {"ticker": "010950.KS", "name": "S-Oil", "sector": "2차전지/화학/에너지", "weight": 12},
    {"ticker": "066970.KQ", "name": "엘앤에프", "sector": "2차전지/화학/에너지", "weight": 7},
    {"ticker": "247540.KQ", "name": "에코프로비엠", "sector": "2차전지/화학/에너지", "weight": 9},
    {"ticker": "086520.KQ", "name": "에코프로", "sector": "2차전지/화학/에너지", "weight": 10},
    # 제약/바이오
    {"ticker": "207940.KS", "name": "삼성바이오로직스", "sector": "제약/바이오", "weight": 65},
    {"ticker": "068270.KS", "name": "셀트리온", "sector": "제약/바이오", "weight": 45},
    {"ticker": "000100.KS", "name": "유한양행", "sector": "제약/바이오", "weight": 15},
    {"ticker": "128940.KS", "name": "한미약품", "sector": "제약/바이오", "weight": 12},
    {"ticker": "326030.KS", "name": "SK바이오팜", "sector": "제약/바이오", "weight": 10},
    {"ticker": "196170.KQ", "name": "알테오젠", "sector": "제약/바이오", "weight": 9},
    {"ticker": "302440.KS", "name": "SK바이오사이언스", "sector": "제약/바이오", "weight": 7},
    # 자동차/모빌리티
    {"ticker": "005380.KS", "name": "현대차", "sector": "자동차/모빌리티", "weight": 55},
    {"ticker": "000270.KS", "name": "기아", "sector": "자동차/모빌리티", "weight": 50},
    {"ticker": "012330.KS", "name": "현대모비스", "sector": "자동차/모빌리티", "weight": 22},
    {"ticker": "204320.KS", "name": "HL만도", "sector": "자동차/모빌리티", "weight": 8},
    {"ticker": "011210.KS", "name": "현대위아", "sector": "자동차/모빌리티", "weight": 5},
    # 방산/조선/중공업
    {"ticker": "012450.KS", "name": "한화에어로스페이스", "sector": "방산/조선/중공업", "weight": 30},
    {"ticker": "064350.KS", "name": "현대로템", "sector": "방산/조선/중공업", "weight": 18},
    {"ticker": "079550.KS", "name": "LIG넥스원", "sector": "방산/조선/중공업", "weight": 15},
    {"ticker": "329180.KS", "name": "HD현대중공업", "sector": "방산/조선/중공업", "weight": 20},
    {"ticker": "042660.KS", "name": "한화오션", "sector": "방산/조선/중공업", "weight": 18},
    {"ticker": "010140.KS", "name": "삼성중공업", "sector": "방산/조선/중공업", "weight": 14},
    {"ticker": "034020.KS", "name": "두산에너빌리티", "sector": "방산/조선/중공업", "weight": 22},
    {"ticker": "047810.KS", "name": "한국항공우주", "sector": "방산/조선/중공업", "weight": 12},
    # 전력/전력기기
    {"ticker": "267260.KS", "name": "HD현대일렉트릭", "sector": "전력/전력기기", "weight": 25},
    {"ticker": "010120.KS", "name": "LS일렉트릭", "sector": "전력/전력기기", "weight": 18},
    {"ticker": "015760.KS", "name": "한국전력", "sector": "전력/전력기기", "weight": 16},
    {"ticker": "047050.KS", "name": "포스코인터내셔널", "sector": "전력/전력기기", "weight": 10},
    # 금융/지주
    {"ticker": "105560.KS", "name": "KB금융", "sector": "금융/지주", "weight": 35},
    {"ticker": "055550.KS", "name": "신한지주", "sector": "금융/지주", "weight": 30},
    {"ticker": "086790.KS", "name": "하나금융지주", "sector": "금융/지주", "weight": 20},
    {"ticker": "316140.KS", "name": "우리금융지주", "sector": "금융/지주", "weight": 16},
    {"ticker": "138040.KS", "name": "메리츠금융지주", "sector": "금융/지주", "weight": 18},
    {"ticker": "032830.KS", "name": "삼성생명", "sector": "금융/지주", "weight": 18},
    {"ticker": "000810.KS", "name": "삼성화재", "sector": "금융/지주", "weight": 16},
    {"ticker": "006800.KS", "name": "미래에셋증권", "sector": "금융/지주", "weight": 10},
    {"ticker": "323410.KS", "name": "카카오뱅크", "sector": "금융/지주", "weight": 12},
    # 플랫폼/통신
    {"ticker": "035420.KS", "name": "NAVER", "sector": "플랫폼/통신", "weight": 30},
    {"ticker": "035720.KS", "name": "카카오", "sector": "플랫폼/통신", "weight": 22},
    {"ticker": "017670.KS", "name": "SK텔레콤", "sector": "플랫폼/통신", "weight": 15},
    {"ticker": "030200.KS", "name": "KT", "sector": "플랫폼/통신", "weight": 14},
    {"ticker": "032640.KS", "name": "LG유플러스", "sector": "플랫폼/통신", "weight": 8},
    # 소비재/유통/뷰티
    {"ticker": "090430.KS", "name": "아모레퍼시픽", "sector": "소비재/유통/뷰티", "weight": 14},
    {"ticker": "051900.KS", "name": "LG생활건강", "sector": "소비재/유통/뷰티", "weight": 12},
    {"ticker": "033780.KS", "name": "KT&G", "sector": "소비재/유통/뷰티", "weight": 18},
    {"ticker": "097950.KS", "name": "CJ제일제당", "sector": "소비재/유통/뷰티", "weight": 10},
    {"ticker": "023530.KS", "name": "롯데쇼핑", "sector": "소비재/유통/뷰티", "weight": 6},
    {"ticker": "004170.KS", "name": "신세계", "sector": "소비재/유통/뷰티", "weight": 6},
    # 철강/건설/인프라
    {"ticker": "010130.KS", "name": "고려아연", "sector": "철강/건설/인프라", "weight": 20},
    {"ticker": "004020.KS", "name": "현대제철", "sector": "철강/건설/인프라", "weight": 10},
    {"ticker": "028260.KS", "name": "삼성물산", "sector": "철강/건설/인프라", "weight": 25},
    {"ticker": "000720.KS", "name": "현대건설", "sector": "철강/건설/인프라", "weight": 8},
]

US_MARKET_DATA = [
    # Electronic Technology
    {"ticker": "AAPL", "name": "AAPL", "sector": "Electronic Technology", "weight": 340},
    {"ticker": "NVDA", "name": "NVDA", "sector": "Electronic Technology", "weight": 310},
    {"ticker": "AVGO", "name": "AVGO", "sector": "Electronic Technology", "weight": 90},
    {"ticker": "CSCO", "name": "CSCO", "sector": "Electronic Technology", "weight": 28},
    {"ticker": "TXN", "name": "TXN", "sector": "Electronic Technology", "weight": 22},
    {"ticker": "INTC", "name": "INTC", "sector": "Electronic Technology", "weight": 14},
    {"ticker": "QCOM", "name": "QCOM", "sector": "Electronic Technology", "weight": 26},
    {"ticker": "MU", "name": "MU", "sector": "Electronic Technology", "weight": 18},
    {"ticker": "ADI", "name": "ADI", "sector": "Electronic Technology", "weight": 16},
    {"ticker": "AMAT", "name": "AMAT", "sector": "Electronic Technology", "weight": 22},
    {"ticker": "LRCX", "name": "LRCX", "sector": "Electronic Technology", "weight": 18},
    {"ticker": "KLAC", "name": "KLAC", "sector": "Electronic Technology", "weight": 16},
    {"ticker": "DELL", "name": "DELL", "sector": "Electronic Technology", "weight": 10},
    {"ticker": "HPQ", "name": "HPQ", "sector": "Electronic Technology", "weight": 8},
    {"ticker": "WDC", "name": "WDC", "sector": "Electronic Technology", "weight": 7},
    {"ticker": "STX", "name": "STX", "sector": "Electronic Technology", "weight": 7},
    {"ticker": "MCHP", "name": "MCHP", "sector": "Electronic Technology", "weight": 6},
    {"ticker": "ON", "name": "ON", "sector": "Electronic Technology", "weight": 6},
    {"ticker": "SWKS", "name": "SWKS", "sector": "Electronic Technology", "weight": 5},
    {"ticker": "GLW", "name": "GLW", "sector": "Electronic Technology", "weight": 6},
    {"ticker": "TER", "name": "TER", "sector": "Electronic Technology", "weight": 5},
    {"ticker": "APH", "name": "APH", "sector": "Electronic Technology", "weight": 8},
    {"ticker": "TEL", "name": "TEL", "sector": "Electronic Technology", "weight": 7},
    {"ticker": "KEYS", "name": "KEYS", "sector": "Electronic Technology", "weight": 5},
    # Technology Services
    {"ticker": "MSFT", "name": "MSFT", "sector": "Technology Services", "weight": 320},
    {"ticker": "META", "name": "META", "sector": "Technology Services", "weight": 150},
    {"ticker": "ORCL", "name": "ORCL", "sector": "Technology Services", "weight": 55},
    {"ticker": "GOOGL", "name": "GOOGL", "sector": "Technology Services", "weight": 220},
    {"ticker": "ACN", "name": "ACN", "sector": "Technology Services", "weight": 24},
    {"ticker": "CRM", "name": "CRM", "sector": "Technology Services", "weight": 32},
    {"ticker": "ADBE", "name": "ADBE", "sector": "Technology Services", "weight": 24},
    {"ticker": "NFLX", "name": "NFLX", "sector": "Technology Services", "weight": 40},
    {"ticker": "ADP", "name": "ADP", "sector": "Technology Services", "weight": 14},
    {"ticker": "NOW", "name": "NOW", "sector": "Technology Services", "weight": 22},
    {"ticker": "IBM", "name": "IBM", "sector": "Technology Services", "weight": 26},
    {"ticker": "SNPS", "name": "SNPS", "sector": "Technology Services", "weight": 14},
    {"ticker": "CDNS", "name": "CDNS", "sector": "Technology Services", "weight": 14},
    {"ticker": "INTU", "name": "INTU", "sector": "Technology Services", "weight": 20},
    {"ticker": "PANW", "name": "PANW", "sector": "Technology Services", "weight": 18},
    {"ticker": "CRWD", "name": "CRWD", "sector": "Technology Services", "weight": 16},
    {"ticker": "FTNT", "name": "FTNT", "sector": "Technology Services", "weight": 12},
    {"ticker": "SHOP", "name": "SHOP", "sector": "Technology Services", "weight": 18},
    {"ticker": "UBER", "name": "UBER", "sector": "Technology Services", "weight": 22},
    {"ticker": "PYPL", "name": "PYPL", "sector": "Technology Services", "weight": 12},
    {"ticker": "EA", "name": "EA", "sector": "Technology Services", "weight": 8},
    {"ticker": "TTWO", "name": "TTWO", "sector": "Technology Services", "weight": 7},
    # Finance
    {"ticker": "BRK-B", "name": "BRK.B", "sector": "Finance", "weight": 95},
    {"ticker": "JPM", "name": "JPM", "sector": "Finance", "weight": 65},
    {"ticker": "BAC", "name": "BAC", "sector": "Finance", "weight": 32},
    {"ticker": "WFC", "name": "WFC", "sector": "Finance", "weight": 26},
    {"ticker": "GS", "name": "GS", "sector": "Finance", "weight": 20},
    {"ticker": "MS", "name": "MS", "sector": "Finance", "weight": 20},
    {"ticker": "C", "name": "C", "sector": "Finance", "weight": 18},
    {"ticker": "SCHW", "name": "SCHW", "sector": "Finance", "weight": 18},
    {"ticker": "AXP", "name": "AXP", "sector": "Finance", "weight": 24},
    {"ticker": "BLK", "name": "BLK", "sector": "Finance", "weight": 22},
    {"ticker": "SPGI", "name": "SPGI", "sector": "Finance", "weight": 22},
    {"ticker": "COF", "name": "COF", "sector": "Finance", "weight": 12},
    {"ticker": "USB", "name": "USB", "sector": "Finance", "weight": 10},
    {"ticker": "PNC", "name": "PNC", "sector": "Finance", "weight": 9},
    {"ticker": "TFC", "name": "TFC", "sector": "Finance", "weight": 8},
    {"ticker": "CME", "name": "CME", "sector": "Finance", "weight": 12},
    {"ticker": "ICE", "name": "ICE", "sector": "Finance", "weight": 10},
    {"ticker": "MET", "name": "MET", "sector": "Finance", "weight": 8},
    {"ticker": "PRU", "name": "PRU", "sector": "Finance", "weight": 7},
    {"ticker": "AIG", "name": "AIG", "sector": "Finance", "weight": 7},
    {"ticker": "PGR", "name": "PGR", "sector": "Finance", "weight": 20},
    {"ticker": "CB", "name": "CB", "sector": "Finance", "weight": 16},
    {"ticker": "KKR", "name": "KKR", "sector": "Finance", "weight": 20},
    {"ticker": "BX", "name": "BX", "sector": "Finance", "weight": 28},
    # Health Technology
    {"ticker": "LLY", "name": "LLY", "sector": "Health Technology", "weight": 85},
    {"ticker": "JNJ", "name": "JNJ", "sector": "Health Technology", "weight": 40},
    {"ticker": "ABBV", "name": "ABBV", "sector": "Health Technology", "weight": 35},
    {"ticker": "MRK", "name": "MRK", "sector": "Health Technology", "weight": 30},
    {"ticker": "PFE", "name": "PFE", "sector": "Health Technology", "weight": 18},
    {"ticker": "DHR", "name": "DHR", "sector": "Health Technology", "weight": 22},
    {"ticker": "TMO", "name": "TMO", "sector": "Health Technology", "weight": 26},
    {"ticker": "ABT", "name": "ABT", "sector": "Health Technology", "weight": 24},
    {"ticker": "MDT", "name": "MDT", "sector": "Health Technology", "weight": 16},
    {"ticker": "SYK", "name": "SYK", "sector": "Health Technology", "weight": 18},
    {"ticker": "BSX", "name": "BSX", "sector": "Health Technology", "weight": 20},
    {"ticker": "ISRG", "name": "ISRG", "sector": "Health Technology", "weight": 25},
    {"ticker": "GILD", "name": "GILD", "sector": "Health Technology", "weight": 16},
    {"ticker": "AMGN", "name": "AMGN", "sector": "Health Technology", "weight": 15},
    {"ticker": "BMY", "name": "BMY", "sector": "Health Technology", "weight": 12},
    {"ticker": "ZTS", "name": "ZTS", "sector": "Health Technology", "weight": 10},
    {"ticker": "REGN", "name": "REGN", "sector": "Health Technology", "weight": 10},
    {"ticker": "VRTX", "name": "VRTX", "sector": "Health Technology", "weight": 12},
    {"ticker": "BDX", "name": "BDX", "sector": "Health Technology", "weight": 8},
    # Retail Trade
    {"ticker": "AMZN", "name": "AMZN", "sector": "Retail Trade", "weight": 200},
    {"ticker": "WMT", "name": "WMT", "sector": "Retail Trade", "weight": 60},
    {"ticker": "COST", "name": "COST", "sector": "Retail Trade", "weight": 45},
    {"ticker": "HD", "name": "HD", "sector": "Retail Trade", "weight": 42},
    {"ticker": "LOW", "name": "LOW", "sector": "Retail Trade", "weight": 20},
    {"ticker": "TGT", "name": "TGT", "sector": "Retail Trade", "weight": 12},
    {"ticker": "TJX", "name": "TJX", "sector": "Retail Trade", "weight": 18},
    {"ticker": "DG", "name": "DG", "sector": "Retail Trade", "weight": 5},
    {"ticker": "DLTR", "name": "DLTR", "sector": "Retail Trade", "weight": 5},
    {"ticker": "ROST", "name": "ROST", "sector": "Retail Trade", "weight": 8},
    {"ticker": "KR", "name": "KR", "sector": "Retail Trade", "weight": 7},
    {"ticker": "BBY", "name": "BBY", "sector": "Retail Trade", "weight": 5},
    {"ticker": "ORLY", "name": "ORLY", "sector": "Retail Trade", "weight": 10},
    {"ticker": "AZO", "name": "AZO", "sector": "Retail Trade", "weight": 9},
    # Consumer Non-Durables
    {"ticker": "PG", "name": "PG", "sector": "Consumer Non-Durables", "weight": 45},
    {"ticker": "KO", "name": "KO", "sector": "Consumer Non-Durables", "weight": 30},
    {"ticker": "PEP", "name": "PEP", "sector": "Consumer Non-Durables", "weight": 26},
    {"ticker": "PM", "name": "PM", "sector": "Consumer Non-Durables", "weight": 22},
    {"ticker": "MO", "name": "MO", "sector": "Consumer Non-Durables", "weight": 14},
    {"ticker": "NKE", "name": "NKE", "sector": "Consumer Non-Durables", "weight": 16},
    {"ticker": "MDLZ", "name": "MDLZ", "sector": "Consumer Non-Durables", "weight": 15},
    {"ticker": "CL", "name": "CL", "sector": "Consumer Non-Durables", "weight": 12},
    {"ticker": "KMB", "name": "KMB", "sector": "Consumer Non-Durables", "weight": 8},
    {"ticker": "STZ", "name": "STZ", "sector": "Consumer Non-Durables", "weight": 6},
    {"ticker": "EL", "name": "EL", "sector": "Consumer Non-Durables", "weight": 5},
    {"ticker": "KHC", "name": "KHC", "sector": "Consumer Non-Durables", "weight": 6},
    {"ticker": "GIS", "name": "GIS", "sector": "Consumer Non-Durables", "weight": 6},
    {"ticker": "MNST", "name": "MNST", "sector": "Consumer Non-Durables", "weight": 10},
    # Energy Minerals
    {"ticker": "XOM", "name": "XOM", "sector": "Energy Minerals", "weight": 55},
    {"ticker": "CVX", "name": "CVX", "sector": "Energy Minerals", "weight": 32},
    {"ticker": "COP", "name": "COP", "sector": "Energy Minerals", "weight": 18},
    {"ticker": "EOG", "name": "EOG", "sector": "Energy Minerals", "weight": 10},
    {"ticker": "PSX", "name": "PSX", "sector": "Energy Minerals", "weight": 7},
    {"ticker": "MPC", "name": "MPC", "sector": "Energy Minerals", "weight": 7},
    {"ticker": "VLO", "name": "VLO", "sector": "Energy Minerals", "weight": 6},
    {"ticker": "OXY", "name": "OXY", "sector": "Energy Minerals", "weight": 6},
    {"ticker": "WMB", "name": "WMB", "sector": "Energy Minerals", "weight": 8},
    {"ticker": "KMI", "name": "KMI", "sector": "Energy Minerals", "weight": 7},
    {"ticker": "SLB", "name": "SLB", "sector": "Energy Minerals", "weight": 14},
    # Producer Manufacturing
    {"ticker": "CAT", "name": "CAT", "sector": "Producer Manufacturing", "weight": 24},
    {"ticker": "DE", "name": "DE", "sector": "Producer Manufacturing", "weight": 18},
    {"ticker": "HON", "name": "HON", "sector": "Producer Manufacturing", "weight": 18},
    {"ticker": "ETN", "name": "ETN", "sector": "Producer Manufacturing", "weight": 22},
    {"ticker": "GE", "name": "GE", "sector": "Producer Manufacturing", "weight": 24},
    {"ticker": "EMR", "name": "EMR", "sector": "Producer Manufacturing", "weight": 8},
    {"ticker": "ITW", "name": "ITW", "sector": "Producer Manufacturing", "weight": 8},
    {"ticker": "PH", "name": "PH", "sector": "Producer Manufacturing", "weight": 7},
    {"ticker": "ROK", "name": "ROK", "sector": "Producer Manufacturing", "weight": 5},
    {"ticker": "CMI", "name": "CMI", "sector": "Producer Manufacturing", "weight": 6},
    # Utilities
    {"ticker": "NEE", "name": "NEE", "sector": "Utilities", "weight": 20},
    {"ticker": "DUK", "name": "DUK", "sector": "Utilities", "weight": 12},
    {"ticker": "SO", "name": "SO", "sector": "Utilities", "weight": 12},
    {"ticker": "D", "name": "D", "sector": "Utilities", "weight": 8},
    {"ticker": "AEP", "name": "AEP", "sector": "Utilities", "weight": 8},
    {"ticker": "EXC", "name": "EXC", "sector": "Utilities", "weight": 6},
    {"ticker": "XEL", "name": "XEL", "sector": "Utilities", "weight": 6},
    {"ticker": "ED", "name": "ED", "sector": "Utilities", "weight": 5},
    {"ticker": "PEG", "name": "PEG", "sector": "Utilities", "weight": 6},
    # Health Services
    {"ticker": "UNH", "name": "UNH", "sector": "Health Services", "weight": 55},
    {"ticker": "CVS", "name": "CVS", "sector": "Health Services", "weight": 14},
    {"ticker": "CI", "name": "CI", "sector": "Health Services", "weight": 16},
    {"ticker": "HUM", "name": "HUM", "sector": "Health Services", "weight": 8},
    {"ticker": "ELV", "name": "ELV", "sector": "Health Services", "weight": 10},
    {"ticker": "CNC", "name": "CNC", "sector": "Health Services", "weight": 5},
    # Process Industries
    {"ticker": "LIN", "name": "LIN", "sector": "Process Industries", "weight": 25},
    {"ticker": "SHW", "name": "SHW", "sector": "Process Industries", "weight": 14},
    {"ticker": "ECL", "name": "ECL", "sector": "Process Industries", "weight": 8},
    {"ticker": "APD", "name": "APD", "sector": "Process Industries", "weight": 7},
    {"ticker": "DD", "name": "DD", "sector": "Process Industries", "weight": 6},
    {"ticker": "DOW", "name": "DOW", "sector": "Process Industries", "weight": 6},
    {"ticker": "PPG", "name": "PPG", "sector": "Process Industries", "weight": 5},
    # Transportation
    {"ticker": "UPS", "name": "UPS", "sector": "Transportation", "weight": 12},
    {"ticker": "FDX", "name": "FDX", "sector": "Transportation", "weight": 10},
    {"ticker": "UNP", "name": "UNP", "sector": "Transportation", "weight": 20},
    {"ticker": "CSX", "name": "CSX", "sector": "Transportation", "weight": 9},
    {"ticker": "NSC", "name": "NSC", "sector": "Transportation", "weight": 8},
    {"ticker": "DAL", "name": "DAL", "sector": "Transportation", "weight": 6},
    {"ticker": "UAL", "name": "UAL", "sector": "Transportation", "weight": 5},
    {"ticker": "LUV", "name": "LUV", "sector": "Transportation", "weight": 4},
    # Consumer Services
    {"ticker": "MCD", "name": "MCD", "sector": "Consumer Services", "weight": 26},
    {"ticker": "SBUX", "name": "SBUX", "sector": "Consumer Services", "weight": 16},
    {"ticker": "BKNG", "name": "BKNG", "sector": "Consumer Services", "weight": 22},
    {"ticker": "ABNB", "name": "ABNB", "sector": "Consumer Services", "weight": 14},
    {"ticker": "DIS", "name": "DIS", "sector": "Consumer Services", "weight": 22},
    {"ticker": "MAR", "name": "MAR", "sector": "Consumer Services", "weight": 8},
    {"ticker": "HLT", "name": "HLT", "sector": "Consumer Services", "weight": 8},
    {"ticker": "YUM", "name": "YUM", "sector": "Consumer Services", "weight": 6},
    # Commercial Services
    {"ticker": "V", "name": "V", "sector": "Commercial Services", "weight": 60},
    {"ticker": "MA", "name": "MA", "sector": "Commercial Services", "weight": 50},
    {"ticker": "FIS", "name": "FIS", "sector": "Commercial Services", "weight": 6},
    {"ticker": "PAYX", "name": "PAYX", "sector": "Commercial Services", "weight": 6},
    {"ticker": "VRSK", "name": "VRSK", "sector": "Commercial Services", "weight": 5},
    {"ticker": "CTAS", "name": "CTAS", "sector": "Commercial Services", "weight": 6},
    {"ticker": "WM", "name": "WM", "sector": "Commercial Services", "weight": 8},
    {"ticker": "RSG", "name": "RSG", "sector": "Commercial Services", "weight": 7},
    # Consumer Durables
    {"ticker": "TSLA", "name": "TSLA", "sector": "Consumer Durables", "weight": 85},
    {"ticker": "F", "name": "F", "sector": "Consumer Durables", "weight": 12},
    {"ticker": "GM", "name": "GM", "sector": "Consumer Durables", "weight": 12},
    {"ticker": "TM", "name": "TM", "sector": "Consumer Durables", "weight": 30},
    {"ticker": "RACE", "name": "RACE", "sector": "Consumer Durables", "weight": 15},
    {"ticker": "WHR", "name": "WHR", "sector": "Consumer Durables", "weight": 3},
    {"ticker": "NVR", "name": "NVR", "sector": "Consumer Durables", "weight": 5},
    {"ticker": "PHM", "name": "PHM", "sector": "Consumer Durables", "weight": 5},
    {"ticker": "DHI", "name": "DHI", "sector": "Consumer Durables", "weight": 6},
    # Communications
    {"ticker": "T", "name": "T", "sector": "Communications", "weight": 18},
    {"ticker": "VZ", "name": "VZ", "sector": "Communications", "weight": 20},
    {"ticker": "TMUS", "name": "TMUS", "sector": "Communications", "weight": 24},
    {"ticker": "CMCSA", "name": "CMCSA", "sector": "Communications", "weight": 16},
    # Industrial Services
    {"ticker": "HAL", "name": "HAL", "sector": "Industrial Services", "weight": 6},
    {"ticker": "BKR", "name": "BKR", "sector": "Industrial Services", "weight": 5},
    {"ticker": "URI", "name": "URI", "sector": "Industrial Services", "weight": 6},
    {"ticker": "FAST", "name": "FAST", "sector": "Industrial Services", "weight": 5},
    {"ticker": "GWW", "name": "GWW", "sector": "Industrial Services", "weight": 5},
    {"ticker": "JCI", "name": "JCI", "sector": "Industrial Services", "weight": 6},
    # Distribution Services
    {"ticker": "SYY", "name": "SYY", "sector": "Distribution Services", "weight": 5},
    {"ticker": "MCK", "name": "MCK", "sector": "Distribution Services", "weight": 7},
    {"ticker": "COR", "name": "COR", "sector": "Distribution Services", "weight": 6},
    {"ticker": "CDW", "name": "CDW", "sector": "Distribution Services", "weight": 4},
    # Non-Energy Minerals
    {"ticker": "NEM", "name": "NEM", "sector": "Non-Energy Minerals", "weight": 12},
    {"ticker": "FCX", "name": "FCX", "sector": "Non-Energy Minerals", "weight": 12},
    {"ticker": "AA", "name": "AA", "sector": "Non-Energy Minerals", "weight": 4},
    {"ticker": "X", "name": "X", "sector": "Non-Energy Minerals", "weight": 3},
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

# --- 5. Finviz 스타일 컬러 매핑 (연속 그라데이션이 아닌 '등급형' 배색) ---
def get_finviz_color(pct: float) -> str:
    """등락률을 Finviz 클래식 팔레트(딥레드~그레이~딥그린)의 등급 색상으로 변환."""
    if pct <= -3:
        return "#a50e0e"
    elif pct <= -2:
        return "#c9302c"
    elif pct <= -1:
        return "#e0605c"
    elif pct <= -0.3:
        return "#f0928f"
    elif pct < 0.3:
        return "#d5d5d5"  # 보합 구간은 회색 (예: AAPL +0.33%처럼 살짝 움직여도 그레이 처리하려면 임계값 조정)
    elif pct < 1:
        return "#8fce9e"
    elif pct < 2:
        return "#4caf6e"
    elif pct < 3:
        return "#2e8b4f"
    else:
        return "#1a6b35"


def build_finviz_treemap(df: pd.DataFrame) -> go.Figure:
    ids, labels, parents, values, colors, customdata = [], [], [], [], [], []

    # 섹터(부모) 노드 - 헤더처럼 흰 배경 + 검은 글씨로 고정
    sector_totals = df.groupby("Sector")["Weight"].sum().to_dict()

    # 루트: branchvalues="total" 사용 시 부모 값 = 자식 값의 합이어야 렌더링됨 (0으로 두면 트리맵이 빈 화면으로 나옴)
    ids.append("root")
    labels.append("")
    parents.append("")
    values.append(sum(sector_totals.values()))
    colors.append("#ffffff")
    customdata.append(["", "", ""])

    for sector, total_w in sector_totals.items():
        ids.append(sector)
        labels.append(f"{sector} ›")
        parents.append("root")
        values.append(total_w)
        colors.append("#ffffff")
        customdata.append(["", "", ""])

    # 종목(리프) 노드 - 등락률에 따른 등급 색상
    for _, row in df.iterrows():
        ids.append(row["Ticker"])
        labels.append(f"<b>{row['Ticker']}</b><br>{row['ChangeText']}")
        parents.append(row["Sector"])
        values.append(max(row["Weight"], 0.1))
        colors.append(get_finviz_color(row["Change"]))
        customdata.append([row["Name"], row["ChangeText"], row["Ticker"]])

    fig = go.Figure(go.Treemap(
        ids=ids,
        labels=labels,
        parents=parents,
        values=values,
        branchvalues="total",
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        customdata=customdata,
        texttemplate="%{label}",
        textfont=dict(color="#111111", family="Arial, Helvetica, sans-serif"),
        hovertemplate="<b>%{customdata[0]}</b> (%{customdata[2]})<br>변동률: %{customdata[1]}<extra></extra>",
        pathbar=dict(visible=False),
        tiling=dict(pad=2),
    ))

    fig.update_layout(
        template="plotly_white",
        paper_bgcolor="#ffffff",
        plot_bgcolor="#ffffff",
        height=850,
        margin=dict(l=0, r=0, t=10, b=0),
    )
    return fig


# --- 6. UI 및 대시보드 렌더링 ---
st.title("🛰️ ZION : MARKET MAP TERMINAL")
st.write("시가총액 규모 및 당일 등락률을 트리맵 형태로 시각화합니다. (Finviz 클래식 스타일)")
st.write("---")

col_market, _ = st.columns([2, 3])
with col_market:
    selected_market = st.radio("분석 시장 선택", ["대한민국 KOSPI 주요 종목", "미국 S&P 500 빅테크"], horizontal=True)

target_dataset = KOSPI_STOCKS if "KOSPI" in selected_market else US_MARKET_DATA

with st.spinner("📡 시장 데이터 수집 및 비주얼 매핑 중..."):
    df_heatmap = fetch_heatmap_data(target_dataset)

if not df_heatmap.empty:
    df_heatmap["Weight"] = pd.to_numeric(df_heatmap["Weight"])

    fig = build_finviz_treemap(df_heatmap)

    # ---------------------------------------------------------
    # 🚀 [클릭 로직] plotly_events를 써서 클릭 신호 수신
    # ---------------------------------------------------------
    clicked_data = plotly_events(
        fig,
        click_event=True,
        hover_event=False,
        select_event=False,
        override_height=850,
        key="treemap_click"
    )

    if clicked_data:
        try:
            point_index = clicked_data[0].get("pointNumber")
            if point_index is not None:
                clicked_ticker = fig.data[0].customdata[point_index][2]
                if clicked_ticker and str(clicked_ticker) not in ["(?)", "None", ""]:
                    st.session_state.ticker_val = clicked_ticker
                    st.session_state.ticker_input_key = clicked_ticker
                    st.session_state.run_analysis = True
                    st.switch_page("pages/1_ZION_Analyzer.py")
        except Exception as e:
            st.error(f"클릭 처리 중 오류: {e}")

    # ---------------------------------------------------------
    # 하단 시장 요약 메트릭
    # ---------------------------------------------------------
    st.write("---")
    st.subheader("📊 섹터별 동향 요약")

    gainers = df_heatmap[df_heatmap["Change"] > 0]
    losers = df_heatmap[df_heatmap["Change"] < 0]

    m1, m2, m3, m4 = st.columns(4)
    m1.metric("상승 종목 수", f"{len(gainers)} 개")
    m2.metric("하락 종목 수", f"{len(losers)} 개")

    max_gainer = df_heatmap.loc[df_heatmap['Change'].idxmax()] if not gainers.empty else None
    min_loser = df_heatmap.loc[df_heatmap['Change'].idxmin()] if not losers.empty else None

    m3.metric("최대 상승 종목", f"{max_gainer['Name']} ({max_gainer['Change']:+.2f}%)" if max_gainer is not None else "-")
    m4.metric("최대 하락 종목", f"{min_loser['Name']} ({min_loser['Change']:+.2f}%)" if min_loser is not None else "-")

else:
    st.error("히트맵 데이터를 구성하지 못했습니다.")
