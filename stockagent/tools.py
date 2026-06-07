"""Tools the agent can call. A plain function + @tool -> an LLM tool schema.
에이전트가 부를 수 있는 도구. 보통 함수 + @tool -> LLM 도구 스키마."""
import inspect
from typing import Callable

import feedparser
import yfinance as yf

_PYTYPE = {int: "integer", float: "number", str: "string", bool: "boolean"}


def tool(fn: Callable) -> Callable:
    """Build an OpenAI-style function schema from the signature. / 시그니처에서 스키마 생성."""
    sig = inspect.signature(fn)
    props, required = {}, []
    for name, p in sig.parameters.items():
        props[name] = {"type": _PYTYPE.get(p.annotation, "string")}
        if p.default is inspect.Parameter.empty:
            required.append(name)
    fn.schema = {
        "type": "function",
        "function": {
            "name": fn.__name__,
            "description": (fn.__doc__ or "").strip().split("\n")[0],
            "parameters": {"type": "object", "properties": props, "required": required},
        },
    }
    return fn


@tool
def get_stock_info(ticker: str) -> dict:
    """Get current price and basic info for a stock ticker. / 종목 현재가·기본정보."""
    try:
        fi = yf.Ticker(ticker).fast_info
        price = fi.get("lastPrice") or fi.get("last_price")
        return {
            "ticker": ticker.upper(),
            "price": round(price, 2) if price else None,
            "currency": fi.get("currency", "USD"),
            "day_high": fi.get("dayHigh") or fi.get("day_high"),
            "day_low": fi.get("dayLow") or fi.get("day_low"),
        }
    except Exception as e:  # graceful — yfinance can rate-limit / yfinance는 제한될 수 있음
        return {"error": f"could not fetch {ticker}: {e}", "ticker": ticker}


@tool
def get_stock_history(ticker: str, period: str = "1mo") -> dict:
    """Get recent price history summary (period like 1mo, 3mo, 1y). / 최근 가격 이력 요약."""
    try:
        hist = yf.Ticker(ticker).history(period=period)
        if hist.empty:
            return {"error": "no data", "ticker": ticker}
        close = hist["Close"]
        return {
            "ticker": ticker.upper(),
            "period": period,
            "start": round(float(close.iloc[0]), 2),
            "end": round(float(close.iloc[-1]), 2),
            "change_pct": round((float(close.iloc[-1]) / float(close.iloc[0]) - 1) * 100, 2),
            "high": round(float(close.max()), 2),
            "low": round(float(close.min()), 2),
        }
    except Exception as e:
        return {"error": str(e), "ticker": ticker}


@tool
def search_news(query: str, max_items: int = 5) -> list:
    """Search recent news headlines for a topic via Google News RSS. / 뉴스 헤드라인 검색."""
    try:
        url = f"https://news.google.com/rss/search?q={query}&hl=en-US"
        feed = feedparser.parse(url)
        return [{"title": e.title, "link": e.link} for e in feed.entries[:max_items]]
    except Exception as e:
        return [{"error": str(e)}]


TOOLS = [get_stock_info, get_stock_history, search_news]
REGISTRY = {t.__name__: t for t in TOOLS}
SCHEMAS = [t.schema for t in TOOLS]
