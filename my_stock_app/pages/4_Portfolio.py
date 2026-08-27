import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from PIL import Image
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import theme
import db
from auth import require_login, ensure_user
from data_source import fetch_price_with_fallback

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Portfolio", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Portfolio", page_icon="💼", layout="wide")

theme.inject_base_css()
require_login()
USER_ID = ensure_user()

theme.page_header("PORTFOLIO TRACKER", "내가 보유한 종목의 실시간 평가손익을 확인합니다.")
st.caption(f"👤 로그인 계정: **{USER_ID}** (계정별로 데이터가 구분돼요)")
st.write("---")

with st.container(border=True):
    st.subheader("➕ 보유 종목 추가")
    c1, c2, c3, c4 = st.columns([2, 1, 1, 1])
    with c1:
        add_ticker = st.text_input("종목 코드", placeholder="예: AAPL, 005930.KS").upper().strip()
    with c2:
        add_shares = st.number_input("수량", min_value=0.0, value=1.0, step=1.0)
    with c3:
        add_price = st.number_input("평균 매수 단가", min_value=0.0, value=0.0, step=0.01)
    with c4:
        st.write("")
        st.write("")
        if st.button("추가", type="primary", use_container_width=True):
            if add_ticker and add_shares > 0 and add_price > 0:
                db.add_holding(USER_ID, add_ticker, add_shares, add_price)
                st.success(f"{add_ticker} {add_shares}주 추가됐습니다.")
                st.rerun()
            else:
                st.warning("종목 코드, 수량, 매수 단가를 모두 입력해주세요.")

st.write("")
holdings = db.get_portfolio(USER_ID)

if not holdings:
    st.info("아직 보유 종목이 없습니다. 위에서 추가해보세요.")
else:
    rows = []
    failed_tickers = []
    with st.spinner("📡 실시간 시세 조회 중..."):
        for rowid, ticker, shares, avg_price in holdings:
            curr_price, change_pct = fetch_price_with_fallback(ticker)
            price_failed = curr_price is None
            if price_failed:
                failed_tickers.append(ticker)
            cost = shares * avg_price
            # 가격 조회에 실패하면 매수 단가로 대체하지 않고, 계산 자체를 하지 않음(N/A로 표시)
            value = (shares * curr_price) if not price_failed else float("nan")
            pnl = (value - cost) if not price_failed else float("nan")
            pnl_pct = (pnl / cost * 100) if (not price_failed and cost) else float("nan")
            rows.append({
                "rowid": rowid, "종목": ticker, "수량": shares, "평균단가": avg_price,
                "현재가": curr_price if not price_failed else float("nan"),
                "당일등락률": change_pct if not price_failed else float("nan"),
                "평가금액": value, "평가손익": pnl, "손익률(%)": pnl_pct,
                "가격조회실패": price_failed,
            })

    if failed_tickers:
        st.warning(f"⚠️ 다음 종목은 실시간 시세를 가져오지 못해 손익 계산에서 제외했습니다: {', '.join(failed_tickers)}")

    df = pd.DataFrame(rows)
    ok_df = df[~df["가격조회실패"]]

    total_cost = (ok_df["수량"] * ok_df["평균단가"]).sum()
    total_value = ok_df["평가금액"].sum()
    total_pnl = total_value - total_cost
    total_pnl_pct = (total_pnl / total_cost * 100) if total_cost else 0.0

    m1, m2, m3 = st.columns(3)
    m1.metric("총 평가금액", f"{total_value:,.2f}" + (" *" if failed_tickers else ""))
    m2.metric("총 평가손익", f"{total_pnl:,.2f}", f"{total_pnl_pct:+.2f}%")
    m3.metric("보유 종목 수", f"{len(df)} 개")
    if failed_tickers:
        st.caption("* 시세 조회 실패 종목은 총액 계산에서 제외됨")

    st.write("---")
    col_table, col_pie = st.columns([3, 2])

    with col_table:
        st.subheader("📋 보유 종목 상세")
        display_df = df.drop(columns=["rowid", "가격조회실패"]).copy()
        for col in ["평균단가", "현재가", "평가금액", "평가손익"]:
            display_df[col] = df[col].map(lambda x: f"{x:,.2f}" if pd.notna(x) else "N/A")
        display_df["당일등락률"] = df["당일등락률"].map(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A")
        display_df["손익률(%)"] = df["손익률(%)"].map(lambda x: f"{x:+.2f}%" if pd.notna(x) else "N/A")
        st.dataframe(display_df, use_container_width=True, hide_index=True)

        del_col1, del_col2 = st.columns([3, 1])
        with del_col1:
            target_to_delete = st.selectbox("삭제할 보유 종목 선택", options=df["종목"].tolist(),
                                             key="del_target", label_visibility="collapsed")
        with del_col2:
            if st.button("🗑️ 삭제", use_container_width=True):
                rowid_to_delete = df[df["종목"] == target_to_delete]["rowid"].iloc[0]
                db.delete_holding(int(rowid_to_delete))
                st.rerun()

    with col_pie:
        st.subheader("🥧 자산 비중")
        fig = go.Figure(data=[go.Pie(
            labels=ok_df["종목"], values=ok_df["평가금액"], hole=0.45,
            marker=dict(colors=["#2563eb", "#16a34a", "#f59e0b", "#dc2626", "#7c3aed", "#0891b2", "#db2777"]),
        )])
        fig.update_layout(template="plotly_white", paper_bgcolor="#ffffff", height=350,
                           margin=dict(l=10, r=10, t=10, b=10), showlegend=True)
        st.plotly_chart(fig, use_container_width=True)

st.write("---")
st.caption("⚠️ 시세는 참고용이며, 실제 매매 시 증권사 앱의 시세를 기준으로 확인하세요.")
