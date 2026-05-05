import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import datetime

class StockAnalyzer():
    def __init__(self, ticker):
        self.ticker = ticker
        self.df = None

    def fetch_data(self, start_date, end_date):
        with st.spinner(f"[{self.ticker}] 데이터 수집 중..."):
            try:
                data = yf.download(self.ticker, start=start_date, end=end_date)
                if data.empty:
                    st.error("수집된 데이터가 없습니다. 종목 코드나 기간을 확인하세요.")
                    return False
                
                self.df = data
                st.success("데이터 수집 완료!")
                return True
            except Exception as e:
                st.error(f"데이터 수집 중 예외 발생: {e}")
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
        if self.df is None or 'RSI' not in self.df.columns: return

        self.df['prev_MA5'] = self.df['MA5'].shift(1)
        self.df['prev_MA20'] = self.df['MA20'].shift(1)
        self.df['Signal'] = 0

        # 1. 매수 신호
        buy_cond = (self.df['prev_MA5'] < self.df['prev_MA20']) & \
                   (self.df['MA5'] > self.df['MA20']) & \
                   (self.df['RSI'] < 65)
        self.df.loc[buy_cond, 'Signal'] = 1

        # 2. 매도 신호
        sell_cond = (self.df['prev_MA5'] > self.df['prev_MA20']) & \
                    (self.df['MA5'] < self.df['MA20']) & \
                    (self.df['RSI'] > 35)
        self.df.loc[sell_cond, 'Signal'] = -1
        
        buy_count = sum(self.df['Signal']==1)
        sell_count = sum(self.df['Signal']==-1)
        st.info(f"신호 분석 완료: 🟢 매수 신호 {buy_count}건 | 🔴 매도 신호 {sell_count}건")

    def visualize(self):
        if self.df is None: return

        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})

        # 기본 차트 및 이평선
        ax1.plot(self.df.index, self.df['Close'], label='Close', color='black', alpha=0.5)
        ax1.plot(self.df.index, self.df['MA5'], label='MA5', color='red', alpha=0.8)
        ax1.plot(self.df.index, self.df['MA20'], label='MA20', color='blue', alpha=0.8)

        # 매수/매도 신호 표시
        buy_points = self.df[self.df['Signal'] == 1]
        ax1.plot(buy_points.index, buy_points['Close'], '^', markersize=10, color='red', label='BUY Signal')

        sell_points = self.df[self.df['Signal'] == -1]
        ax1.plot(sell_points.index, sell_points['Close'], 'v', markersize=10, color='blue', label='SELL Signal')

        ax1.set_title(f"{self.ticker} Trading Signals")
        ax1.legend()
        ax1.grid(True, alpha=0.3)

        # RSI 차트
        ax2.plot(self.df.index, self.df['RSI'], color='purple', label='RSI')
        ax2.axhline(70, color='red', linestyle='--', alpha=0.5)
        ax2.axhline(30, color='blue', linestyle='--', alpha=0.5)
        ax2.set_ylim(0, 100)
        ax2.grid(True, alpha=0.3)

        plt.tight_layout()
        
        # Streamlit 화면에 그래프 출력
        st.pyplot(fig)


# === Streamlit UI 구성 ===
st.set_page_config(page_title="주식 기술적 분석 대시보드", layout="wide")
st.title("📈 주식 기술적 분석 및 매매 신호 탐지기")
st.markdown("이평선 골든/데드 크로스와 RSI 지표를 활용하여 매수/매도 타이밍을 분석합니다.")

# 사이드바 입력 폼
with st.sidebar:
    st.header("설정")
    ticker_input = st.text_input("종목 코드 (예: ORCL, AAPL, NVDA)", value="ORCL")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일", datetime.date(2025, 1, 1))
    with col2:
        end_date = st.date_input("종료일", datetime.date(2026, 4, 15))
    
    analyze_btn = st.button("분석 실행", type="primary", use_container_width=True)

# 메인 화면 로직
if analyze_btn:
    if start_date >= end_date:
        st.error("종료일이 시작일보다 빠를 수 없습니다.")
    else:
        analyzer = StockAnalyzer(ticker_input.upper())
        if analyzer.fetch_data(start_date, end_date):
            analyzer.calculate_indicators()
            analyzer.get_signals()
            analyzer.visualize()
            
            with st.expander("데이터 원본 보기 (최근 10일)"):
                st.dataframe(analyzer.df.tail(10))