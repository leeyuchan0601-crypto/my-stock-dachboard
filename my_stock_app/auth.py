"""
'로그인'이라기보다는 '내 데이터 구분용 닉네임' 수준의 가벼운 사용자 식별 모듈.

⚠️ 주의: 비밀번호 검증이 없는 방식이라 진짜 보안 인증은 아님.
같은 닉네임을 아무나 입력하면 그 사람의 포트폴리오/검색 기록을 볼 수 있음.
여러 명이 실제로 쓰는 서비스로 키우려면 Streamlit의 st.login()(OIDC 기반, Google/GitHub
OAuth 앱 등록 필요)으로 교체하는 걸 권장.
"""
import streamlit as st


def ensure_user() -> str:
    if "user_id" not in st.session_state:
        st.session_state.user_id = "guest"
    return st.session_state.user_id


def user_switcher_widget():
    """사이드바에 닉네임 입력창을 그려서 데이터를 구분함."""
    ensure_user()
    with st.sidebar:
        st.caption("👤 내 데이터 구분용 닉네임")
        nickname = st.text_input(
            "닉네임",
            value=st.session_state.user_id,
            key="user_id_input",
            label_visibility="collapsed",
            help="같은 닉네임으로 접속하면 포트폴리오/검색 기록이 이어져요. 비밀번호는 없어요.",
        )
        cleaned = nickname.strip() if nickname else "guest"
        if cleaned != st.session_state.user_id:
            st.session_state.user_id = cleaned
            st.rerun()
