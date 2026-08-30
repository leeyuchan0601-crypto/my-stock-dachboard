import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import os
import sys
from streamlit_plotly_events import plotly_events

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import theme
import db
from auth import require_login, ensure_user
from data_source import smart_cache_ttl, download_with_retry

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Market Heatmap", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Market Heatmap", page_icon="Z", layout="wide")

theme.inject_base_css()
require_login()
USER_ID = ensure_user()

st.markdown("""
    <style>
    .legend-wrap {
        display: flex; align-items: center; gap: 18px; flex-wrap: wrap;
        background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;
        padding: 10px 16px; margin-bottom: 14px;
    }
    .legend-item { display: flex; align-items: center; gap: 6px; font-size: 13px; color: #334155; font-weight: 600; }
    .legend-swatch { width: 14px; height: 14px; border-radius: 3px; display: inline-block; }
    </style>
    """, unsafe_allow_html=True)

# --- 주식 데이터 리스트 (Finviz 표준 섹터 체계) ---
KOSPI_STOCKS = [
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
    {"ticker": "207940.KS", "name": "삼성바이오로직스", "sector": "제약/바이오", "weight": 65},
    {"ticker": "068270.KS", "name": "셀트리온", "sector": "제약/바이오", "weight": 45},
    {"ticker": "000100.KS", "name": "유한양행", "sector": "제약/바이오", "weight": 15},
    {"ticker": "128940.KS", "name": "한미약품", "sector": "제약/바이오", "weight": 12},
    {"ticker": "326030.KS", "name": "SK바이오팜", "sector": "제약/바이오", "weight": 10},
    {"ticker": "196170.KQ", "name": "알테오젠", "sector": "제약/바이오", "weight": 9},
    {"ticker": "302440.KS", "name": "SK바이오사이언스", "sector": "제약/바이오", "weight": 7},
    {"ticker": "005380.KS", "name": "현대차", "sector": "자동차/모빌리티", "weight": 55},
    {"ticker": "000270.KS", "name": "기아", "sector": "자동차/모빌리티", "weight": 50},
    {"ticker": "012330.KS", "name": "현대모비스", "sector": "자동차/모빌리티", "weight": 22},
    {"ticker": "204320.KS", "name": "HL만도", "sector": "자동차/모빌리티", "weight": 8},
    {"ticker": "011210.KS", "name": "현대위아", "sector": "자동차/모빌리티", "weight": 5},
    {"ticker": "012450.KS", "name": "한화에어로스페이스", "sector": "방산/조선/중공업", "weight": 30},
    {"ticker": "064350.KS", "name": "현대로템", "sector": "방산/조선/중공업", "weight": 18},
    {"ticker": "079550.KS", "name": "LIG넥스원", "sector": "방산/조선/중공업", "weight": 15},
    {"ticker": "329180.KS", "name": "HD현대중공업", "sector": "방산/조선/중공업", "weight": 20},
    {"ticker": "042660.KS", "name": "한화오션", "sector": "방산/조선/중공업", "weight": 18},
    {"ticker": "010140.KS", "name": "삼성중공업", "sector": "방산/조선/중공업", "weight": 14},
    {"ticker": "034020.KS", "name": "두산에너빌리티", "sector": "방산/조선/중공업", "weight": 22},
    {"ticker": "047810.KS", "name": "한국항공우주", "sector": "방산/조선/중공업", "weight": 12},
    {"ticker": "267260.KS", "name": "HD현대일렉트릭", "sector": "전력/전력기기", "weight": 25},
    {"ticker": "010120.KS", "name": "LS일렉트릭", "sector": "전력/전력기기", "weight": 18},
    {"ticker": "015760.KS", "name": "한국전력", "sector": "전력/전력기기", "weight": 16},
    {"ticker": "047050.KS", "name": "포스코인터내셔널", "sector": "전력/전력기기", "weight": 10},
    {"ticker": "105560.KS", "name": "KB금융", "sector": "금융/지주", "weight": 35},
    {"ticker": "055550.KS", "name": "신한지주", "sector": "금융/지주", "weight": 30},
    {"ticker": "086790.KS", "name": "하나금융지주", "sector": "금융/지주", "weight": 20},
    {"ticker": "316140.KS", "name": "우리금융지주", "sector": "금융/지주", "weight": 16},
    {"ticker": "138040.KS", "name": "메리츠금융지주", "sector": "금융/지주", "weight": 18},
    {"ticker": "032830.KS", "name": "삼성생명", "sector": "금융/지주", "weight": 18},
    {"ticker": "000810.KS", "name": "삼성화재", "sector": "금융/지주", "weight": 16},
    {"ticker": "006800.KS", "name": "미래에셋증권", "sector": "금융/지주", "weight": 10},
    {"ticker": "323410.KS", "name": "카카오뱅크", "sector": "금융/지주", "weight": 12},
    {"ticker": "035420.KS", "name": "NAVER", "sector": "플랫폼/통신", "weight": 30},
    {"ticker": "035720.KS", "name": "카카오", "sector": "플랫폼/통신", "weight": 22},
    {"ticker": "017670.KS", "name": "SK텔레콤", "sector": "플랫폼/통신", "weight": 15},
    {"ticker": "030200.KS", "name": "KT", "sector": "플랫폼/통신", "weight": 14},
    {"ticker": "032640.KS", "name": "LG유플러스", "sector": "플랫폼/통신", "weight": 8},
    {"ticker": "090430.KS", "name": "아모레퍼시픽", "sector": "소비재/유통/뷰티", "weight": 14},
    {"ticker": "051900.KS", "name": "LG생활건강", "sector": "소비재/유통/뷰티", "weight": 12},
    {"ticker": "033780.KS", "name": "KT&G", "sector": "소비재/유통/뷰티", "weight": 18},
    {"ticker": "097950.KS", "name": "CJ제일제당", "sector": "소비재/유통/뷰티", "weight": 10},
    {"ticker": "023530.KS", "name": "롯데쇼핑", "sector": "소비재/유통/뷰티", "weight": 6},
    {"ticker": "004170.KS", "name": "신세계", "sector": "소비재/유통/뷰티", "weight": 6},
    {"ticker": "010130.KS", "name": "고려아연", "sector": "철강/건설/인프라", "weight": 20},
    {"ticker": "004020.KS", "name": "현대제철", "sector": "철강/건설/인프라", "weight": 10},
    {"ticker": "028260.KS", "name": "삼성물산", "sector": "철강/건설/인프라", "weight": 25},
    {"ticker": "000720.KS", "name": "현대건설", "sector": "철강/건설/인프라", "weight": 8},
]

