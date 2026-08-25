import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
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
        except Exception:
            return []
    return []

def save_history(history):
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f)

def on_ticker_enter():
    if "ticker_input_key" in st.session_state:
        input_val = st.session_state.ticker_input_key.upper().strip()
        if input_val:
            if input_val in st.session_state.history:
                st.session_state.history.remove(input_val)
            st.session_state.history.insert(0, input_val)
            save_history(st.session_state.history)
            st.session_state.ticker_val = input_val
            st.session_state.run_analysis = True

def select_quick_ticker(tk):
    st.session_state.ticker_val = tk
    st.session_state.ticker_input_key = tk
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

# --- 2. 라이트 모던 테마 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    h1, h3 { color: #0f172a !important; font-weight: 800 !important; }
    p, span, label { color: #475569; }

    div[data-testid="metric-container"] {
        background-color: #ffffff;
        border: 1px solid #e2e8f0;
        padding: 16px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
    }
    div[data-testid="metric-container"] label { color: #64748b !important; font-weight: 600; }
    div[data-testid="metric-container"] div { color: #0f172a !important; }

    .stTabs [data-baseweb="tab-list"] { gap: 20px; }
    .stTabs [data-baseweb="tab"] { height: 48px; font-weight: 700; }

    .quick-tk button {
        border-radius: 8px !important;
        border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important;
        color: #2563eb !important;
        font-weight: 700 !important;
    }
    .quick-tk button:hover {
        background-color: #2563eb !important;
        color: #ffffff !important;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 분석 클래스 ---
class StockAnalyzer():
    def __init__(self, ticker):
        self.ticker = ticker
        self.df = None
        self.display_start_date = None

    def fetch_data(self, start_date, end_date):
        self.display_start_date = start_date
        buffer_days = 40
        extended_start = start_date - datetime.timedelta(days=buffer_days)

        with st.spinner(f"📡 [ZION] {self.ticker} 동기화 중..."):
            try:
                data = yf.download(self.ticker, start=extended_start, end=end_date)
                if data.empty:
                    st.error("데이터가 없습니다. 종목 코드를 확인해주세요.")
                    return False
                if isinstance(data.columns, pd.MultiIndex):
                    data.columns = data.columns.get_level_values(0)
                self.df = data
                return True
            except Exception:
                st.error("데이터 수신 중 오류가 발생했습니다.")
                return False

    def calculate_indicators(self):
        if self.df is None:
            return
        self.df['MA5'] = self.df['Close'].rolling(5).mean()
        self.df['MA20'] = self.df['Close'].rolling(20).mean()
        delta = self.df['Close'].diff()
        up, down = delta.clip(lower=0), -delta.clip(upper=0)
        avg_up, avg_down = up.rolling(14).mean(), down.rolling(14).mean()
        rs = avg_up / avg_down
        self.df['RSI'] = 100 - (100 / (1 + rs))

    def get_signals(self):
        if self.df is None:
            return
        self.df['Signal'] = 0
        buy = (self.df['MA5'].shift(1) < self.df['MA20'].shift(1)) & (self.df['MA5'] > self.df['MA20']) & (self.df['RSI'] < 70)
        sell = (self.df['MA5'].shift(1) > self.df['MA20'].shift(1)) & (self.df['MA5'] < self.df['MA20']) & (self.df['RSI'] > 30)
        self.df.loc[buy, 'Signal'] = 1
        self.df.loc[sell, 'Signal'] = -1

    def get_display_df(self):
        return self.df.loc[self.display_start_date:].copy()

    def display_metrics(self):
        display_df = self.get_display_df()
        # 선택한 구간에 표시할 데이터가 2개 미만이면(전일 대비 계산 불가) 안내만 하고 종료
        if len(display_df) < 2:
            st.info("선택한 기간이 너무 짧아 전일 대비 정보를 계산할 수 없습니다. 시작일을 더 이전으로 넓혀주세요.")
            return
        last, prev = display_df.iloc[-1], display_df.iloc[-2]
        m1, m2, m3 = st.columns(3)
        curr_price = float(last['Close'])
        m1.metric("현재 주가", f"${curr_price:.2f}", f"{curr_price - float(prev['Close']):.2f}")
        rsi_val = last['RSI']
        m2.metric("RSI 지수", f"{float(rsi_val):.1f}" if pd.notna(rsi_val) else "N/A")
        recent_sig = display_df['Signal'].tail(3)
        sig_text = "🟢 BUY" if 1 in recent_sig.values else "🔴 SELL" if -1 in recent_sig.values else "⚪ HOLD"
        m3.metric("최근 시그널(3일)", sig_text)

    def display_financials(self):
        try:
            t_obj = yf.Ticker(self.ticker)
            df_all = pd.concat([t_obj.quarterly_financials, t_obj.quarterly_balance_sheet, t_obj.quarterly_cashflow])
            target = {
                'Total Revenue': '매출액', 'Gross Profit': '매출총이익', 'Operating Income': '영업이익',
                'Net Income': '당기순이익', 'EBITDA': 'EBITDA', 'Basic EPS': 'EPS',
                'Total Assets': '총 자산', 'Total Liabilities Net Minority Interest': '총 부채',
                'Total Debt': '총 차입금', 'Operating Cash Flow': '영업현금흐름',
                'Free Cash Flow': '잉여현금흐름(FCF)', 'Capital Expenditure': '재투자비용(CAPEX)'
            }
            available = [m for m in target.keys() if m in df_all.index]
            if not available:
                st.warning("재무 데이터가 제공되지 않는 종목입니다.")
                return
            df_res = df_all.loc[available].copy()
            df_res.index = [target[m] for m in available]

            def fmt(x):
                if pd.isna(x) or x == 0:
                    return "-"
                if -1000 < x < 1000:
                    return f"{x:.2f}"
                return f"{x / 1e9:,.2f} B"

            st.dataframe(df_res.map(fmt), use_container_width=True)
        except Exception:
            st.warning("재무 데이터 호출 실패")

    def visualize(self):
        if self.df is None:
            return
        display_df = self.get_display_df()

        fig = make_subplots(rows=2, cols=1, shared_xaxes=True,
                             vertical_spacing=0.05, row_heights=[0.7, 0.3])

        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['Close'], name='Price',
                                  line=dict(color='#0f172a', width=1.5), opacity=0.55), row=1, col=1)
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['MA5'], name='MA5',
                                  line=dict(color='#ef4444', width=2)), row=1, col=1)
        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['MA20'], name='MA20',
                                  line=dict(color='#2563eb', width=2)), row=1, col=1)

        buy_pts = display_df[display_df['Signal'] == 1]
        fig.add_trace(go.Scatter(x=buy_pts.index, y=buy_pts['Close'], mode='markers', name='BUY',
                                  marker=dict(symbol='triangle-up', size=13, color='#16a34a',
                                              line=dict(width=1, color='#ffffff'))), row=1, col=1)
        sell_pts = display_df[display_df['Signal'] == -1]
        fig.add_trace(go.Scatter(x=sell_pts.index, y=sell_pts['Close'], mode='markers', name='SELL',
                                  marker=dict(symbol='triangle-down', size=13, color='#dc2626',
                                              line=dict(width=1, color='#ffffff'))), row=1, col=1)

        fig.add_trace(go.Scatter(x=display_df.index, y=display_df['RSI'], name='RSI',
                                  line=dict(color='#7c3aed', width=1.5)), row=2, col=1)
        fig.add_trace(go.Scatter(x=display_df.index, y=[70] * len(display_df), name='Overbought',
                                  line=dict(color='#ef4444', width=1, dash='dash'), showlegend=False), row=2, col=1)
        fig.add_trace(go.Scatter(x=display_df.index, y=[30] * len(display_df), name='Oversold',
                                  line=dict(color='#16a34a', width=1, dash='dash'), showlegend=False), row=2, col=1)

        fig.update_layout(
            template='plotly_white',
            paper_bgcolor='#ffffff',
            plot_bgcolor='#ffffff',
            height=800,
            title_text=f"🛰️ {self.ticker} INTERACTIVE TERMINAL",
            hovermode='x unified',
            showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=50, b=10)
        )
        fig.update_yaxes(title_text="Price ($)", row=1, col=1, gridcolor="#e2e8f0")
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1, gridcolor="#e2e8f0")
        fig.update_xaxes(gridcolor="#e2e8f0")

        st.plotly_chart(fig, use_container_width=True)


