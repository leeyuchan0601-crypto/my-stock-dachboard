import streamlit as st
import yfinance as yf
import pandas as pd
from PIL import Image
import os

# 1. 페이지 설정
parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Currency", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Currency", page_icon="💱", layout="wide")

# 2. 하이테크 스타일링
st.markdown("""
    <style>
    .stNumberInput > div > div > input {
        background-color: rgba(0, 212, 255, 0.05);
        color: #00d4ff;
        border: 1px solid #00d4ff;
        font-size: 24px;
    }
    .converter-card {
        padding: 30px;
        background-color: rgba(0, 212, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.2);
        border-radius: 15px;
        text-align: center;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("ZION : CURRENCY CONVERTER")
st.subheader("실시간 환율 동기화 및 계산기")
st.write("---")

# 3. 환율 데이터 가져오기 함수
@st.cache_data(ttl=600) # 10분 동안 결과 캐싱
def get_exchange_rate(ticker):
    data = yf.Ticker(ticker).history(period="1d")
    if not data.empty:
        return data['Close'].iloc[-1]
    return None

# 4. 입력 UI 구성
currencies = {
    "USD (미국 달러)": "USDKRW=X",
    "JPY (일본 엔)": "JPYKRW=X",
    "EUR (유로)": "EURKRW=X",
    "CNY (중국 위안)": "CNYKRW=X",
    "GBP (영국 파운드)": "GBPKRW=X"
}

col1, col2 = st.columns(2)

with col1:
    st.markdown("### 계산 설정")
    selected_name = st.selectbox("변환할 통화 선택", list(currencies.keys()))
    amount = st.number_input("금액 입력", min_value=0.0, value=1.0, step=1.0)

with col2:
    ticker = currencies[selected_name]
    rate = get_exchange_rate(ticker)
    
    if rate:
        # 엔화는 보통 100엔 기준이므로 별도 처리
        actual_rate = rate if "JPY" not in selected_name else rate * 100
        result = amount * actual_rate
        
        st.markdown(f"### 변환 결과 ({selected_name.split()[0]} → KRW)")
        st.markdown(f"""
            <div class="converter-card">
                <h1 style='color: #00d4ff; margin-bottom: 0;'>{result:,.2f} 원</h1>
                <p style='color: #888;'>적용 환율: 1 {selected_name.split()[0]} = {actual_rate:,.2f} KRW</p>
            </div>
            """, unsafe_allow_html=True)
        
        st.caption(f"최근 동기화 시각: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')}")
    else:
        st.error("환율 데이터를 불러오는 데 실패했습니다.")

st.write("---")
st.info("위 환율은 야후 파이낸스(Yahoo Finance) 기준이며 실거래 환율과는 차이가 있을 수 있습니다.")
