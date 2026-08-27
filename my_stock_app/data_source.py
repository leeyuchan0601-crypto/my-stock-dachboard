"""
데이터 신뢰성 강화용 헬퍼.

1) fetch_price_with_fallback(): yfinance로 먼저 시도하고, 실패하면
   st.secrets["ALPHA_VANTAGE_KEY"]가 설정된 경우에만 Alpha Vantage로 재시도함.
   키가 없으면 조용히 yfinance 결과(또는 None)만 반환 — 즉, 키 없이도 기존처럼 동작함.

   Alpha Vantage 무료 키는 https://www.alphavantage.co/support/#api-key 에서 발급받고,
   .streamlit/secrets.toml에 아래처럼 추가하면 자동으로 활성화됨:
       ALPHA_VANTAGE_KEY = "여기에_발급받은_키"

2) smart_cache_ttl(): 한국/미국 정규장 시간대를 대략적으로 감안해서, 장중엔 캐시를 짧게(변동 반영 빠르게),
   장 마감/주말엔 길게 잡아 불필요한 API 호출을 줄임. 공휴일까지 정교하게 따지진 않는
   '대략적인' 휴리스틱이라 완벽한 장 캘린더가 필요하면 pandas_market_calendars 도입을 권장.
"""
import datetime
import time
import functools
import requests
import streamlit as st
import yfinance as yf


def with_retry(retries: int = 3, base_delay: float = 1.5):
    """
    일시적인 오류(야후 rate limit, yfinance 내부 캐시 DB 잠금 등)에 대비한 재시도 데코레이터.
    실패할 때마다 base_delay * (2 ** 시도횟수) 만큼 대기 후 다시 시도함 (지수 백오프).
    마지막 시도까지 실패하면 원래 예외를 그대로 올림.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exc = None
            for attempt in range(retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    if attempt < retries - 1:
                        time.sleep(base_delay * (2 ** attempt))
            raise last_exc
        return wrapper
    return decorator


@with_retry(retries=3, base_delay=1.5)
def download_with_retry(tickers, **kwargs):
    """yf.download를 재시도 로직으로 감싼 버전. 히트맵/알림처럼 여러 종목을 한 번에 받을 때 사용."""
    return yf.download(tickers, **kwargs)


def _is_krx_hours(now_kst: datetime.datetime) -> bool:
    if now_kst.weekday() >= 5:  # 토(5)/일(6)
        return False
    t = now_kst.time()
    return datetime.time(9, 0) <= t <= datetime.time(15, 30)


def _is_us_hours(now_kst: datetime.datetime) -> bool:
    # 미국 정규장(서머타임 미반영 단순화): 한국시간 기준 대략 22:30~05:00
    if now_kst.weekday() >= 5:
        return False
    t = now_kst.time()
    return t >= datetime.time(22, 30) or t <= datetime.time(5, 0)


def smart_cache_ttl(default_open: int = 60, default_closed: int = 1800) -> int:
    """장중이면 짧은 TTL(초), 장 마감/주말이면 긴 TTL을 반환."""
    now_kst = datetime.datetime.utcnow() + datetime.timedelta(hours=9)
    if _is_krx_hours(now_kst) or _is_us_hours(now_kst):
        return default_open
    return default_closed


def _fetch_alpha_vantage_quote(ticker: str, api_key: str):
    try:
        url = "https://www.alphavantage.co/query"
        params = {"function": "GLOBAL_QUOTE", "symbol": ticker, "apikey": api_key}
        resp = requests.get(url, params=params, timeout=5)
        data = resp.json().get("Global Quote", {})
        price = data.get("05. price")
        change_pct = data.get("10. change percent", "").replace("%", "")
        if price and change_pct:
            return float(price), float(change_pct)
    except Exception:
        pass
    return None, None


def fetch_price_with_fallback(ticker: str):
    """(현재가, 등락률%) 튜플 반환. 실패하면 (None, None)."""
    try:
        hist = yf.Ticker(ticker).history(period="5d")
        if not hist.empty and len(hist) >= 2:
            curr = float(hist["Close"].iloc[-1])
            prev = float(hist["Close"].iloc[-2])
            return curr, round((curr - prev) / prev * 100, 2)
    except Exception:
        pass

    api_key = None
    try:
        api_key = st.secrets.get("ALPHA_VANTAGE_KEY")
    except Exception:
        # secrets.toml이 없는 환경에서는 st.secrets 접근 자체가 예외를 던질 수 있음 → 조용히 무시
        api_key = None
    if api_key:
        return _fetch_alpha_vantage_quote(ticker, api_key)

    return None, None
