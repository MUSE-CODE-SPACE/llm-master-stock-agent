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


def to_anthropic_tools(schemas: list) -> list:
    """Convert OpenAI function schemas to Anthropic tool format.
    OpenAI: {"type": "function", "function": {name, description, parameters}}
    Anthropic: {name, description, input_schema}
    OpenAI 도구 스키마를 Anthropic 형식으로 변환."""
    return [
        {
            "name": s["function"]["name"],
            "description": s["function"]["description"],
            "input_schema": s["function"]["parameters"],
        }
        for s in schemas
    ]


def _ask_anthropic(client, question: str, on_event=None) -> str:
    """Tool-calling loop, Anthropic Messages API flavor. / Anthropic 도구 호출 루프."""
    tools = to_anthropic_tools(SCHEMAS)
    messages = [{"role": "user", "content": question}]
    for _ in range(settings.max_steps):
        resp = client.messages.create(
            model=settings.llm_model, max_tokens=1024, system=SYSTEM,
            messages=messages, tools=tools,
        )
        if resp.stop_reason != "tool_use":
            return "".join(b.text for b in resp.content if b.type == "text")
        # Echo the assistant turn back, then answer every tool_use block
        # with a matching tool_result. / 어시스턴트 턴을 그대로 되돌려주고 결과 첨부.
        messages.append({"role": "assistant", "content": resp.content})
        results = []
        for block in resp.content:
            if block.type != "tool_use":
                continue
            name, args = block.name, dict(block.input or {})
            if on_event:
                on_event("tool_call", {"name": name, "args": args})
            result = REGISTRY[name](**args) if name in REGISTRY else {"error": "unknown tool"}
            if on_event:
                on_event("tool_result", {"name": name, "result": result})
            results.append({"type": "tool_result", "tool_use_id": block.id,
                            "content": json.dumps(result, ensure_ascii=False)})
        messages.append({"role": "user", "content": results})
    return "Reached max steps without a final answer. / 최대 단계 도달."


def ask(question: str, on_event=None) -> str:
    """Run the tool-calling loop and return the final answer. / 루프를 돌려 최종 답 반환."""
    kind, client = _llm()
    if kind == "anthropic":
        return _ask_anthropic(client, question, on_event)
    # OpenAI/Ollama path (both speak the OpenAI Chat API) / openai·ollama 경로
    messages = [{"role": "system", "content": SYSTEM}, {"role": "user", "content": question}]
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
