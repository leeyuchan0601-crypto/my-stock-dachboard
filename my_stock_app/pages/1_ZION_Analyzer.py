import streamlit as st
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import yfinance as yf
import pandas as pd
import datetime
from PIL import Image
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import theme
import db
from auth import require_login, ensure_user


def select_quick_ticker(tk):
    st.session_state.ticker_val = tk
    st.session_state.ticker_input_key = tk
    st.session_state.run_analysis = True


# --- 페이지 설정 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Analyzer", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Analyzer", page_icon="📈", layout="wide")

theme.inject_base_css()
require_login()
USER_ID = ensure_user()


# --- 분석 클래스 ---
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
                data = yf.download(self.ticker, start=extended_start, end=end_date, threads=True)
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
            template='plotly_white', paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
            height=800, title_text=f"🛰️ {self.ticker} INTERACTIVE TERMINAL",
            hovermode='x unified', showlegend=True,
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
            margin=dict(l=10, r=10, t=50, b=10)
        )
        fig.update_yaxes(title_text="Price ($)", row=1, col=1, gridcolor="#e2e8f0")
        fig.update_yaxes(title_text="RSI", range=[0, 100], row=2, col=1, gridcolor="#e2e8f0")
        fig.update_xaxes(gridcolor="#e2e8f0")

        st.plotly_chart(fig, use_container_width=True)

    def run_backtest(self):
        """MA5/MA20 크로스 전략을 신호대로 매매했을 때의 누적 수익률 vs Buy&Hold 비교."""
        display_df = self.get_display_df()
        if len(display_df) < 10:
            st.info("백테스트를 하기엔 구간이 너무 짧습니다. 최소 몇 주 이상의 기간을 선택해주세요.")
            return

        position = 0
        entry_price = 0.0
        trades = []
        equity = 1.0
        equity_curve = []

        for _, row in display_df.iterrows():
            price = float(row['Close'])
            if position == 0 and row['Signal'] == 1:
                position = 1
                entry_price = price
            elif position == 1 and row['Signal'] == -1:
                ret = (price - entry_price) / entry_price
                equity *= (1 + ret)
                trades.append(ret)
                position = 0
            equity_curve.append(equity * ((price / entry_price) if position == 1 else 1))

        strategy_return = (equity - 1) * 100
        buyhold_return = (float(display_df['Close'].iloc[-1]) / float(display_df['Close'].iloc[0]) - 1) * 100
        win_trades = [t for t in trades if t > 0]
        win_rate = (len(win_trades) / len(trades) * 100) if trades else 0.0

        b1, b2, b3, b4 = st.columns(4)
        b1.metric("전략 누적 수익률", f"{strategy_return:+.2f}%")
        b2.metric("단순 보유(Buy&Hold)", f"{buyhold_return:+.2f}%")
        b3.metric("완결된 매매 횟수", f"{len(trades)} 회")
        b4.metric("승률", f"{win_rate:.1f}%" if trades else "N/A")

        if strategy_return > buyhold_return:
            st.success(f"이 구간에서는 MA크로스 전략이 단순 보유보다 {strategy_return - buyhold_return:+.2f}%p 더 나았습니다.")
        else:
            st.warning(f"이 구간에서는 단순 보유가 전략보다 {buyhold_return - strategy_return:+.2f}%p 더 나았습니다.")

        eq_df = pd.DataFrame({"날짜": display_df.index, "전략 자산 추이": equity_curve})
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=eq_df["날짜"], y=eq_df["전략 자산 추이"], name="전략",
                                  line=dict(color="#2563eb", width=2)))
        bh_curve = display_df['Close'] / float(display_df['Close'].iloc[0])
        fig.add_trace(go.Scatter(x=display_df.index, y=bh_curve, name="Buy & Hold",
                                  line=dict(color="#94a3b8", width=2, dash="dash")))
        fig.update_layout(template='plotly_white', paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
                           height=380, margin=dict(l=10, r=10, t=30, b=10),
                           yaxis=dict(title="자산 배수(시작=1.0)", gridcolor="#e2e8f0"),
                           xaxis=dict(gridcolor="#e2e8f0"))
        st.plotly_chart(fig, use_container_width=True)
        st.caption("⚠️ 과거 데이터 기반 시뮬레이션이며, 수수료·세금·슬리피지는 반영되지 않았습니다. 실제 투자 성과와 다를 수 있습니다.")


@st.cache_data(ttl=600)
def fetch_compare_series(tickers, start, end):
    out = {}
    for tk in tickers:
        try:
            data = yf.download(tk, start=start, end=end, threads=True)
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)
            if not data.empty:
                out[tk] = data['Close']
        except Exception:
            continue
    return out


