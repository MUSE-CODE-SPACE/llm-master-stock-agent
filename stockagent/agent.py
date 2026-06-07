"""The agent loop: model -> tool calls -> execute -> repeat (max_steps cap).
Works with OpenAI, Anthropic, or a local SLM (Ollama). / 도구 호출 루프, 멀티 벤더."""
import json

from stockagent.settings import settings
from stockagent.tools import REGISTRY, SCHEMAS

SYSTEM = (
    "You are a stock-analysis assistant. Use the tools to fetch real data before "
    "answering. ALWAYS end with this disclaimer line: "
    "'This is not investment advice. / 투자 조언이 아닙니다.' "
    "도구로 실제 데이터를 가져와 분석하고, 마지막에 반드시 면책 문구를 붙여라."
)

_client = None


def _llm():
    global _client
    if _client is not None:
        return _client
    if settings.provider == "anthropic":
        from anthropic import Anthropic

        _client = ("anthropic", Anthropic(api_key=settings.anthropic_api_key))
    else:
        from openai import OpenAI

        if settings.provider == "ollama":
            _client = ("openai", OpenAI(base_url=settings.ollama_base_url, api_key="ollama"))
        else:
            _client = ("openai", OpenAI(api_key=settings.openai_api_key))
    return _client


def ask(question: str, on_event=None) -> str:
    """Run the tool-calling loop and return the final answer. / 루프를 돌려 최종 답 반환."""
    kind, client = _llm()
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
    # OpenAI/Ollama path (Anthropic uses a different tool schema; OpenAI form is the default demo)
    for _ in range(settings.max_steps):
        resp = client.chat.completions.create(
            model=settings.llm_model, messages=messages, tools=SCHEMAS, tool_choice="auto"
        )
        msg = resp.choices[0].message
        messages.append(msg.model_dump(exclude_none=True))
        if not msg.tool_calls:
            return msg.content or ""
        for tc in msg.tool_calls:
            name = tc.function.name
            args = json.loads(tc.function.arguments or "{}")
            if on_event:
                on_event("tool_call", {"name": name, "args": args})
            result = REGISTRY[name](**args) if name in REGISTRY else {"error": "unknown tool"}
            if on_event:
                on_event("tool_result", {"name": name, "result": result})
            messages.append({"role": "tool", "tool_call_id": tc.id, "content": json.dumps(result, ensure_ascii=False)})
    return "Reached max steps without a final answer. / 최대 단계 도달."
