import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import datetime
from PIL import Image
import os

# --- 1. 페이지 설정 (맨 위에 한 번만!) ---
image_path = "ark_base.png"
if os.path.exists(image_path):
    img = Image.open(image_path)
    st.set_page_config(page_title="ZION", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION", page_icon="🛡️", layout="wide")

# --- 2. 하이테크 커스텀 CSS 주입 ---
st.markdown("""
    <style>
    /* 메인 배경 및 폰트 설정 */
    .main {
        background-color: #0e1117;
    }
    h1, h2, h3 {
        color: #00d4ff !important;
        font-family: 'Courier New', Courier, monospace;
    }
    /* 메트릭 카드 스타일링 */
    div[data-testid="metric-container"] {
        background-color: rgba(0, 212, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.2);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    /* 버튼 스타일 */
    .stButton>button {
        background-color: #00d4ff;
        color: black;
        border-radius: 5px;
        font-weight: bold;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #ffffff;
        box-shadow: 0 0 15px #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)

st.title(" ZION : ZERO INSIGHT ON")
st.subheader("금융을 바라보는 올바른 시선")
st.markdown("---")

# [클래스 부분은 기존과 동일하되, UI 요소만 살짝 다듬습니다]
class StockAnalyzer():
    def __init__(self, ticker):
        self.ticker = ticker
        self.df = None

    def fetch_data(self, start_date, end_date):
        with st.spinner(f" [ZION] {self.ticker} 데이터 동기화 중..."):
            try:
                data = yf.download(self.ticker, start=start_date, end=end_date)
                if data.empty:
                    st.error("데이터 동기화 실패.")
                    return False
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                self.df = data
                return True
            except Exception as e:
                st.error(f"연결 오류: {e}")
                return False

    def calculate_indicators(self):
        if self.df is None: return 
        self.df['MA5'] = self.df['Close'].rolling(window=5).mean()
        self.df['MA20'] = self.df['Close'].rolling(window=20).mean()
        delta = self.df['Close'].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        avg_up = up.rolling(window=14).mean()
        avg_down = down.rolling(window=14).mean()
        rs = avg_up / avg_down
        self.df['RSI'] = 100 - (100 / (1 + rs))

    def get_signals(self):
        if self.df is None: return
        self.df['prev_MA5'] = self.df['MA5'].shift(1)
        self.df['prev_MA20'] = self.df['MA20'].shift(1)
        self.df['Signal'] = 0
        buy_cond = (self.df['prev_MA5'] < self.df['prev_MA20']) & (self.df['MA5'] > self.df['MA20']) & (self.df['RSI'] < 65)
        self.df.loc[buy_cond, 'Signal'] = 1
        sell_cond = (self.df['prev_MA5'] > self.df['prev_MA20']) & (self.df['MA5'] < self.df['MA20']) & (self.df['RSI'] > 35)
        self.df.loc[sell_cond, 'Signal'] = -1

    def display_metrics(self):
        last_row = self.df.iloc[-1]
        prev_row = self.df.iloc[-2]
        current_price = float(last_row['Close'])
        price_diff = current_price - float(prev_row['Close'])
        
        m1, m2, m3 = st.columns(3)
        m1.metric("CURRENT PRICE", f"${current_price:.2f}", f"{price_diff:.2f}")
        m2.metric("RSI INDEX", f"{float(last_row['RSI']):.1f}")
        m3.metric("LATEST SIGNAL", "BUY" if last_row['Signal']==1 else "SELL" if last_row['Signal']==-1 else "HOLD")

    def display_financials(self):
        try:
            ticker_obj = yf.Ticker(self.ticker)
            df_fin = ticker_obj.quarterly_financials
            
            if df_fin.empty:
                st.warning("분기 재무 데이터를 불러올 수 없습니다.")
                return

            # 1. 가장 중요한 4가지만 골라내고 한글로 번역
            target_metrics = {
                'Total Revenue': '매출액',
                'Net Income': '당기순이익',
                'Operating Income': '영업이익',
                'EBITDA': '현금창출력(EBITDA)'
            }
            
            # 데이터프레임에서 위 항목만 추출
            available_metrics = [m for m in target_metrics.keys() if m in df_fin.index]
            df_filtered = df_fin.loc[available_metrics].copy()
            df_filtered.index = [target_metrics[m] for m in available_metrics]

            # 2. 숫자를 읽기 쉽게 변환 (예: 8,393,000,000 -> 8.39 B)
            def format_billions(x):
                if pd.isna(x) or x == 0: return "-"
                return f"{x / 1e9:,.2f} B"

            st.subheader(f"{self.ticker} 분기별 핵심 실적 요약")
            
            # 스타일 적용 (최대값 강조 + 포맷팅)
            formatted_df = df_filtered.map(format_billions)
            st.dataframe(formatted_df, use_container_width=True)
            
            st.caption("※ B = 10억 달러 (Billion). 숫자가 낮을수록 기업의 규모나 수익이 적음을 의미합니다.")
            
        except Exception as e:
            st.error(f"재무 데이터 정리 중 에러 발생: {e}")
    def visualize(self):
        # 다크모드 차트 설정
        plt.style.use('dark_background')
        fig, ax1 = plt.subplots(figsize=(12, 5))
        ax1.plot(self.df.index, self.df['Close'], color='#ffffff', alpha=0.3)
        ax1.plot(self.df.index, self.df['MA5'], color='#ff0055', label='Short-term')
        ax1.plot(self.df.index, self.df['MA20'], color='#00d4ff', label='Long-term')
        ax1.legend()
        st.pyplot(fig)

# --- 4. 사이드바 ---
with st.sidebar:
    st.header("CONTROL CENTER")
    ticker_input = st.text_input("TARGET TICKER", value="ORCL")
    start_date = st.date_input("START", datetime.date(2025, 1, 1))
    end_date = st.date_input("END", datetime.date.today())
    analyze_btn = st.button("EXECUTE ANALYSIS", type="primary", use_container_width=True)

# --- 5. 메인 로직 (탭 시스템 적용) ---
if analyze_btn:
    analyzer = StockAnalyzer(ticker_input.upper())
    if analyzer.fetch_data(start_date, end_date):
        analyzer.calculate_indicators()
        analyzer.get_signals()
        
        analyzer.display_metrics()
        
        st.markdown("###  SYSTEM DIAGNOSTICS")
        # 탭 생성
        tab1, tab2, tab3 = st.tabs(["CHART ANALYSIS", "FINANCIAL DATA", "RAW LOGS"])
        
        with tab1:
            analyzer.visualize()
        
        with tab2:
            analyzer.display_financials()
            
        with tab3:
            st.dataframe(analyzer.df.tail(20))
