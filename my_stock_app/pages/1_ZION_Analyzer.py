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
    if "ticker_input_key" in st.session_state:
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
# pages 폴더 안에 있으므로 부모 경로를 찾아 이미지 로드
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
    .stTabs [data-baseweb="tab"] { 
        height: 50px; 
        font-weight: bold; 
        font-size: 16px; 
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 분석 클래스 ---
class StockAnalyzer():
    def __init__(self, ticker):
        self.ticker = ticker
        self.df = None
        self.display_start_date = None # 사용자가 보고싶은 실제 시작일

    def fetch_data(self, start_date, end_date):
        self.display_start_date = start_date # 실제 보여줄 날짜 기억

        # [핵심] Auto Lead-in: 기술지표 계산을 위해 40일 데이터를 더 다운로드함
        buffer_days = 40
        extended_start = start_date - datetime.timedelta(days=buffer_days)
        
        with st.spinner(f"📡 [ZION] {self.ticker} 데이터 동기화 중... (+Lead-in 40일)"):
            try:
                # 더 긴 기간의 데이터를 다운로드
                data = yf.download(self.ticker, start=extended_start, end=end_date)
                
                if data.empty:
                    st.error("수집된 데이터가 없습니다. 티커를 확인하세요.")
                    return False
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                self.df = data
                return True
            except Exception as e:
                st.error(f"데이터 수집 오류: {e}")
                return False
        
    def calculate_indicators(self):
        if self.df is None: return 
        # 이동평균선 (확장된 데이터에서 계산하므로 Lag가 상쇄됨)
        self.df['MA5'] = self.df['Close'].rolling(5).mean()
        self.df['MA20'] = self.df['Close'].rolling(20).mean()
        # RSI 지표
        delta = self.df['Close'].diff()
        up, down = delta.clip(lower=0), -delta.clip(upper=0)
        avg_up = up.rolling(14).mean()
        avg_down = down.rolling(14).mean()
        rs = avg_up / avg_down
        self.df['RSI'] = 100 - (100 / (1 + rs))

    def get_signals(self):
        if self.df is None: return
        self.df['Signal'] = 0
        
        # [신호 강화] RSI 조건을 조금 더 직관적으로 완화
        # 매수: 골든크로스 & RSI 70 미만 (완전 과열 아니면 매수)
        buy = (self.df['MA5'].shift(1) < self.df['MA20'].shift(1)) & \
              (self.df['MA5'] > self.df['MA20']) & \
              (self.df['RSI'] < 70) 
              
        # 매도: 데드크로스 & RSI 30 초과 (완전 침체 아니면 매도)
        sell = (self.df['MA5'].shift(1) > self.df['MA20'].shift(1)) & \
               (self.df['MA5'] < self.df['MA20']) & \
               (self.df['RSI'] > 30)
               
        self.df.loc[buy, 'Signal'] = 1
        self.df.loc[sell, 'Signal'] = -1

    def display_metrics(self):
        if self.df is None or len(self.df) < 2: return
        
        # [핵심] 사용자가 선택한 기간 이후의 데이터만 추출하여 메트릭 계산
        display_df = self.df.loc[self.display_start_date:].copy()
        
        if display_df.empty or len(display_df) < 2:
            st.warning("선택한 기간에 표시할 수 있는 데이터가 너무 적습니다.")
            return

        last, prev = display_df.iloc[-1], display_df.iloc[-2]
        m1, m2, m3 = st.columns(3)
        
        curr_price = float(last['Close'])
        diff = curr_price - float(prev['Close'])
        
        m1.metric("현재 주가", f"${curr_price:.2f}", f"{diff:.2f}")
        m2.metric("RSI 지수", f"{float(last['RSI']):.1f}")
        
        sig_text = "HOLD"
        # 최근 3일 이내의 신호가 있다면 표시 (더 안정적인 신호 캐치)
        recent_sig = display_df['Signal'].tail(3)
        if 1 in recent_sig.values: sig_text = "🟢 BUY (Recent)"
        elif -1 in recent_sig.values: sig_text = "🔴 SELL (Recent)"
        else: sig_text = "HOLD"
        
        m3.metric("최근 시그널(3일)", sig_text)

    def display_financials(self):
        try:
            t_obj = yf.Ticker(self.ticker)
            # 재무제표 통합
            df_inc = t_obj.quarterly_financials
            df_bal = t_obj.quarterly_balance_sheet
            df_cf  = t_obj.quarterly_cashflow

            if df_inc.empty and df_bal.empty and df_cf.empty:
                st.warning("재무 데이터를 불러올 수 없습니다.")
                return

            df_all = pd.concat([df_inc, df_bal, df_cf])
            
            target = {
                'Total Revenue': '매출액', 'Gross Profit': '매출총이익', 
                'Operating Income': '영업이익', 'Net Income': '당기순이익', 
                'EBITDA': 'EBITDA', 'Basic EPS': '주당순이익(EPS)',
                'Total Assets': '총 자산', 'Total Liabilities Net Minority Interest': '총 부채',
                'Total Debt': '총 차입금', 'Operating Cash Flow': '영업현금흐름', 
                'Free Cash Flow': '잉여현금흐름(FCF)', 'Capital Expenditure': '재투자비용(CAPEX)'
            }
            
            available = [m for m in target.keys() if m in df_all.index]
            if not available:
                st.warning("표시할 수 있는 재무 항목이 없습니다.")
                return

            df_res = df_all.loc[available].copy()
            df_res.index = [target[m] for m in available]

            def fmt(x):
                if pd.isna(x) or x == 0: return "-"
                if -1000 < x < 1000: return f"{x:.2f}"
                return f"{x / 1e9:,.2f} B"

            st.dataframe(df_res.map(fmt), use_container_width=True)
            st.caption("※ B = 10억 달러(Billion USD). EPS는 달러 단위.")
        except Exception as e:
            st.error(f"재무 데이터 호출 실패: {e}")

    def visualize(self):
        if self.df is None: return
        
        # [핵심] 사용자가 선택한 기간 이후의 데이터만 추출하여 시각화
        display_df = self.df.loc[self.display_start_date:].copy()
        
        if display_df.empty:
            st.error("시각화할 데이터가 없습니다.")
            return

        plt.style.use('dark_background')
        fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True, 
                                       gridspec_kw={'height_ratios': [3, 1]})
        
        # 메인 차트
        ax1.plot(display_df.index, display_df['Close'], color='white', alpha=0.3, label='Close')
        ax1.plot(display_df.index, display_df['MA5'], color='#ff0055', label='MA5', linewidth=2)
        ax1.plot(display_df.index, display_df['MA20'], color='#00d4ff', label='MA20', linewidth=2)
        
        # [신호 강화] 매수/매도 화살표 시인성 강화 (markersize=15)
        buy_points = display_df[display_df['Signal'] == 1]
        ax1.plot(buy_points.index, buy_points['Close'], '^', color='#00ff00', markersize=15, label='BUY SIGNAL', markeredgecolor='black')
        
        sell_points = display_df[display_df['Signal'] == -1]
        ax1.plot(sell_points.index, sell_points['Close'], 'v', color='#ff0000', markersize=15, label='SELL SIGNAL', markeredgecolor='black')
        
        ax1.set_title(f"🛰️ {self.ticker} DIAGNOSTICS CHART", color='#00d4ff', fontsize=18)
        ax1.legend(loc='upper left')
        ax1.grid(True, alpha=0.1)

        # RSI 차트
        ax2.plot(display_df.index, display_df['RSI'], color='#bc13fe', label='RSI', linewidth=1.5)
        # 과열/침체 기준선 (가독성 강화)
        ax2.axhline(70, color='#ff4444', linestyle='--', alpha=0.7)
        ax2.axhline(30, color='#44ff44', linestyle='--', alpha=0.7)
        ax2.fill_between(display_df.index, 70, 100, color='#ff0000', alpha=0.1) # 과열 구간 바탕색
        ax2.fill_between(display_df.index, 0, 30, color='#00ff00', alpha=0.1)  # 침체 구간 바탕색
        ax2.set_ylim(0, 100)
        ax2.set_ylabel("RSI")
        ax2.legend(loc='upper left')
        ax2.grid(True, alpha=0.05)
        
        plt.tight_layout()
        st.pyplot(fig)

