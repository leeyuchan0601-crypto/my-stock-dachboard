import streamlit as st
from PIL import Image
import os

# --- 페이지 설정 ---
image_path = "ark_base.png"
if os.path.exists(image_path):
    img = Image.open(image_path)
    st.set_page_config(page_title="ZION | Gateway", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Gateway", page_icon="🛰️", layout="wide")

# --- 라이트 모던 테마 CSS ---
st.markdown("""
    <style>
    .stApp { background-color: #f8fafc; }
    h1 { color: #0f172a !important; font-weight: 800 !important; letter-spacing: -0.5px; }
    h3 { color: #0f172a !important; font-weight: 700 !important; }
    p, span, label { color: #475569; }

    .zion-hero {
        text-align: center;
        padding: 8px 0 4px 0;
    }
    .zion-tagline {
        color: #64748b;
        font-size: 18px;
        margin-top: -8px;
    }

    div[data-testid="stVerticalBlockBorderWrapper"] {
        background-color: #ffffff;
        border-radius: 16px;
        border: 1px solid #e2e8f0;
        box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
        transition: box-shadow 0.2s ease, transform 0.2s ease;
    }
    div[data-testid="stVerticalBlockBorderWrapper"]:hover {
        box-shadow: 0 8px 20px rgba(37, 99, 235, 0.12);
        transform: translateY(-2px);
    }

    .stButton>button {
        width: 100%;
        height: 56px;
        font-size: 16px !important;
        font-weight: 700;
        background-color: #2563eb;
        border: none;
        color: #ffffff;
        border-radius: 10px;
        transition: 0.2s;
    }
    .stButton>button:hover {
        background-color: #1d4ed8;
        box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
    }
    .card-icon { font-size: 34px; margin-bottom: 4px; }
    .card-title { font-size: 20px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
    .card-desc { font-size: 14px; color: #64748b; min-height: 44px; }
    </style>
    """, unsafe_allow_html=True)

# --- 메인 이미지 / 헤더 ---
if os.path.exists(image_path):
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.image(image_path, use_container_width=True)

st.markdown('<div class="zion-hero">', unsafe_allow_html=True)
st.title("ZION")
st.markdown('<p class="zion-tagline">금융의 심연을 꿰뚫는 최후의 시선</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.write("")
st.write("---")

# --- 기능 카드 3분할 ---
col1, col2, col3 = st.columns(3, gap="large")

with col1:
    with st.container(border=True):
        st.markdown('<div class="card-icon">📈</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">ZION Analyzer</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-desc">종목별 기술적 지표(MA, RSI)와 매수/매도 시그널, 재무 데이터를 한눈에 분석합니다.</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("🚀 ANALYZER 열기", use_container_width=True, key="btn_analyzer"):
            st.switch_page("pages/1_ZION_Analyzer.py")

with col2:
    with st.container(border=True):
        st.markdown('<div class="card-icon">💱</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Currency Converter</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-desc">실시간 환율로 원화와 주요 외화(USD·JPY·EUR·CNY)를 양방향으로 즉시 변환합니다.</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("💱 CONVERTER 열기", use_container_width=True, key="btn_currency"):
            st.switch_page("pages/2_Currency_Converter.py")

with col3:
    with st.container(border=True):
        st.markdown('<div class="card-icon">🗺️</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-title">Market Heatmap</div>', unsafe_allow_html=True)
        st.markdown('<div class="card-desc">KOSPI·미국 주요 종목의 당일 등락률을 섹터별 트리맵으로 한눈에 파악합니다.</div>', unsafe_allow_html=True)
        st.write("")
        if st.button("🗺️ HEATMAP 열기", use_container_width=True, key="btn_heatmap"):
            st.switch_page("pages/3_Market_Heatmap.py")

st.write("")
st.caption("좌측 사이드바에서도 언제든 페이지를 이동할 수 있어요.")
