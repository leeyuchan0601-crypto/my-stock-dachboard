import streamlit as st
import yfinance as yf
import pandas as pd
from PIL import Image
import os

# --- 1. 페이지 설정 및 아이콘 ---
# pages 폴더 내부에 있으므로 상위 폴더의 이미지를 참조합니다.
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Currency", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Currency", page_icon="💱", layout="wide")

# --- 2. 하이테크 사이버펑크 스타일링 ---
st.markdown("""
    <style>
    /* 입력창 스타일 */
    .stNumberInput > div > div > input {
        background-color: rgba(0, 212, 255, 0.05);
        color: #00d4ff;
        border: 1px solid #00d4ff;
        font-size: 24px;
        font-weight: bold;
    }
    /* 결과 카드 스타일 */
    .converter-card {
        padding: 40px;
        background-color: rgba(0, 212, 255, 0.05);
        border: 2px solid rgba(0, 212, 255, 0.3);
        border-radius: 20px;
        text-align: center;
        box-shadow: 0 0 20px rgba(0, 212, 255, 0.1);
    }
    .result-val {
        color: #00d4ff;
        font-size: 48px;
        font-weight: 900;
        margin-bottom: 10px;
    }
    .sub-info {
        color: #888;
        font-size: 16px;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 실시간 환율 데이터 함수 (10분 캐싱) ---
@st.cache_data(ttl=600)
def get_exchange_rate(ticker):
    try:
        data = yf.Ticker(ticker).history(period="1d")
        if not data.empty:
            return data['Close'].iloc[-1]
        return None
    except:
        return None

# --- 4. 메인 UI ---
st.title("🛰️ ZION : TWO-WAY CURRENCY TERMINAL")
st.write("---")

# 통화 목록 및 티커
currencies = {
    "USD (미국 달러)": {"ticker": "USDKRW=X", "unit": "달러", "symbol": "$"},
    "JPY (일본 엔)": {"ticker": "JPYKRW=X", "unit": "엔", "symbol": "¥"},
    "EUR (유로)": {"ticker": "EURKRW=X", "unit": "유로", "symbol": "€"},
    "CNY (중국 위안)": {"ticker": "CNYKRW=X", "unit": "위안", "symbol": "¥"},
    "GBP (영국 파운드)": {"ticker": "GBPKRW=X", "unit": "파운드", "symbol": "£"}
}

col1, col2 = st.columns([1, 1.5])

with col1:
    st.subheader("🛠️ CONVERSION SETTING")
    
    # 1. 변환 방향 선택
    mode = st.radio(
        "변환 방향 선택",
        ["외화 ➔ 한국 돈(KRW)", "한국 돈(KRW) ➔ 외화"],
        horizontal=True
    )
    
    st.write("")
    
    # 2. 통화 선택
    selected_name = st.selectbox("대상 통화", list(currencies.keys()))
    curr_info = currencies[selected_name]
    
    # 3. 금액 입력
    input_label = "금액 입력 (" + ("KRW" if "한국 돈" in mode else curr_info['unit']) + ")"
    amount = st.number_input(input_label, min_value=0.0, value=1000.0 if "한국 돈" in mode else 1.0, step=100.0 if "한국 돈" in mode else 1.0)

with col2:
    rate = get_exchange_rate(curr_info['ticker'])
    
    if rate:
        # 엔화(JPY)는 100엔당 원화로 환산되는 특수성 처리
        is_jpy = "JPY" in selected_name
        base_rate = rate * 100 if is_jpy else rate
        
        st.subheader("💸 CALCULATION RESULT")
        
        if "한국 돈" in mode:
            # KRW -> Foreign
            # 엔화는 원화/환율 * 100
            result = (amount / base_rate) * 100 if is_jpy else (amount / base_rate)
            res_unit = curr_info['unit']
            res_symbol = curr_info['symbol']
            display_text = f"{res_symbol} {result:,.2f} {res_unit}"
            rate_info = f"적용 환율: 1 {res_unit} = {base_rate:,.2f} KRW"
        else:
            # Foreign -> KRW
            result = (amount / 100) * base_rate if is_jpy else amount * base_rate
            display_text = f"{result:,.0f} 원 (KRW)"
            rate_info = f"적용 환율: 1 {curr_info['unit']} = {base_rate:,.2f} KRW"

        # 결과 카드 출력
        st.markdown(f"""
            <div class="converter-card">
                <div class="result-val">{display_text}</div>
                <div class="sub-info">{rate_info}</div>
            </div>
            """, unsafe_allow_html=True)
        
        st.write("")
        st.caption(f"🕒 데이터 동기화: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M:%S')} (Yahoo Finance)")
    else:
        st.error("📡 통신 오류: 환율 데이터를 가져올 수 없습니다.")

st.write("---")
st.info("💡 일본 엔(JPY)의 경우 시장 관행에 따라 100엔 단위를 기준으로 계산되었습니다.")
