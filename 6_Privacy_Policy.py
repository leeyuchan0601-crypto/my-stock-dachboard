import streamlit as st
import os
from PIL import Image

# --- 1. 페이지 설정 및 아이콘 ---
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Privacy Policy", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Privacy Policy", page_icon="⚖️", layout="wide")

# --- 2. 하이테크 스타일링 CSS ---
st.markdown("""
    <style>
    .policy-container {
        background-color: rgba(0, 212, 255, 0.05);
        border: 1px solid rgba(0, 212, 255, 0.2);
        padding: 30px;
        border-radius: 10px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.3);
        margin-bottom: 20px;
    }
    .policy-title {
        color: #00d4ff;
        border-bottom: 1px solid #00d4ff;
        padding-bottom: 10px;
        margin-bottom: 20px;
    }
    .policy-subtitle {
        color: #ff0055;
        margin-top: 20px;
    }
    .stMarkdown p {
        color: #e0e0e0;
        line-height: 1.6;
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 메인 콘텐츠 렌더링 ---
st.title("⚖️ ZION : PRIVACY POLICY (개인정보처리방침)")
st.write("본 서비스(ZION)는 사용자의 개인정보를 소중히 다루며, 관련 법령을 준수합니다.")
st.write("---")

st.markdown('<div class="policy-container">', unsafe_allow_html=True)

st.markdown('<h3 class="policy-title">제1조 (개인정보의 처리 목적)</h3>', unsafe_allow_html=True)
st.markdown("""
ZION(이하 '서비스')은(는) 다음의 목적을 위하여 개인정보를 처리합니다. 처리하고 있는 개인정보는 다음의 목적 이외의 용도로는 이용되지 않으며, 이용 목적이 변경되는 경우에는 별도의 동의를 받는 등 필요한 조치를 이행할 예정입니다.
1. **Google OAuth 로그인 연동:** 사용자 식별 및 맞춤형 서비스(포트폴리오, 관심종목 등) 제공
2. **서비스 제공 및 유지보수:** 사용자 설정 저장(검색 기록, 포트폴리오 데이터, 알림 설정 등)
""")

st.markdown('<h3 class="policy-title">제2조 (처리하는 개인정보의 항목)</h3>', unsafe_allow_html=True)
st.markdown("""
본 서비스는 다음의 개인정보 항목을 처리하고 있습니다.
* **필수 수집 항목:** Google 계정 정보 (이메일 주소, 이름, 프로필 사진 식별자)
* **서비스 이용 중 생성되는 데이터:** 주식 검색 기록, 포트폴리오 내역(매수 단가/수량), 관심 종목 리스트, Slack Webhook URL (단, Webhook URL은 브라우저 로컬 세션에만 임시 저장되며 서버 DB에 영구 저장되지 않습니다.)
""")

st.markdown('<h3 class="policy-title">제3조 (개인정보의 처리 및 보유 기간)</h3>', unsafe_allow_html=True)
st.markdown("""
본 서비스는 원칙적으로 사용자가 서비스 탈퇴(또는 Google 계정 연동 해제) 시 해당 사용자의 모든 개인정보 및 데이터를 지체 없이 파기합니다.
* 내부 DB(SQLite)에 저장된 사용자 맞춤 데이터는 서비스 이용 기간 동안만 보관됩니다.
""")

st.markdown('<h3 class="policy-title">제4조 (개인정보의 제3자 제공 및 위탁)</h3>', unsafe_allow_html=True)
st.markdown("""
본 서비스는 원칙적으로 사용자의 개인정보를 제3자에게 제공하거나 외부에 위탁하지 않습니다. 단, 서비스 인프라 제공을 위해 Streamlit Cloud 서버를 활용하고 있으며, 주식 데이터 조회를 위해 yfinance(Yahoo Finance API)를 이용합니다. (API 호출 과정에서 사용자의 개인정보는 전송되지 않습니다.)
""")

st.markdown('<h3 class="policy-title">제5조 (사용자의 권리 및 행사 방법)</h3>', unsafe_allow_html=True)
st.markdown("""
사용자는 언제든지 Google 계정 보안 설정에서 본 서비스에 대한 접근 권한을 철회(연동 해제)할 수 있습니다. 
서비스 관련 데이터 삭제를 원하실 경우, 서비스 관리자에게 문의해 주시면 신속하게 처리하겠습니다.
""")

st.markdown('<h3 class="policy-title">제6조 (면책 조항)</h3>', unsafe_allow_html=True)
st.markdown("""
본 서비스에서 제공하는 주가 정보 및 분석 데이터는 투자 참고용이며, 실제 시장 데이터와 지연(Delay) 또는 오차가 발생할 수 있습니다. 
본 서비스는 투자 결과에 대한 법적 책임을 지지 않으며, 최종 투자 판단의 책임은 전적으로 사용자 본인에게 있습니다.
""")

st.markdown('</div>', unsafe_allow_html=True)

st.write("---")
st.caption("시행일자: 2024년 (최초 제정)")