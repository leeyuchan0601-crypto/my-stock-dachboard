"""
Streamlit 내장 OIDC 로그인(st.login/st.user) 래퍼.

전제 조건 (앱 소유자가 사전에 해야 하는 일):
1. Google Cloud Console(또는 GitHub Developer Settings)에서 OAuth 클라이언트를 등록
2. .streamlit/secrets.toml (로컬) 또는 Streamlit Cloud의 'Settings > Secrets' (배포 환경)에
   아래 형식으로 값을 채워 넣기:

    [auth]
    redirect_uri = "https://<너의-앱-주소>.streamlit.app/oauth2callback"
    cookie_secret = "아무 문자열이나 길고 무작위하게"

    [auth.google]
    client_id = "GOOGLE_CLIENT_ID"
    client_secret = "GOOGLE_CLIENT_SECRET"
    server_metadata_url = "https://accounts.google.com/.well-known/openid-configuration"

3. requirements.txt에 Authlib 추가 (이미 반영됨)

로컬 개발 중에는 redirect_uri를 http://localhost:8501/oauth2callback 로 바꾼
별도의 secrets.toml을 쓰는 게 편함 (배포용과 로컬용 OAuth 클라이언트를 따로 등록해도 됨).
"""
import streamlit as st


def _auth_configured() -> bool:
    """secrets.toml에 [auth] 섹션이 채워져 있는지 확인. 없으면 로그인 기능 자체가 꺼짐."""
    try:
        return "auth" in st.secrets and "google" in st.secrets.get("auth", {})
    except Exception:
        return False


def is_logged_in() -> bool:
    return hasattr(st, "user") and getattr(st.user, "is_logged_in", False)


def ensure_user() -> str | None:
    """로그인된 사용자의 고유 식별자(이메일)를 반환. 비로그인 시 None."""
    if is_logged_in():
        return st.user.email
    return None


def require_login():
    """
    로그인이 안 되어 있으면 로그인 화면만 그리고 나머지 페이지 실행을 중단(st.stop).
    로그인이 되어 있으면 사이드바에 사용자 정보 + 로그아웃 버튼을 그리고 그대로 통과.
    """
    if not _auth_configured():
        st.error(
            "⚠️ 로그인 기능이 아직 설정되지 않았어요. "
            "secrets.toml(또는 Streamlit Cloud의 Secrets 설정)에 [auth] / [auth.google] 값을 "
            "채워 넣어야 로그인을 쓸 수 있어요."
        )
        st.stop()

    if not is_logged_in():
        st.title("🔐 ZION 로그인")
        st.write("Google 계정으로 로그인하면 내 포트폴리오·관심종목·검색 기록이 저장돼요.")
        st.button("🔑 Google로 로그인", type="primary", on_click=st.login, args=("google",))
        st.stop()

    with st.sidebar:
        st.caption("👤 로그인 계정")
        name = getattr(st.user, "name", None) or st.user.email
        st.markdown(f"**{name}**")
        st.caption(st.user.email)
        if st.button("🚪 로그아웃", use_container_width=True):
            st.logout()
