import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import datetime
from PIL import Image
import os

# 1. 페이지 설정 (분석기 전용)
st.set_page_config(page_title="ZION Analyzer", page_icon="📈", layout="wide")

# 2. 하이테크 사이버펑크 CSS 스타일링
st.markdown("""
    <style>
    /* 메트릭 카드 스타일 */
    div[data-testid="metric-container"] {
        background-color: rgba(0, 212, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.2);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    /* 탭 메뉴 스타일 */
    .stTabs [data-baseweb="tab-list"] {
        gap: 24px;
    }
    .stTabs [data-baseweb="tab"] {
        height: 50px;
        white-space: pre-wrap;
        font-weight: bold;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

class StockAnalyzer():
    def __init__(self, ticker):
        self.ticker = ticker
        self.df = None

    def fetch_data(self, start_date, end_date):
        with st.spinner(f"📡 [ZION] {self.ticker} 데이터 동기화 중..."):
            try:
                data = yf.download(self.ticker, start=start_date, end=end_date)
                if data.empty:
                    st.error("수집된 데이터가 없습니다.")
                    return False
                
                # [중요] yfinance 멀티 인덱스 컬럼 정리 (TypeError 방지)
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                
                self.df = data
                return True
            except Exception as e:
                st.error(f"데이터 수집 중 예외 발생: {e}")
                return False
        
    def calculate_indicators(self):
        if self.df is None: return 
        
        # 이동평균선
        self.df['MA5'] = self.df['Close'].rolling(window=5).mean()
        self.df['MA20'] = self.df['Close'].rolling(window=20).mean()

        # RSI 지표
        delta = self.df['Close'].diff()
        up = delta.clip(lower=0)
        down = -delta.clip(upper=0)
        avg_up = up.rolling(window=14).mean()
        avg_down = down.rolling(window=14).mean()
        rs = avg_up / avg_down
        self.df['RSI'] = 100 - (100 / (1 + rs))

    def get_signals(self):
        if self.df is None or 'RSI' not in self.df.columns: return

        self.df['prev_MA5'] = self.df['MA5'].shift(1)
        self.df['prev_MA20'] = self.df['MA20'].shift(1)
        self.df['Signal'] = 0

        # 매수 신호: 골든크로스 & RSI 저평가
        buy_cond = (self.df['prev_MA5'] < self.df['prev_MA20']) & \
                   (self.df['MA5'] > self.df['MA20']) & \
                   (self.df['RSI'] < 65)
        self.df.loc[buy_cond, 'Signal'] = 1

        # 매도 신호: 데드크로스 & RSI 고평가
        sell_cond = (self.df['prev_MA5'] > self.df['prev_MA20']) & \
                    (self.df['MA5'] < self.df['MA20']) & \
                    (self.df['RSI'] > 35)
        self.df.loc[sell_cond, 'Signal'] = -1

    def display_metrics(self):
        if self.df is None or len(self.df) < 2: return

        last_row = self.df.iloc[-1]
        prev_row = self.df.iloc[-2]

        try:
            # 강제 float 변환으로 데이터 안정성 확보
            current_price = float(last_row['Close'])
            prev_price = float(prev_row['Close'])
            price_diff = current_price - prev_price
            current_rsi = float(last_row['RSI'])
        except:
            st.warning("데이터 형식이 올바르지 않습니다.")
            return

        m1, m2, m3 = st.columns(3)
        with m1:
            st.metric(label="현재 주가", value=f"${current_price:.2f}", delta=f"{price_diff:.2f}")
        with m2:
            st.metric(label="RSI 지수", value=f"{current_rsi:.1f}", help="70 이상 과매수, 30 이하 과매도")
        with m3:
            last_sig = "HOLD"
            if last_row['Signal'] == 1: last_sig = "🟢 BUY"
            elif last_row['Signal'] == -1: last_sig = "🔴 SELL"
            st.metric(label="최근 시그널", value=last_sig)

    def display_financials(self):
        try:
            ticker_obj = yf.Ticker(self.ticker)
            df_fin = ticker_obj.quarterly_financials # 분기별 데이터
            
            if df_fin.empty:
                st.warning("재무 데이터를 불러올 수 없습니다.")
                return

            target_metrics = {
                'Total Revenue': '매출액',
                'Net Income': '당기순이익',
                'Operating Income': '영업이익',
                'EBITDA': '현금창출력(EBITDA)'
            }
            
            available = [m for m in target_metrics.keys() if m in df_fin.index]
            df_filtered = df_fin.loc[available].copy()
            df_filtered.index = [target_metrics[m] for m in available]

            # 10억 달러(B) 단위 포맷팅
            def format_billions(x):
                if pd.isna(x) or x == 0: return "-"
                return f"{x / 1e9:,.2f} B"

            st.dataframe(df_filtered.map(format_billions), use_container_width=True)
            st.caption("※ 단위: 10억 달러(Billion USD)")
            
        except Exception as e:
            st.error(f"재무 데이터 분석 오류: {e}")

    def visualize(self):
        if self.df is None: return
        plt.style.use('dark_background') # 다크모드 적용
        
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

        # 주가 및 이동평균선
        ax1.plot(self.df.index, self.df['Close'], label='Close', color='#ffffff', alpha=0.3)
        ax1.plot(self.df.index, self.df['MA5'], label='MA5', color='#ff0055', alpha=0.8)
        ax1.plot(self.df.index, self.df['MA20'], label='MA20', color='#00d4ff', alpha=0.8)

        # 신호 표시
        buy = self.df[self.df['Signal'] == 1]
        ax1.plot(buy.index, buy['Close'], '^', markersize=12, color='#00ff00', label='BUY')
        sell = self.df[self.df['Signal'] == -1]
        ax1.plot(sell.index, sell['Close'], 'v', markersize=12, color='#ff0000', label='SELL')

        ax1.set_title(f"{self.ticker} ANALYSIS", color='#00d4ff', fontsize=16)
        ax1.legend()
        ax1.grid(True, alpha=0.1)

        # RSI
        ax2.plot(self.df.index, self.df['RSI'], color='#bc13fe')
        ax2.axhline(70, color='#ff0000', linestyle='--', alpha=0.5)
        ax2.axhline(30, color='#00ff00', linestyle='--', alpha=0.5)
        ax2.set_ylim(0, 100)
        ax2.set_ylabel("RSI")

        plt.tight_layout()
        st.pyplot(fig)

# --- 실행 로직 ---
with st.sidebar:
    st.header("🛸 CONTROL PANEL")
    ticker_input = st.text_input("종목 코드", value="ORCL").upper()
    col1, col2 = st.columns(2)
    with col1:
        start_d = st.date_input("시작일", datetime.date(2025, 1, 1))
    with col2:
        end_d = st.date_input("종료일", datetime.date.today())
    analyze_btn = st.button("SYSTEM START", type="primary", use_container_width=True)

if analyze_btn:
    analyzer = StockAnalyzer(ticker_input)
    if analyzer.fetch_data(start_d, end_d):
        analyzer.calculate_indicators()
        analyzer.get_signals()
        
        st.title(f"🛰️ {ticker_input} DIAGNOSTICS")
        analyzer.display_metrics()
        
        st.write("---")
        
        # 탭 구성
        tab1, tab2, tab3 = st.tabs(["📊 CHART ANALYSIS", "💼 FINANCIAL DATA", "📜 RAW LOGS"])
        
        with tab1:
            analyzer.visualize()
        with tab2:
            st.subheader("분기별 실적 요약")
            analyzer.display_financials()
        with tab3:
            st.dataframe(analyzer.df.tail(20), use_container_width=True)