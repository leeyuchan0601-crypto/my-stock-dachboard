"""
ZION 앱 전체가 공유하는 테마/스타일 모듈.
pages/*.py 에서는 프로젝트 루트에 이 파일이 있으면 `import theme` 로 바로 불러 쓸 수 있음
(Streamlit이 메인 스크립트 폴더를 sys.path에 자동으로 추가해주기 때문).
"""
import streamlit as st

PRIMARY = "#2563eb"
PRIMARY_DARK = "#1d4ed8"
BG = "#f8fafc"
CARD_BG = "#ffffff"
BORDER = "#e2e8f0"
TEXT_DARK = "#0f172a"
TEXT_MUTED = "#64748b"
GREEN = "#16a34a"
RED = "#dc2626"


def inject_base_css():
    """모든 페이지 상단에서 한 번씩 호출하면 공통 톤(배경/카드/버튼/탭/모바일 대응)이 적용됨."""
    st.markdown(f"""
        <style>
        .stApp {{ background-color: {BG}; }}
        h1, h2, h3 {{ color: {TEXT_DARK} !important; font-weight: 800 !important; letter-spacing: -0.3px; }}
        p, span, label {{ color: {TEXT_MUTED}; }}

        div[data-testid="metric-container"] {{
            background-color: {CARD_BG};
            border: 1px solid {BORDER};
            padding: 16px;
            border-radius: 12px;
            box-shadow: 0 1px 3px rgba(15, 23, 42, 0.04);
        }}
        div[data-testid="metric-container"] label {{ color: {TEXT_MUTED} !important; font-weight: 600; }}
        div[data-testid="metric-container"] div {{ color: {TEXT_DARK} !important; }}

        .stTabs [data-baseweb="tab-list"] {{ gap: 20px; }}
        .stTabs [data-baseweb="tab"] {{ height: 46px; font-weight: 700; }}

        .stButton>button {{
            border-radius: 10px;
            font-weight: 700;
        }}

        div[data-testid="stVerticalBlockBorderWrapper"] {{
            background-color: {CARD_BG};
            border-radius: 14px;
            border: 1px solid {BORDER};
        }}

        /* 모바일 대응: 화면이 좁아지면 여백/폰트 축소 */
        @media (max-width: 640px) {{
            div[data-testid="metric-container"] {{ padding: 10px; }}
            h1 {{ font-size: 24px !important; }}
            h3 {{ font-size: 18px !important; }}
        }}

        /* 스켈레톤 로딩 박스: 무거운 데이터를 불러오는 동안 빈 화면 대신 표시 */
        @keyframes zion-shimmer {{
            0% {{ background-position: -400px 0; }}
            100% {{ background-position: 400px 0; }}
        }}
        .zion-skeleton {{
            border-radius: 12px;
            background: linear-gradient(90deg, #e2e8f0 25%, #f1f5f9 37%, #e2e8f0 63%);
            background-size: 800px 100%;
            animation: zion-shimmer 1.4s ease-in-out infinite;
        }}
        </style>
        """, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = None, icon: str = ""):
    st.title(f"{icon} {title}".strip())
    if subtitle:
        st.caption(subtitle)


def skeleton(height: int = 400, key: str = "default"):
    """무거운 데이터 로딩 중 보여줄 스켈레톤(반짝이는 회색 박스) placeholder.
    사용법: ph = theme.skeleton(850); ... 데이터 준비되면 ph.empty() 로 지우고 실제 내용을 그림."""
    ph = st.empty()
    ph.markdown(
        f'<div class="zion-skeleton" style="height:{height}px; width:100%;"></div>',
        unsafe_allow_html=True,
    )
    return ph