US_MARKET_DATA = [
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
    {"ticker": "NEE", "name": "NEE", "sector": "Utilities", "weight": 20},
    {"ticker": "DUK", "name": "DUK", "sector": "Utilities", "weight": 12},
    {"ticker": "SO", "name": "SO", "sector": "Utilities", "weight": 12},
    {"ticker": "D", "name": "D", "sector": "Utilities", "weight": 8},
    {"ticker": "AEP", "name": "AEP", "sector": "Utilities", "weight": 8},
    {"ticker": "EXC", "name": "EXC", "sector": "Utilities", "weight": 6},
    {"ticker": "XEL", "name": "XEL", "sector": "Utilities", "weight": 6},
    {"ticker": "ED", "name": "ED", "sector": "Utilities", "weight": 5},
    {"ticker": "PEG", "name": "PEG", "sector": "Utilities", "weight": 6},
    {"ticker": "UNH", "name": "UNH", "sector": "Health Services", "weight": 55},
    {"ticker": "CVS", "name": "CVS", "sector": "Health Services", "weight": 14},
    {"ticker": "CI", "name": "CI", "sector": "Health Services", "weight": 16},
    {"ticker": "HUM", "name": "HUM", "sector": "Health Services", "weight": 8},
    {"ticker": "ELV", "name": "ELV", "sector": "Health Services", "weight": 10},
    {"ticker": "CNC", "name": "CNC", "sector": "Health Services", "weight": 5},
    {"ticker": "LIN", "name": "LIN", "sector": "Process Industries", "weight": 25},
    {"ticker": "SHW", "name": "SHW", "sector": "Process Industries", "weight": 14},
    {"ticker": "ECL", "name": "ECL", "sector": "Process Industries", "weight": 8},
    {"ticker": "APD", "name": "APD", "sector": "Process Industries", "weight": 7},
    {"ticker": "DD", "name": "DD", "sector": "Process Industries", "weight": 6},
    {"ticker": "DOW", "name": "DOW", "sector": "Process Industries", "weight": 6},
    {"ticker": "PPG", "name": "PPG", "sector": "Process Industries", "weight": 5},
    {"ticker": "UPS", "name": "UPS", "sector": "Transportation", "weight": 12},
    {"ticker": "FDX", "name": "FDX", "sector": "Transportation", "weight": 10},
    {"ticker": "UNP", "name": "UNP", "sector": "Transportation", "weight": 20},
    {"ticker": "CSX", "name": "CSX", "sector": "Transportation", "weight": 9},
    {"ticker": "NSC", "name": "NSC", "sector": "Transportation", "weight": 8},
    {"ticker": "DAL", "name": "DAL", "sector": "Transportation", "weight": 6},
    {"ticker": "UAL", "name": "UAL", "sector": "Transportation", "weight": 5},
    {"ticker": "LUV", "name": "LUV", "sector": "Transportation", "weight": 4},
    {"ticker": "MCD", "name": "MCD", "sector": "Consumer Services", "weight": 26},
    {"ticker": "SBUX", "name": "SBUX", "sector": "Consumer Services", "weight": 16},
    {"ticker": "BKNG", "name": "BKNG", "sector": "Consumer Services", "weight": 22},
    {"ticker": "ABNB", "name": "ABNB", "sector": "Consumer Services", "weight": 14},
    {"ticker": "DIS", "name": "DIS", "sector": "Consumer Services", "weight": 22},
    {"ticker": "MAR", "name": "MAR", "sector": "Consumer Services", "weight": 8},
    {"ticker": "HLT", "name": "HLT", "sector": "Consumer Services", "weight": 8},
    {"ticker": "YUM", "name": "YUM", "sector": "Consumer Services", "weight": 6},
    {"ticker": "V", "name": "V", "sector": "Commercial Services", "weight": 60},
    {"ticker": "MA", "name": "MA", "sector": "Commercial Services", "weight": 50},
    {"ticker": "FIS", "name": "FIS", "sector": "Commercial Services", "weight": 6},
    {"ticker": "PAYX", "name": "PAYX", "sector": "Commercial Services", "weight": 6},
    {"ticker": "VRSK", "name": "VRSK", "sector": "Commercial Services", "weight": 5},
    {"ticker": "CTAS", "name": "CTAS", "sector": "Commercial Services", "weight": 6},
    {"ticker": "WM", "name": "WM", "sector": "Commercial Services", "weight": 8},
    {"ticker": "RSG", "name": "RSG", "sector": "Commercial Services", "weight": 7},
    {"ticker": "TSLA", "name": "TSLA", "sector": "Consumer Durables", "weight": 85},
    {"ticker": "F", "name": "F", "sector": "Consumer Durables", "weight": 12},
    {"ticker": "GM", "name": "GM", "sector": "Consumer Durables", "weight": 12},
    {"ticker": "TM", "name": "TM", "sector": "Consumer Durables", "weight": 30},
    {"ticker": "RACE", "name": "RACE", "sector": "Consumer Durables", "weight": 15},
    {"ticker": "WHR", "name": "WHR", "sector": "Consumer Durables", "weight": 3},
    {"ticker": "NVR", "name": "NVR", "sector": "Consumer Durables", "weight": 5},
    {"ticker": "PHM", "name": "PHM", "sector": "Consumer Durables", "weight": 5},
    {"ticker": "DHI", "name": "DHI", "sector": "Consumer Durables", "weight": 6},
    {"ticker": "T", "name": "T", "sector": "Communications", "weight": 18},
    {"ticker": "VZ", "name": "VZ", "sector": "Communications", "weight": 20},
    {"ticker": "TMUS", "name": "TMUS", "sector": "Communications", "weight": 24},
    {"ticker": "CMCSA", "name": "CMCSA", "sector": "Communications", "weight": 16},
    {"ticker": "HAL", "name": "HAL", "sector": "Industrial Services", "weight": 6},
    {"ticker": "BKR", "name": "BKR", "sector": "Industrial Services", "weight": 5},
    {"ticker": "URI", "name": "URI", "sector": "Industrial Services", "weight": 6},
    {"ticker": "FAST", "name": "FAST", "sector": "Industrial Services", "weight": 5},
    {"ticker": "GWW", "name": "GWW", "sector": "Industrial Services", "weight": 5},
    {"ticker": "JCI", "name": "JCI", "sector": "Industrial Services", "weight": 6},
    {"ticker": "SYY", "name": "SYY", "sector": "Distribution Services", "weight": 5},
    {"ticker": "MCK", "name": "MCK", "sector": "Distribution Services", "weight": 7},
    {"ticker": "COR", "name": "COR", "sector": "Distribution Services", "weight": 6},
    {"ticker": "CDW", "name": "CDW", "sector": "Distribution Services", "weight": 4},
    {"ticker": "NEM", "name": "NEM", "sector": "Non-Energy Minerals", "weight": 12},
    {"ticker": "FCX", "name": "FCX", "sector": "Non-Energy Minerals", "weight": 12},
    {"ticker": "AA", "name": "AA", "sector": "Non-Energy Minerals", "weight": 4},
    {"ticker": "X", "name": "X", "sector": "Non-Energy Minerals", "weight": 3},
]


