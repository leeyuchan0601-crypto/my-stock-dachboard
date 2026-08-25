import streamlit as st
from PIL import Image
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import theme
from auth import user_switcher_widget, ensure_user

image_path = "ark_base.png"
if os.path.exists(image_path):
    img = Image.open(image_path)
    st.set_page_config(page_title="ZION | Gateway", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Gateway", page_icon="🛰️", layout="wide")

theme.inject_base_css()
user_switcher_widget()
user_id = ensure_user()

st.markdown("""
    <style>
    .zion-hero { text-align: center; padding: 8px 0 4px 0; }
    .zion-tagline { color: #64748b; font-size: 18px; margin-top: -8px; }
    .card-icon { font-size: 32px; margin-bottom: 4px; }
    .card-title { font-size: 19px; font-weight: 800; color: #0f172a; margin-bottom: 4px; }
    .card-desc { font-size: 13px; color: #64748b; min-height: 58px; }
    </style>
    """, unsafe_allow_html=True)

if os.path.exists(image_path):
    col_l, col_c, col_r = st.columns([1, 1, 1])
    with col_c:
        st.image(image_path, use_container_width=True)

st.markdown('<div class="zion-hero">', unsafe_allow_html=True)
st.title("ZION")
st.markdown('<p class="zion-tagline">금융의 심연을 꿰뚫는 최후의 시선</p>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)
st.caption(f"👋 {user_id}님, 환영합니다.")
st.write("---")

pages = [
    ("📈", "ZION Analyzer", "기술적 지표·매매 시그널·백테스트·종목 비교를 한 곳에서.", "pages/1_ZION_Analyzer.py", "btn_analyzer"),
    ("💱", "Currency Converter", "실시간 환율로 원화/외화를 양방향 즉시 변환.", "pages/2_Currency_Converter.py", "btn_currency"),
    ("🗺️", "Market Heatmap", "섹터별 등락률을 트리맵으로 한눈에.", "pages/3_Market_Heatmap.py", "btn_heatmap"),
    ("💼", "Portfolio", "내 보유 종목의 실시간 평가손익을 추적.", "pages/4_Portfolio.py", "btn_portfolio"),
    ("🔔", "Alerts", "관심 종목의 매수/매도 시그널을 Slack으로 알림.", "pages/5_Alerts.py", "btn_alerts"),
]

row1 = st.columns(3, gap="large")
row2 = st.columns(3, gap="large")
slots = row1 + row2

for slot, (icon, title, desc, target, key) in zip(slots, pages):
    with slot:
        with st.container(border=True):
            st.markdown(f'<div class="card-icon">{icon}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-title">{title}</div>', unsafe_allow_html=True)
            st.markdown(f'<div class="card-desc">{desc}</div>', unsafe_allow_html=True)
            if st.button(f"{icon} 열기", use_container_width=True, key=key):
                st.switch_page(target)

st.write("")
st.caption("좌측 사이드바에서도 언제든 페이지를 이동할 수 있어요.")