# --- 4. 사이드바 및 히스토리 로직 ---
if 'history' not in st.session_state: st.session_state.history = load_history()
if 'ticker_val' not in st.session_state: st.session_state.ticker_val = "ORCL"
if 'run_analysis' not in st.session_state: st.session_state.run_analysis = False

with st.sidebar:
    st.header("🛸 ZION CONTROL")
    st.write("---")
    
    # 입력창 (엔터 시 on_ticker_enter 실행)
    ticker_input = st.text_input(
        "종목 코드 (ENTER TO SAVE)", 
        value=st.session_state.ticker_val, 
        key="ticker_input_key", 
        on_change=on_ticker_enter
    ).upper().strip()
    
    col1, col2 = st.columns(2)
    # 시작일 초기값을 조금 더 넉넉하게 잡음
    start_d = col1.date_input("시작일", datetime.date.today() - datetime.timedelta(days=180))
    end_d = col2.date_input("종료일", datetime.date.today())
    
    analyze_btn = st.button("SYSTEM START", type="primary", use_container_width=True)

    st.write("---")
    st.subheader("📜최근 검색 기록")
    
    if not st.session_state.history:
        st.caption("기록이 없습니다.")
    
    for h_ticker in st.session_state.history[:10]:
        h_col1, h_col2 = st.columns([4, 1])
        # 돋보기 아이콘 추가
        if h_col1.button(f"🔍 {h_ticker}", key=f"h_{h_ticker}", use_container_width=True):
            st.session_state.ticker_val = h_ticker
            st.session_state.run_analysis = True
            st.rerun()
        if h_col2.button("🗑️", key=f"d_{h_ticker}", help="기록 삭제"):
            st.session_state.history.remove(h_ticker)
            save_history(st.session_state.history)
            st.rerun()

