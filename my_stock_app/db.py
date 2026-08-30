"""
search_history.json 을 대체하는 SQLite 저장소.
Streamlit Cloud처럼 재배포 시 파일시스템이 리셋되는 환경에서도, 앱이 살아있는 동안은
JSON 파일보다 다루기 쉽고 사용자별(user_id) 데이터 분리가 자연스러움.

주의: Streamlit Cloud 무료 티어는 컨테이너가 재시작되면 로컬 디스크(SQLite 파일 포함)가
초기화될 수 있음. 데이터를 영구 보존하려면 Supabase, Turso 같은 외부 DB로 옮기는 게 안전함.
지금은 '로컬 파일 기반'에서 한 단계 나아간 버전으로 이해하면 됨.
"""
import sqlite3
import os
import datetime

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "zion.db")


def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False, timeout=30)
    # WAL(Write-Ahead Logging) 모드: 읽기와 쓰기가 서로를 덜 막도록 해서
    # 여러 사용자가 동시에 접속해도 "database is locked" 에러가 훨씬 덜 남.
    conn.execute("PRAGMA journal_mode=WAL;")
    # 잠금이 걸려도 즉시 에러 내지 않고 최대 30초까지 기다렸다가 재시도하게 함.
    conn.execute("PRAGMA busy_timeout=30000;")
    conn.execute("""CREATE TABLE IF NOT EXISTS search_history (
        user_id TEXT, ticker TEXT, searched_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS portfolio (
        user_id TEXT, ticker TEXT, shares REAL, avg_price REAL, added_at TEXT
    )""")
    conn.execute("""CREATE TABLE IF NOT EXISTS watchlist (
        user_id TEXT, ticker TEXT, added_at TEXT
    )""")
    conn.commit()
    return conn


# ---------------- 검색 기록 ----------------
def add_history(user_id: str, ticker: str):
    conn = get_conn()
    conn.execute("DELETE FROM search_history WHERE user_id=? AND ticker=?", (user_id, ticker))
    conn.execute(
        "INSERT INTO search_history VALUES (?, ?, ?)",
        (user_id, ticker, datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_history(user_id: str, limit: int = 10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT ticker FROM search_history WHERE user_id=? ORDER BY searched_at DESC LIMIT ?",
        (user_id, limit),
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def delete_history(user_id: str, ticker: str):
    conn = get_conn()
    conn.execute("DELETE FROM search_history WHERE user_id=? AND ticker=?", (user_id, ticker))
    conn.commit()
    conn.close()


# ---------------- 포트폴리오 ----------------
def add_holding(user_id: str, ticker: str, shares: float, avg_price: float):
    conn = get_conn()
    conn.execute(
        "INSERT INTO portfolio VALUES (?, ?, ?, ?, ?)",
        (user_id, ticker, shares, avg_price, datetime.datetime.now().isoformat()),
    )
    conn.commit()
    conn.close()


def get_portfolio(user_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT rowid, ticker, shares, avg_price FROM portfolio WHERE user_id=? ORDER BY rowid",
        (user_id,),
    ).fetchall()
    conn.close()
    return rows


def delete_holding(rowid: int):
    conn = get_conn()
    conn.execute("DELETE FROM portfolio WHERE rowid=?", (rowid,))
    conn.commit()
    conn.close()


# ---------------- 관심종목(알림 대상) ----------------
def add_watch(user_id: str, ticker: str):
    conn = get_conn()
    existing = conn.execute(
        "SELECT 1 FROM watchlist WHERE user_id=? AND ticker=?", (user_id, ticker)
    ).fetchone()
    if not existing:
        conn.execute(
            "INSERT INTO watchlist VALUES (?, ?, ?)",
            (user_id, ticker, datetime.datetime.now().isoformat()),
        )
        conn.commit()
    conn.close()


def get_watchlist(user_id: str):
    conn = get_conn()
    rows = conn.execute(
        "SELECT ticker FROM watchlist WHERE user_id=? ORDER BY added_at DESC", (user_id,)
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]


def delete_watch(user_id: str, ticker: str):
    conn = get_conn()
    conn.execute("DELETE FROM watchlist WHERE user_id=? AND ticker=?", (user_id, ticker))
    conn.commit()
    conn.close()