# --- 4. 사이드바 및 히스토리 로직 ---
if 'history' not in st.session_state: st.session_state.history = load_history()
if 'ticker_val' not in st.session_state: st.session_state.ticker_val = "ORCL"
if 'run_analysis' not in st.session_state: st.session_state.run_analysis = False

with st.sidebar:
    st.header("🛸 ZION CONTROL")

    if "ticker_input_key" not in st.session_state or st.session_state.ticker_input_key != st.session_state.ticker_val:
        st.session_state.ticker_input_key = st.session_state.ticker_val

    ticker_input = st.text_input("종목 코드", key="ticker_input_key", on_change=on_ticker_enter).upper().strip()

    col1, col2 = st.columns(2)
    start_d = col1.date_input("시작일", datetime.date.today() - datetime.timedelta(days=180))
    end_d = col2.date_input("종료일", datetime.date.today())
    analyze_btn = st.button("SYSTEM START", type="primary", use_container_width=True)

    st.write("---")
    st.caption("⚡ 빠른 선택")
    quick_tickers = ["AAPL", "NVDA", "TSLA", "MSFT", "005930.KS", "SPY"]
    st.markdown('<div class="quick-tk">', unsafe_allow_html=True)
    qcols = st.columns(3)
    for i, tk in enumerate(quick_tickers):
        with qcols[i % 3]:
            st.button(
                tk,
                key=f"quick_{tk}",
                use_container_width=True,
                on_click=select_quick_ticker,
                args=(tk,),
            )
    st.markdown('</div>', unsafe_allow_html=True)

    st.write("---")
    st.subheader("📜 최근 검색 기록")
    if not st.session_state.history:
        st.caption("아직 검색 기록이 없습니다.")
    for h_ticker in st.session_state.history[:10]:
        h_col1, h_col2 = st.columns([4, 1])
        if h_col1.button(f"🔍 {h_ticker}", key=f"h_{h_ticker}", use_container_width=True):
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
    final_ticker = ticker_input if analyze_btn else st.session_state.ticker_val
    if final_ticker and final_ticker not in st.session_state.history:
        st.session_state.history.insert(0, final_ticker)
        save_history(st.session_state.history)

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
            analyzer.display_financials()
        with tab3:
            raw_df = analyzer.get_display_df().tail(30)
            st.dataframe(raw_df, use_container_width=True)
            st.download_button(
                "⬇️ CSV로 다운로드",
                data=raw_df.to_csv().encode("utf-8-sig"),
                file_name=f"{final_ticker}_raw_data.csv",
                mime="text/csv",
                use_container_width=True,
            )
else:
    st.title("🛰️ ZION ANALYZER")
    st.info("왼쪽 사이드바에서 종목 코드를 입력하거나, 빠른 선택 버튼을 눌러 분석을 시작하세요.")