# --- 5. 메인 분석 실행부 ---
if analyze_btn or st.session_state.run_analysis:
    st.session_state.run_analysis = False # 플래그 초기화
    
    # 버튼 클릭 시에도 히스토리 저장 로직 작동
    final_ticker = ticker_input if analyze_btn else st.session_state.ticker_val
    
    # 비어있지 않을 때만 저장
    if final_ticker and final_ticker not in st.session_state.history:
        st.session_state.history.insert(0, final_ticker)
        save_history(st.session_state.history)

    # 분석 실행
    analyzer = StockAnalyzer(final_ticker)
    if analyzer.fetch_data(start_d, end_d):
        analyzer.calculate_indicators()
        analyzer.get_signals()
        
        st.title(f"🛰️ {final_ticker} SYSTEM DIAGNOSTICS")
        analyzer.display_metrics()
        
        st.write("---")
        tab1, tab2, tab3 = st.tabs(["📊 ANALYSIS CHART", "💼 FINANCIAL DATA", "📜 RAW LOGS"])
        
        with tab1:
            analyzer.visualize()
        with tab2:
            st.subheader(f"{final_ticker} 분기별 통합 재무 리포트")
            analyzer.display_financials()
        with tab3:
            st.subheader("최신 30거래일 로우 데이터")
            # 확장 다운로드한 전체가 아니라, 실제 사용자가 보는 기간의 데이터만 표시
            raw_display_df = analyzer.df.loc[analyzer.display_start_date:].copy()
            st.dataframe(raw_display_df.tail(30), use_container_width=True)
