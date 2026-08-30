import streamlit as st
import pandas as pd
import yfinance as yf
import requests
from PIL import Image
import os
import sys
from concurrent.futures import ThreadPoolExecutor, as_completed

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import theme
import db
from auth import require_login, ensure_user
from data_source import download_with_retry

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
icon_path = os.path.join(parent_dir, "ark_base.png")

if os.path.exists(icon_path):
    img = Image.open(icon_path)
    st.set_page_config(page_title="ZION | Alerts", page_icon=img, layout="wide")
else:
    st.set_page_config(page_title="ZION | Alerts", page_icon="Z", layout="wide")

theme.inject_base_css()
require_login()
USER_ID = ensure_user()

theme.page_header("SIGNAL ALERTS", "관심 종목의 매수/매도 시그널을 확인하고 Slack으로 알림을 보냅니다.")
st.write("---")

# --- 1. Slack 연동 설정 ---
with st.container(border=True):
    st.subheader("Slack 연동 설정")
    st.caption(
        "Slack에서 '앱 > Incoming Webhooks'로 발급받은 Webhook URL을 붙여넣으세요. "
        "이 값은 브라우저 세션에만 저장되고 서버에 영구 저장되지 않아요."
    )
    webhook_url = st.text_input(
        "Slack Webhook URL",
        value=st.session_state.get("slack_webhook", ""),
        type="password",
        placeholder="https://hooks.slack.com/services/...",
    )
    st.session_state.slack_webhook = webhook_url
    if st.button("테스트 알림 보내기", disabled=not webhook_url):
        try:
            resp = requests.post(webhook_url, json={"text": "ZION 알림 테스트입니다. 연동이 정상 작동합니다!"}, timeout=5)
            if resp.status_code == 200:
                st.success("테스트 메시지를 보냈어요. Slack 채널을 확인해보세요.")
            else:
                st.error(f"전송 실패 (status {resp.status_code}). Webhook URL을 다시 확인해주세요.")
        except Exception as e:
            st.error(f"전송 중 오류: {e}")

st.write("")

# --- 2. 관심 종목 관리 ---
with st.container(border=True):
    st.subheader("관심 종목 관리")
    c1, c2 = st.columns([4, 1])
    with c1:
        new_watch = st.text_input("종목 코드 추가", placeholder="예: AAPL, 005930.KS",
                                   label_visibility="collapsed").upper().strip()
    with c2:
        if st.button("추가", use_container_width=True):
            if new_watch:
                db.add_watch(USER_ID, new_watch)
                st.rerun()

    watchlist = db.get_watchlist(USER_ID)
    if not watchlist:
        st.info("관심 종목이 없습니다. 히트맵에서 종목을 클릭하면 자동으로 추가되기도 해요.")
    else:
        chip_cols = st.columns(min(len(watchlist), 6) or 1)
        for i, tk in enumerate(watchlist):
            with chip_cols[i % len(chip_cols)]:
                if st.button(f"{tk} 제거", key=f"unwatch_{tk}", use_container_width=True):
                    db.delete_watch(USER_ID, tk)
                    st.rerun()

st.write("")


# --- 3. 시그널 계산 ---
def compute_signal(ticker):
    try:
        data = download_with_retry(ticker, period="6mo", progress=False, threads=True)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.get_level_values(0)
        if data.empty or len(data) < 25:
            return None

        data['MA5'] = data['Close'].rolling(5).mean()
        data['MA20'] = data['Close'].rolling(20).mean()
        delta = data['Close'].diff()
        up, down = delta.clip(lower=0), -delta.clip(upper=0)
        rs = up.rolling(14).mean() / down.rolling(14).mean()
        data['RSI'] = 100 - (100 / (1 + rs))

        last = data.iloc[-1]
        prev = data.iloc[-2]
        buy = (prev['MA5'] < prev['MA20']) and (last['MA5'] > last['MA20']) and (last['RSI'] < 70)
        sell = (prev['MA5'] > prev['MA20']) and (last['MA5'] < last['MA20']) and (last['RSI'] > 30)

        signal = "BUY" if buy else "SELL" if sell else "HOLD"
        return {
            "ticker": ticker, "price": float(last['Close']),
            "rsi": float(last['RSI']) if pd.notna(last['RSI']) else None,
            "signal": signal,
        }
    except Exception:
        return None


# --- 4. 시그널 확인 + 알림 발송 ---
st.subheader("지금 신호 확인")
if not watchlist:
    st.caption("관심 종목을 먼저 등록해주세요.")
else:
    if st.button("전체 신호 확인 & Slack 알림 보내기", type="primary", use_container_width=True):
        results = []
        progress_box = st.status("관심 종목 신호 계산 중...", expanded=True)
        with ThreadPoolExecutor(max_workers=min(8, len(watchlist))) as executor:
            future_to_tk = {executor.submit(compute_signal, tk): tk for tk in watchlist}
            done_count = 0
            for future in as_completed(future_to_tk):
                tk = future_to_tk[future]
                done_count += 1
                r = future.result()
                if r:
                    results.append(r)
                    progress_box.write(f"({done_count}/{len(watchlist)}) {tk} → {r['signal']}")
                else:
                    progress_box.write(f"({done_count}/{len(watchlist)}) {tk} → 조회 실패")
        progress_box.update(label="신호 계산 완료", state="complete", expanded=False)

        if results:
            df = pd.DataFrame(results)
            st.dataframe(df.rename(columns={
                "ticker": "종목", "price": "현재가", "rsi": "RSI", "signal": "시그널"
            }), use_container_width=True, hide_index=True)

            actionable = [r for r in results if r["signal"] in ("BUY", "SELL")]
            if actionable and webhook_url:
                lines = ["*ZION 시그널 알림*"]
                for r in actionable:
                    lines.append(f"*{r['ticker']}* — {r['signal']} 시그널 (현재가 {r['price']:.2f}, RSI {r['rsi']:.1f})")
                try:
                    resp = requests.post(webhook_url, json={"text": "\n".join(lines)}, timeout=5)
                    if resp.status_code == 200:
                        st.success(f"{len(actionable)}건의 시그널을 Slack으로 전송했습니다.")
                    else:
                        st.error("Slack 전송에 실패했습니다.")
                except Exception as e:
                    st.error(f"전송 중 오류: {e}")
            elif actionable and not webhook_url:
                st.warning("BUY/SELL 시그널이 있지만, Slack Webhook URL이 설정되지 않아 알림을 보내지 않았습니다.")
            else:
                st.info("현재 발생한 BUY/SELL 시그널이 없습니다 (전부 HOLD).")
        else:
            st.error("신호를 계산할 데이터를 가져오지 못했습니다.")

st.write("---")
st.markdown("""
** 자동으로 주기적 알림을 받으려면?**

Streamlit 앱은 브라우저 탭이 열려 있을 때만 실행되기 때문에, "매일 아침 9시에 자동으로 확인"처럼
정해진 시간에 스스로 실행되진 않아요. 완전 자동화하려면 아래처럼 외부 스케줄러가 필요해요:

1. 이 페이지의 `compute_signal()` 로직을 별도의 스크립트(`check_signals.py`)로 분리
2. GitHub Actions의 `schedule` 트리거(cron)로 하루 1~2회 그 스크립트를 실행
3. 스크립트 안에서 Slack Webhook으로 바로 전송

원하면 이 자동화용 스크립트와 GitHub Actions 워크플로 파일(`.github/workflows/signal_check.yml`)도 만들어줄 수 있어요.
""")
