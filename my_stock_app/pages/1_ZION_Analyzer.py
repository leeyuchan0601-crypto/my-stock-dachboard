import streamlit as st
import matplotlib.pyplot as plt
import yfinance as yf
import pandas as pd
import datetime
from PIL import Image
import os
import json

# --- 0. 데이터 관리 및 콜백 함수 ---
HISTORY_FILE = "search_history.json"

def load_history():
    if os.path.exists(HISTORY_FILE):
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except: return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def on_ticker_enter():
    # 입력창(key="ticker_input_key")의 값을 가져와서 세션에 저장
    input_val = st.session_state.ticker_input_key.upper().strip()
    if input_val:
        # 1. 히스토리에 즉시 추가 (중복 제거 후 맨 위로)
        if input_val in st.session_state.history:
            st.session_state.history.remove(input_val)
        st.session_state.history.insert(0, input_val)
        save_history(st.session_state.history)
        
        # 2. 현재 입력값을 동기화하고 분석 신호 ON
        st.session_state.ticker_val = input_val
        st.session_state.run_analysis = True

# --- 1. 페이지 설정 및 아이콘 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Analyzer", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Analyzer", page_icon="📈", layout="wide")

# --- 2. 하이테크 사이버펑크 CSS ---
st.markdown("""
    <style>
    div[data-testid="metric-container"] {
        background-color: rgba(0, 212, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.2);
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
    }
    .stTabs [data-baseweb="tab-list"] { gap: 24px; }
    .stTabs [data-baseweb="tab"] { height: 50px; font-weight: bold; font-size: 16px; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 분석 클래스 ---
class StockAnalyzer():
    def __init__(self, ticker):
        self.ticker = ticker
        self.df = None

    def fetch_data(self, start_date, end_date):
        with st.spinner(f"[ZION] {self.ticker} 동기화 중..."):
            try:
                data = yf.download(self.ticker, start=start_date, end=end_date)
                if data.empty: return False
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                self.df = data
                return True
            except: return False
        
    def calculate_indicators(self):
        if self.df is None: return 
        self.df['MA5'] = self.df['Close'].rolling(5).mean()
        self.df['MA20'] = self.df['Close'].rolling(20).mean()
        delta = self.df['Close'].diff()
        up, down = delta.clip(lower=0), -delta.clip(upper=0)
        rs = up.rolling(14).mean() / down.rolling(14).mean()
        self.df['RSI'] = 100 - (100 / (1 + rs))

    def get_signals(self):
        self.df['Signal'] = 0
        buy = (self.df['MA5'].shift(1) < self.df['MA20'].shift(1)) & (self.df['MA5'] > self.df['MA20']) & (self.df['RSI'] < 65)
        sell = (self.df['MA5'].shift(1) > self.df['MA20'].shift(1)) & (self.df['MA5'] < self.df['MA20']) & (self.df['RSI'] > 35)
        self.df.loc[buy, 'Signal'] = 1
        self.df.loc[sell, 'Signal'] = -1

    def display_metrics(self):
        last, prev = self.df.iloc[-1], self.df.iloc[-2]
        m1, m2, m3 = st.columns(3)
        m1.metric("현재 주가", f"${float(last['Close']):.2f}", f"{float(last['Close'])-float(prev['Close']):.2f}")
        m2.metric("RSI 지수", f"{float(last['RSI']):.1f}")
        sig = "🟢 BUY" if last['Signal']==1 else "🔴 SELL" if last['Signal']==-1 else "HOLD"
        m3.metric("최근 시그널", sig)

    def display_financials(self):
        try:
            t_obj = yf.Ticker(self.ticker)
            df_all = pd.concat([t_obj.quarterly_financials, t_obj.quarterly_balance_sheet, t_obj.quarterly_cashflow])
            target = {
                'Total Revenue': '매출액', 'Gross Profit': '매출총이익', 'Operating Income': '영업이익', 
                'Net Income': '당기순이익', 'EBITDA': 'EBITDA', 'Basic EPS': 'EPS',
                'Total Assets': '총 자산', 'Total Liabilities Net Minority Interest': '총 부채',
                'Total Debt': '총 차입금', 'Operating Cash Flow': '영업현금흐름', 'Free Cash Flow': '잉여현금흐름(FCF)'
            }
            available = [m for m in target.keys() if m in df_all.index]
            df_res = df_all.loc[available].copy()
            df_res.index = [target[m] for m in available]
            def fmt(x):
                if pd.isna(x) or x == 0: return "-"
                if -1000 < x < 1000: return f"{x:.2f}"
                return f"{x / 1e9:,.2f} B"
            st.dataframe(df_res.map(fmt), use_container_width=True)
            st.caption("※ B = 10억 달러(Billion USD)")
        except: st.warning("재무 데이터를 불러올 수 없습니다.")

    def visualize(self):
        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, gridspec_kw={'height_ratios': [3, 1]})
        ax1.plot(self.df.index, self.df['Close'], color='white', alpha=0.3)
        ax1.plot(self.df.index, self.df['MA5'], color='#ff0055', label='MA5')
        ax1.plot(self.df.index, self.df['MA20'], color='#00d4ff', label='MA20')
        ax1.legend()
        ax2.plot(self.df.index, self.df['RSI'], color='#bc13fe')
        ax2.axhline(70, color='red', alpha=0.5); ax2.axhline(30, color='green', alpha=0.5)
        st.pyplot(fig)

# --- 4. 사이드바 및 히스토리 로직 ---
if 'history' not in st.session_state: st.session_state.history = load_history()
if 'ticker_val' not in st.session_state: st.session_state.ticker_val = "ORCL"
if 'run_analysis' not in st.session_state: st.session_state.run_analysis = False

with st.sidebar:
    st.header("CONTROL PANEL")
    ticker_input = st.text_input(
        "종목 코드", 
        value=st.session_state.ticker_val, 
        key="ticker_input_key", 
        on_change=on_ticker_enter
    ).upper()
    
    col1, col2 = st.columns(2)
    start_d = col1.date_input("시작일", datetime.date(2025, 1, 1))
    end_d = col2.date_input("종료일", datetime.date.today())
    
    analyze_btn = st.button("SYSTEM START", type="primary", use_container_width=True)

    st.write("---")
    st.subheader("최근 검색 기록")
    for h_ticker in st.session_state.history[:10]:
        h_col1, h_col2 = st.columns([4, 1])
        if h_col1.button(f"{h_ticker}", key=f"h_{h_ticker}", use_container_width=True):
            st.session_state.ticker_val = h_ticker
            st.session_state.run_analysis = True
            st.rerun()
        if h_col2.button("🗑️", key=f"d_{h_ticker}"):
            st.session_state.history.remove(h_ticker)
            save_history(st.session_state.history)
            st.rerun()

# --- 5. 메인 분석 실행부 ---
if analyze_btn or st.session_state.run_analysis:
    st.session_state.run_analysis = False
    target_ticker = st.session_state.ticker_val
    
    # 분석 객체 생성 및 실행
    analyzer = StockAnalyzer(target_ticker)
    if analyzer.fetch_data(start_d, end_d):
        analyzer.calculate_indicators()
        analyzer.get_signals()
        
        st.title(f"🛰️ {target_ticker} DIAGNOSTICS")
        analyzer.display_metrics()
        
        st.write("---")
        tab1, tab2, tab3 = st.tabs(["CHART ANALYSIS", "FINANCIAL DATA", "RAW LOGS"])
        with tab1: analyzer.visualize()
        with tab2: analyzer.display_financials()
        with tab3: st.dataframe(analyzer.df.tail(20), use_container_width=True)
