import streamlit as st
import os

# 페이지 설정
st.set_page_config(page_title="ZION | Gateway", page_icon="🛰️", layout="wide")

# CSS로 하이테크 스타일링
st.markdown("""
    <style>
    .main { background-color: #0e1117; }
    .stButton>button {
        width: 100%;
        height: 80px;
        font-size: 20px !important;
        background-color: rgba(0, 212, 255, 0.1);
        border: 2px solid #00d4ff;
        color: #00d4ff;
        border-radius: 10px;
        transition: 0.3s;
    }
    .stButton>button:hover {
        background-color: #00d4ff;
        color: black;
        box-shadow: 0 0 20px #00d4ff;
    }
    </style>
    """, unsafe_allow_html=True)

# 메인 이미지 출력
image_path = "ark_base.png"
if os.path.exists(image_path):
    st.image(image_path, use_container_width=True)

st.title("🛰️ SYSTEM ZION")
st.subheader("금융의 심연을 꿰뚫는 최후의 시선")
st.write("---")

# 입장 버튼
if st.button("🚀 ENTER ZION ANALYZER"):
    st.switch_page("pages/1_ZION_Analyzer.py")