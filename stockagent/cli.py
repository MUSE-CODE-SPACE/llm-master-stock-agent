"""Multi-turn CLI. / 멀티턴 대화 CLI."""
from stockagent.agent import ask
from stockagent.memory import add_watchlist, load_watchlist


def _show(kind, payload):
    if kind == "tool_call":
        print(f"  🔧 {payload['name']}({payload['args']})")
    elif kind == "tool_result":
        print(f"  📥 {payload['result']}")


def main(user_id: str = "demo") -> None:
    print(f"Stock agent — watchlist: {load_watchlist(user_id) or '(empty)'}")
    while True:
        try:
            q = input("\nQ> ").strip()
        except (EOFError, KeyboardInterrupt):
            print("\nbye"); break
        if not q:
            continue
        print(ask(q, on_event=_show))


if __name__ == "__main__":
    main()