def fetch_heatmap_data(market_list, ttl_seconds):
    # ttl을 장중/장마감에 따라 동적으로 바꾸기 위해 캐시 래퍼를 매번 그 ttl로 재구성함
    @st.cache_data(ttl=ttl_seconds)
    def _cached(tickers_tuple):
        tickers = list(tickers_tuple)
        data = download_with_retry(tickers, period="5d", progress=False, threads=True)
        return data

    try:
        data = _cached(tuple(item["ticker"] for item in market_list))
        close_data = data["Close"] if isinstance(data.columns, pd.MultiIndex) else data

        results = []
        failed_tickers = []
        for item in market_list:
            tk = item["ticker"]
            if tk in close_data.columns:
                series = close_data[tk].dropna()
                if len(series) >= 2:
                    curr_price = series.iloc[-1]
                    prev_price = series.iloc[-2]
                    pct_change = ((curr_price - prev_price) / prev_price) * 100
                else:
                    pct_change = float("nan")
                    failed_tickers.append(tk)
            else:
                pct_change = float("nan")
                failed_tickers.append(tk)

            change_text = f"{pct_change:+.2f}%" if pd.notna(pct_change) else "N/A"
            results.append({
                "Ticker": tk, "Name": item["name"], "Sector": item["sector"], "Weight": item["weight"],
                "Change": round(pct_change, 2) if pd.notna(pct_change) else float("nan"),
                "ChangeText": change_text,
            })

        if failed_tickers:
            # "0%"로 조용히 둔갑시키지 않고, 데이터 조회에 실패한 종목이 있다는 걸 명확히 알림
            st.caption(f"{len(failed_tickers)}개 종목의 시세를 가져오지 못했습니다(회색 N/A로 표시):"
                       f"{', '.join(failed_tickers[:8])}{' 외' if len(failed_tickers) > 8 else ''}")

        return pd.DataFrame(results)
    except Exception as e:
        st.error(f"데이터 연동 중 오류 발생: {e}")
        return pd.DataFrame()


