"""Per-user watchlist memory (SQLite). / 사용자별 관심종목 메모리(SQLite)."""
import sqlite3

from stockagent.settings import settings


def _conn():
    c = sqlite3.connect(settings.db_path)
    c.execute(
        "CREATE TABLE IF NOT EXISTS watchlist "
        "(user_id TEXT, ticker TEXT, PRIMARY KEY (user_id, ticker))"
    )
    return c


def add_watchlist(user_id: str, ticker: str) -> None:
    with _conn() as c:
        c.execute("INSERT OR IGNORE INTO watchlist VALUES (?, ?)", (user_id, ticker.upper()))


def load_watchlist(user_id: str) -> list[str]:
    with _conn() as c:
        rows = c.execute("SELECT ticker FROM watchlist WHERE user_id = ?", (user_id,)).fetchall()
    return [r[0] for r in rows]
