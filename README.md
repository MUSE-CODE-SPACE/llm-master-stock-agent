<!-- 🌏 English + 한국어 (English first) -->
# Stock Analysis Agent / 주식 분석 에이전트

> A working tool-calling agent that fetches **real market data** (yfinance) and news, reasons over multiple steps, and answers — with a forced disclaimer. Runs on **OpenAI / Anthropic / a local SLM (Ollama)**.
> 실제 시세(yfinance)와 뉴스를 도구로 가져와 여러 단계로 분석해 답하는 에이전트. 투자 면책 강제. OpenAI/Anthropic/로컬 SLM 모두 지원.

> 📱 Hands-on code for the **[LLM Master](https://apps.apple.com/app/id6769785318)** course — "실전 프로젝트 2: 주식 분석 Agent".

```
question ──▶ LLM ──▶ tool_calls? ──yes──▶ run tool (yfinance/news) ──▶ result ─┐
               ▲                                                                │
               └────────────────────────────────────────────────────────────────┘
                        no ──▶ final answer (+ disclaimer)
```

## Run / 실행
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env        # add your key / 키 입력
python -m stockagent.cli
# Q> 애플(AAPL) 지금 주가랑 최근 한 달 추세 알려줘
```
Example (real run) / 실제 실행 예:
```
🔧 get_stock_info({'ticker':'AAPL'})      📥 price 307.34 USD
🔧 get_stock_history({'ticker':'AAPL','period':'1mo'})  📥 +7.0%
A: 현재 307.34 달러 ... 한 달 +7% 상승 ...
   This is not investment advice. / 투자 조언이 아닙니다.
```

| File | What / 하는 일 |
|---|---|
| `stockagent/tools.py` | `@tool` → schema · get_stock_info / history / search_news |
| `stockagent/agent.py` | tool-calling loop (max_steps), multi-vendor |
| `stockagent/memory.py` | per-user watchlist (SQLite) |
| `stockagent/cli.py` | multi-turn chat |

`PROVIDER=openai|anthropic|ollama` in `.env` — no code change. **Not investment advice.** / 투자 조언 아님.

## License — MIT (educational / 교육용)
