import streamlit as st
import yfinance as yf
import pandas as pd
from PIL import Image
import os

# --- 0. 환율 동기화 및 계산 로직 ---
@st.cache_data(ttl=600)
def get_rate(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
    except:
        return None

def sync_foreign_to_krw():
    # 외화 입력 시 원화 업데이트
    rate = st.session_state.current_rate
    is_jpy = "JPY" in st.session_state.selected_curr
    base_rate = rate * 100 if is_jpy else rate
    
    amount = st.session_state.foreign_input
    if is_jpy:
        st.session_state.krw_input = (amount / 100) * base_rate
    else:
        st.session_state.krw_input = amount * base_rate

def sync_krw_to_foreign():
    # 원화 입력 시 외화 업데이트
    rate = st.session_state.current_rate
    is_jpy = "JPY" in st.session_state.selected_curr
    base_rate = rate * 100 if is_jpy else rate
    
    amount = st.session_state.krw_input
    if is_jpy:
        st.session_state.foreign_input = (amount / base_rate) * 100
    else:
        st.session_state.foreign_input = amount / base_rate

# --- 1. 페이지 설정 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Currency", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Currency", page_icon="💱", layout="wide")

# --- 2. 사이버펑크 스타일링 ---
st.markdown("""
    <style>
    .stNumberInput > div > div > input {
        background-color: rgba(0, 212, 255, 0.05);
        color: #00d4ff;
        border: 1px solid #00d4ff;
        font-size: 32px !important;
        font-weight: 900;
        height: 70px;
        text-align: center;
    }
    .curr-label {
        font-size: 20px;
        color: #00d4ff;
        font-weight: bold;
        margin-bottom: 10px;
        text-align: center;
    }
    .sync-icon {
        font-size: 40px;
        text-align: center;
        margin-top: 45px;
        color: rgba(0, 212, 255, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)

st.title("🛰️ ZION : DUAL-SYNC CURRENCY TERMINAL")
st.write("---")

# --- 3. 세션 상태 초기화 ---
currencies = {
    "USD (미국 달러)": {"ticker": "USDKRW=X", "unit": "USD"},
    "JPY (일본 엔)": {"ticker": "JPYKRW=X", "unit": "JPY"},
    "EUR (유로)": {"ticker": "EURKRW=X", "unit": "EUR"},
    "CNY (중국 위안)": {"ticker": "CNYKRW=X", "unit": "CNY"}
}

if 'foreign_input' not in st.session_state: st.session_state.foreign_input = 1.0
if 'krw_input' not in st.session_state: st.session_state.krw_input = 1350.0 # 초기 대략값
if 'selected_curr' not in st.session_state: st.session_state.selected_curr = "USD (미국 달러)"

# --- 4. 메인 UI ---
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
        st.number_input(
            "외화 입력",
            key="foreign_input",
            on_change=sync_foreign_to_krw,
            label_visibility="collapsed"
        )
        
    with c2:
        st.markdown('<div class="sync-icon">⇆</div>', unsafe_allow_html=True)
        
    with c3:
        st.markdown('<div class="curr-label">KRW (대한민국 원)</div>', unsafe_allow_html=True)
        st.number_input(
            "원화 입력",
            key="krw_input",
            on_change=sync_krw_to_foreign,
            label_visibility="collapsed"
        )

    st.write("---")
    # 현재 환율 정보 요약
    is_jpy = "JPY" in new_curr
    display_rate = rate * 100 if is_jpy else rate
    unit_text = "100엔" if is_jpy else f"1 {currencies[new_curr]['unit']}"
    
    st.subheader("📊 실시간 시장 지표")
    m1, m2, m3 = st.columns(3)
    m1.metric("기준 환율", f"{display_rate:,.2f} KRW", help=f"{unit_text} 당 가격")
    m2.metric("통화 기호", currencies[new_curr]['unit'])
    m3.metric("데이터 소스", "Yahoo Finance")
    
    st.caption(f"🕒 최종 업데이트: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")

else:
    st.error("📡 외계 신호 간섭(데이터 로드 실패): 환율 정보를 가져올 수 없습니다.")

st.write("---")
st.info("💡 입력창에 숫자를 치고 엔터를 누르면 반대편 통화가 즉시 동기화됩니다.")