def get_finviz_color(pct) -> str:
    if pd.isna(pct): return "#94a3b8"  # 데이터 없음(N/A) — 보합(#d5d5d5)과 확실히 구분되는 색
    if pct <= -3: return "#a50e0e"
    elif pct <= -2: return "#c9302c"
    elif pct <= -1: return "#e0605c"
    elif pct <= -0.3: return "#f0928f"
    elif pct < 0.3: return "#d5d5d5"
    elif pct < 1: return "#8fce9e"
    elif pct < 2: return "#4caf6e"
    elif pct < 3: return "#2e8b4f"
    else: return "#1a6b35"


def build_finviz_treemap(df: pd.DataFrame) -> go.Figure:
    ids, labels, parents, values, colors, customdata = [], [], [], [], [], []
    sector_totals = df.groupby("Sector")["Weight"].sum().to_dict()

    ids.append("root"); labels.append(""); parents.append(""); values.append(sum(sector_totals.values()))
    colors.append("#ffffff"); customdata.append(["", "", ""])

    for sector, total_w in sector_totals.items():
        ids.append(sector); labels.append(f"{sector} ›"); parents.append("root"); values.append(total_w)
        colors.append("#ffffff"); customdata.append(["", "", ""])

    for _, row in df.iterrows():
        ids.append(row["Ticker"])
        labels.append(f"<b>{row['Ticker']}</b><br>{row['ChangeText']}")
        parents.append(row["Sector"])
        values.append(max(row["Weight"], 0.1))
        colors.append(get_finviz_color(row["Change"]))
        customdata.append([row["Name"], row["ChangeText"], row["Ticker"]])

    fig = go.Figure(go.Treemap(
        ids=ids, labels=labels, parents=parents, values=values, branchvalues="total",
        marker=dict(colors=colors, line=dict(color="#ffffff", width=2)),
        customdata=customdata, texttemplate="%{label}",
        textfont=dict(color="#111111", family="Arial, Helvetica, sans-serif"),
        hovertemplate="<b>%{customdata[0]}</b> (%{customdata[2]})<br>변동률: %{customdata[1]}<extra></extra>",
        pathbar=dict(visible=False), tiling=dict(pad=2),
    ))
    fig.update_layout(template="plotly_white", paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
                       height=850, margin=dict(l=0, r=0, t=10, b=0))
    return fig