def render_compare_tab(default_ticker, start_d, end_d):
    st.caption("여러 종목의 수익률을 시작일 기준 100으로 정규화해서 비교합니다.")
    candidates = list(dict.fromkeys([default_ticker] + db.get_history(USER_ID, limit=15)))
    picked = st.multiselect("비교할 종목 선택 (최대 5개)", options=candidates,
                             default=candidates[:min(2, len(candidates))], max_selections=5)
    extra = st.text_input("직접 추가 (쉼표로 구분, 예: AAPL,MSFT)")
    if extra:
        picked += [t.strip().upper() for t in extra.split(",") if t.strip()]
    picked = list(dict.fromkeys(picked))

    if len(picked) < 2:
        st.info("2개 이상의 종목을 선택하면 비교 차트가 나타납니다.")
        return

    series_map = fetch_compare_series(tuple(picked), start_d, end_d)
    if not series_map:
        st.error("비교할 데이터를 불러오지 못했습니다.")
        return

    fig = go.Figure()
    palette = ["#2563eb", "#16a34a", "#dc2626", "#7c3aed", "#f59e0b"]
    for i, (tk, series) in enumerate(series_map.items()):
        normalized = series / series.iloc[0] * 100
        fig.add_trace(go.Scatter(x=normalized.index, y=normalized, name=tk,
                                  line=dict(color=palette[i % len(palette)], width=2)))
    fig.update_layout(template='plotly_white', paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
                       height=450, margin=dict(l=10, r=10, t=30, b=10),
                       yaxis=dict(title="정규화 지수(시작=100)", gridcolor="#e2e8f0"),
                       xaxis=dict(gridcolor="#e2e8f0"),
                       legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1))
    st.plotly_chart(fig, use_container_width=True)


# --- 사이드바 ---
if 'ticker_val' not in st.session_state: st.session_state.ticker_val = "ORCL"
if 'run_analysis' not in st.session_state: st.session_state.run_analysis = False

with st.sidebar:
    st.header("🛸 ZION CONTROL")

    if "ticker_input_key" not in st.session_state or st.session_state.ticker_input_key != st.session_state.ticker_val:
        st.session_state.ticker_input_key = st.session_state.ticker_val

    def on_ticker_enter():
        if "ticker_input_key" in st.session_state:
            input_val = st.session_state.ticker_input_key.upper().strip()
            if input_val:
                st.session_state.ticker_val = input_val
                st.session_state.run_analysis = True

    ticker_input = st.text_input("종목 코드", key="ticker_input_key", on_change=on_ticker_enter).upper().strip()

    col1, col2 = st.columns(2)
    start_d = col1.date_input("시작일", datetime.date.today() - datetime.timedelta(days=180))
    end_d = col2.date_input("종료일", datetime.date.today())
    analyze_btn = st.button("SYSTEM START", type="primary", use_container_width=True)

    st.write("---")
    st.caption("⚡ 빠른 선택")
    quick_tickers = ["AAPL", "NVDA", "TSLA", "MSFT", "005930.KS", "SPY"]
    qcols = st.columns(3)
    for i, tk in enumerate(quick_tickers):
        with qcols[i % 3]:
            st.button(tk, key=f"quick_{tk}", use_container_width=True,
                      on_click=select_quick_ticker, args=(tk,))

    st.write("---")
    st.subheader("📜 최근 검색 기록")
    history = db.get_history(USER_ID, limit=10)
    if not history:
        st.caption("아직 검색 기록이 없습니다.")
    for h_ticker in history:
        h_col1, h_col2 = st.columns([4, 1])
        if h_col1.button(f"🔍 {h_ticker}", key=f"h_{h_ticker}", use_container_width=True):
            st.session_state.ticker_val = h_ticker
            st.session_state.run_analysis = True
            st.rerun()
        if h_col2.button("🗑️", key=f"d_{h_ticker}"):
            db.delete_history(USER_ID, h_ticker)
            st.rerun()

# --- 메인 실행부 ---
if analyze_btn or st.session_state.run_analysis:
    st.session_state.run_analysis = False
    final_ticker = ticker_input if analyze_btn else st.session_state.ticker_val
    if final_ticker:
        db.add_history(USER_ID, final_ticker)

    analyzer = StockAnalyzer(final_ticker)
    if analyzer.fetch_data(start_d, end_d):
        analyzer.calculate_indicators()
        analyzer.get_signals()
        theme.page_header(f"{final_ticker} SYSTEM DIAGNOSTICS")
        analyzer.display_metrics()
        st.write("---")
        tab1, tab2, tab3, tab4, tab5 = st.tabs(
            ["📊 CHART", "🧪 BACKTEST", "🔍 COMPARE", "💼 FINANCIALS", "📜 RAW LOGS"]
        )
        with tab1:
            analyzer.visualize()
        with tab2:
            analyzer.run_backtest()
        with tab3:
            render_compare_tab(final_ticker, start_d, end_d)
        with tab4:
            analyzer.display_financials()
        with tab5:
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
    theme.page_header("ZION ANALYZER", "왼쪽 사이드바에서 종목 코드를 입력하거나, 빠른 선택 버튼을 눌러 분석을 시작하세요.")
