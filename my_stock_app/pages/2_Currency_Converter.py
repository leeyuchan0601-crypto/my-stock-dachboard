import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import theme
from auth import require_login, ensure_user


@st.cache_data(ttl=600)
def get_rate(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
    except Exception:
        return None


@st.cache_data(ttl=600)
def get_rate_history(ticker, period="7d"):
    try:
        data = yf.Ticker(ticker).history(period=period)
        return data if not data.empty else None
    except Exception:
        return None


def sync_foreign_to_krw():
    rate = st.session_state.current_rate
    is_jpy = "JPY" in st.session_state.selected_curr
    base_rate = rate * 100 if is_jpy else rate
    amount = st.session_state.foreign_input
    st.session_state.krw_input = (amount / 100 * base_rate) if is_jpy else (amount * base_rate)


def sync_krw_to_foreign():
    rate = st.session_state.current_rate
    is_jpy = "JPY" in st.session_state.selected_curr
    base_rate = rate * 100 if is_jpy else rate
    amount = st.session_state.krw_input
    st.session_state.foreign_input = (amount / base_rate * 100) if is_jpy else (amount / base_rate)


def set_preset_amount(value):
    st.session_state.foreign_input = float(value)
    sync_foreign_to_krw()


current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Currency", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Currency", page_icon="Z", layout="wide")

theme.inject_base_css()
require_login()
ensure_user()

st.markdown("""
    <style>
    .stNumberInput > div > div > input {
        background-color: #ffffff; color: #2563eb; border: 1.5px solid #2563eb;
        font-size: 30px !important; font-weight: 800; height: 68px; text-align: center; border-radius: 10px;
    }
    .curr-label { font-size: 18px; color: #0f172a; font-weight: 700; margin-bottom: 8px; text-align: center; }
    .sync-icon { font-size: 34px; text-align: center; margin-top: 40px; color: #94a3b8; }
    .preset button {
        border-radius: 8px !important; border: 1px solid #e2e8f0 !important;
        background-color: #ffffff !important; color: #2563eb !important; font-weight: 700 !important;
    }
    .preset button:hover { background-color: #2563eb !important; color: #ffffff !important; }
    </style>
    """, unsafe_allow_html=True)

theme.page_header("DUAL-SYNC CURRENCY TERMINAL", icon="")
st.write("---")

currencies = {
    "USD (미국 달러)": {"ticker": "USDKRW=X", "unit": "USD"},
    "JPY (일본 엔)": {"ticker": "JPYKRW=X", "unit": "JPY"},
    "EUR (유로)": {"ticker": "EURKRW=X", "unit": "EUR"},
    "CNY (중국 위안)": {"ticker": "CNYKRW=X", "unit": "CNY"}
}

if 'foreign_input' not in st.session_state: st.session_state.foreign_input = 1.0
if 'krw_input' not in st.session_state: st.session_state.krw_input = 1350.0
if 'selected_curr' not in st.session_state: st.session_state.selected_curr = "USD (미국 달러)"

col_sel, _ = st.columns([2, 3])
with col_sel:
    new_curr = st.selectbox("변환 대상 통화 선택", list(currencies.keys()), key="selected_curr")
    rate = get_rate(currencies[new_curr]['ticker'])
    st.session_state.current_rate = rate

if rate:
    st.write("")
    c1, c2, c3 = st.columns([5, 1, 5])

    with c1:
        st.markdown(f'<div class="curr-label">{new_curr}</div>', unsafe_allow_html=True)
        st.number_input("외화 입력", key="foreign_input", on_change=sync_foreign_to_krw, label_visibility="collapsed")
        st.markdown('<div class="preset">', unsafe_allow_html=True)
        p1, p2, p3, p4 = st.columns(4)
        for col, val in zip([p1, p2, p3, p4], [1, 100, 1000, 10000]):
            with col:
                st.button(f"{val:,}", key=f"preset_{val}", use_container_width=True,
                          on_click=set_preset_amount, args=(val,))
        st.markdown('</div>', unsafe_allow_html=True)

    with c2:
        st.markdown('<div class="sync-icon">=</div>', unsafe_allow_html=True)

    with c3:
        st.markdown('<div class="curr-label">KRW (대한민국 원)</div>', unsafe_allow_html=True)
        st.number_input("원화 입력", key="krw_input", on_change=sync_krw_to_foreign, label_visibility="collapsed")

    st.write("---")
    is_jpy = "JPY" in new_curr
    display_rate = rate * 100 if is_jpy else rate
    unit_text = "100엔" if is_jpy else f"1 {currencies[new_curr]['unit']}"

    st.subheader("실시간 시장 지표")
    m1, m2, m3 = st.columns(3)
    m1.metric("기준 환율", f"{display_rate:,.2f} KRW", help=f"{unit_text} 당 가격")
    m2.metric("통화 기호", currencies[new_curr]['unit'])
    m3.metric("데이터 소스", "Yahoo Finance")
    st.caption(f"최종 업데이트: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

    st.write("---")
    st.subheader("최근 1년 환율 추이")
    hist = get_rate_history(currencies[new_curr]['ticker'], period="1y")
    if hist is not None and not hist.empty:
        trend_series = hist['Close'] * 100 if is_jpy else hist['Close']
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=hist.index, y=trend_series, mode='lines+markers',
                                  line=dict(color='#2563eb', width=2.5), marker=dict(size=5, color='#2563eb'),
                                  fill='tozeroy', fillcolor='rgba(37, 99, 235, 0.08)'))
        fig.update_layout(template='plotly_white', paper_bgcolor='#ffffff', plot_bgcolor='#ffffff',
                           height=280, margin=dict(l=10, r=10, t=10, b=10),
                           yaxis=dict(title=f"KRW / {unit_text}", gridcolor="#e2e8f0"),
                           xaxis=dict(gridcolor="#e2e8f0"))
        st.plotly_chart(fig, use_container_width=True)
    else:
        st.caption("추이 데이터를 불러오지 못했습니다.")
else:
    st.error("외계 신호 간섭(데이터 로드 실패): 환율 정보를 가져올 수 없습니다.")

st.write("---")
st.info("입력창에 숫자를 치고 엔터를 누르면 반대편 통화가 즉시 동기화돼요. 자주 쓰는 금액은 프리셋 버튼으로 바로 입력할 수 있어요.")
