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
                    st.error("수집된 데이터가 없습니다.")
                    return False
                
                # [추가] 멀티 인덱스라면 가장 윗 단계(Close, High 등)만 남기고 정리합니다.
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                
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

    def display_metrics(self):
        if self.df is None or len(self.df) < 2: return

        # 가장 최근 데이터와 이전 데이터 가져오기
        last_row = self.df.iloc[-1]
        prev_row = self.df.iloc[-2]

        # float()를 씌워서 확실하게 숫자 하나만 뽑아옵니다.
        try:
            current_price = float(last_row['Close'])
            prev_price = float(prev_row['Close'])
            price_diff = current_price - prev_price
            current_rsi = float(last_row['RSI'])
        except (TypeError, ValueError):
            # 데이터가 비어있거나 형식이 이상할 경우 대비
            st.warning("데이터 형식이 올바르지 않습니다.")
            return

        m1, m2, m3 = st.columns(3)
        
        with m1:
            st.metric(label="현재 주가", value=f"${current_price:.2f}", delta=f"{price_diff:.2f}")
        
        with m2:
            rsi_status = "보통"
            if current_rsi >= 70: rsi_status = "⚠️ 과매수 (위험)"
            elif current_rsi <= 30: rsi_status = "✅ 과매도 (기회)"
            st.metric(label="현재 RSI 점수", value=f"{current_rsi:.1f}", help="70 이상이면 과열, 30 이하면 저평가 상태입니다.")
            st.caption(f"현재 시장 상태는 **{rsi_status}** 입니다.")

        with m3:
            last_signal = "신호 없음"
            if last_row['Signal'] == 1: last_signal = "🟢 매수 추천"
            elif last_row['Signal'] == -1: last_signal = "🔴 매도 추천"
            st.metric(label="최근 분석 결과", value=last_signal)

    def display_financials(self):
        try:
            ticker_obj = yf.Ticker(self.ticker)
            # 연간 손익계산서 가져오기
            df_fin = ticker_obj.financials
            
            if df_fin.empty:
                st.warning("재무 데이터를 불러올 수 없습니다.")
                return

            # 금융 문맹도 이해하기 쉬운 주요 항목만 필터링 (영문 -> 한글 변환)
            target_metrics = {
                'Total Revenue': '매출액',
                'Net Income': '당기순이익',
                'Operating Income': '영업이익',
                'EBITDA': 'EBITDA (현금창출력)'
            }
            
            # 존재하는 항목만 추출
            available_metrics = [m for m in target_metrics.keys() if m in df_fin.index]
            df_filtered = df_fin.loc[available_metrics].copy()
            df_filtered.index = [target_metrics[m] for m in available_metrics]

            # 숫자를 읽기 쉽게 단위 변경 (예: 10억 단위)
            def format_billions(x):
                if pd.isna(x): return "-"
                return f"{x / 1e9:,.1f} B" # Billion 단위

            st.subheader(f"📊 {self.ticker} 연간 핵심 재무 지표 (단위: 10억 달러)")
            st.dataframe(df_filtered.map(format_billions), use_container_width=True)
            st.caption("※ 데이터는 최신 연도 순으로 표시됩니다.")
            
        except Exception as e:
            st.error(f"재무 데이터 분석 중 에러 발생: {e}")

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
st.set_page_config(page_title="zion", layout="wide")
st.title("기술적 분석 및 매매 신호")
st.markdown("이평선 골든/데드 크로스와 RSI 지표를 활용하여 매수/매도 기준을 제공합니다.")

# 사이드바 입력 폼
with st.sidebar:
    st.header("설정")
    ticker_input = st.text_input("종목 코드 (예: ORCL, AAPL, NVDA)", value="ORCL")
    
    col1, col2 = st.columns(2)
    with col1:
        start_date = st.date_input("시작일", datetime.date(2025, 1, 1))
    with col2:
        end_date = st.date_input("종료일", datetime.date.today())
    
    analyze_btn = st.button("분석 실행", type="primary", use_container_width=True)

# 메인 화면 로직
if analyze_btn:
    if start_date >= end_date:
        st.error("종료일이 시작일보다 빠를 수 없습니다.")
    else:
        # 1. 여기서 analyzer를 정의해줘야 합니다! (이 줄이 빠졌을 거예요)
        analyzer = StockAnalyzer(ticker_input.upper())
        
        # 2. 이제 analyzer를 사용할 수 있습니다.
        if analyzer.fetch_data(start_date, end_date):
            analyzer.calculate_indicators()
            analyzer.get_signals()
            
            # 상단 지표 요약
            st.subheader(f"🔍 {ticker_input.upper()} 현재 상황 요약")
            analyzer.display_metrics() 
            
            st.markdown("---")
            
            # 메인 차트
            analyzer.visualize()
            
            st.markdown("---")
            
            # 재무 제표 expander
            with st.expander("💼 기업 펀더멘탈 (재무 데이터) 확인하기", expanded=True):
                analyzer.display_financials()
            
            # 데이터 원본 보기
            with st.expander("원본 데이터 보기 (최근 10일)"):
                st.dataframe(analyzer.df.tail(10))