# --- UI ---
theme.page_header("MARKET MAP TERMINAL", "시가총액 규모 및 당일 등락률을 트리맵 형태로 시각화합니다. (Finviz 클래식 스타일)")
st.write("---")

col_market, _ = st.columns([2, 3])
with col_market:
    selected_market = st.radio("분석 시장 선택", ["대한민국 KOSPI 주요 종목", "미국 S&P 500 빅테크"], horizontal=True)

target_dataset = KOSPI_STOCKS if "KOSPI" in selected_market else US_MARKET_DATA
ttl = smart_cache_ttl(default_open=60, default_closed=1800)

skeleton_ph = theme.skeleton(height=850)
df_heatmap = fetch_heatmap_data(target_dataset, ttl)
skeleton_ph.empty()

if not df_heatmap.empty:
    df_heatmap["Weight"] = pd.to_numeric(df_heatmap["Weight"])

    st.markdown("""
        <div class="legend-wrap">
            <span style="font-size:13px; color:#64748b; font-weight:700;">등락률 범례</span>
            <div class="legend-item"><span class="legend-swatch" style="background:#a50e0e;"></span>-3% 이하</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#e0605c;"></span>-1%~-2%</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#d5d5d5;"></span>보합</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#8fce9e;"></span>+0.3%~+1%</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#1a6b35;"></span>+3% 이상</div>
            <div class="legend-item"><span class="legend-swatch" style="background:#94a3b8;"></span>N/A(조회 실패)</div>
        </div>
        """, unsafe_allow_html=True)
    st.caption(
        f"최종 업데이트: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} ·"
        f"캐시 주기: 장중 {60}s / 장마감 {1800}s(스마트 조정) · 박스를 클릭하면 해당 종목 분석 페이지로 이동합니다."
    )

    fig = build_finviz_treemap(df_heatmap)

    clicked_data = plotly_events(fig, click_event=True, hover_event=False, select_event=False,
                                  override_height=850, key="treemap_click")

    if clicked_data:
        try:
            point_index = clicked_data[0].get("pointNumber")
            if point_index is not None:
                clicked_ticker = fig.data[0].customdata[point_index][2]
                if clicked_ticker and str(clicked_ticker) not in ["(?)", "None", ""]:
                    db.add_watch(USER_ID, clicked_ticker)
                    st.session_state.ticker_val = clicked_ticker
                    st.session_state.ticker_input_key = clicked_ticker
                    st.session_state.run_analysis = True
                    st.switch_page("pages/1_ZION_Analyzer.py")
        except Exception as e:
            st.error(f"클릭 처리 중 오류: {e}")

    st.write("---")
    st.subheader("섹터별 동향 요약")
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
