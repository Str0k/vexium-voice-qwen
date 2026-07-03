import json, os
from openai import OpenAI
from agent_config import handle_function

def build_client() -> OpenAI:
    return OpenAI(
        api_key=os.environ["DASHSCOPE_API_KEY"],
        base_url=os.getenv("QWEN_BASE_URL", "https://dashscope-intl.aliyuncs.com/compatible-mode/v1"),
    )

def validate_args(raw: str) -> dict:
    try:
        v = json.loads(raw or "{}")
        return v if isinstance(v, dict) else {}
    except (json.JSONDecodeError, TypeError):
        return {}

def run_turn(messages, tools, vertical, *, client=None, max_steps: int = 5,
             extra_args: dict | None = None) -> dict:
    """One conversational turn: let Qwen call tools until it produces a reply.
    `extra_args` (e.g. {"tenant", "call_id"}) is merged into every tool call so
    handlers persist to the right tenant partition, same as the voice path."""
    client = client or build_client()
    model = os.getenv("QWEN_BRAIN_MODEL", "qwen3-max")
    convo = list(messages)
    tool_events: list[dict] = []
    for _ in range(max_steps):
        resp = client.chat.completions.create(
            model=model, messages=convo, tools=tools,
            tool_choice="auto", parallel_tool_calls=True, temperature=0.7,
        )
        msg = resp.choices[0].message
        calls = getattr(msg, "tool_calls", None) or []
        if not calls:
            return {"reply": (msg.content or "").strip(), "tool_events": tool_events}
        convo.append({"role": "assistant", "content": msg.content or "",
                      "tool_calls": [{"id": c.id, "type": "function",
                                      "function": {"name": c.function.name,
                                                   "arguments": c.function.arguments}} for c in calls]})
        for c in calls:
            args = validate_args(c.function.arguments)
            result = handle_function(vertical, c.function.name, {**args, **(extra_args or {})})
            tool_events.append({"name": c.function.name, "arguments": args, "result": result})
            convo.append({"role": "tool", "tool_call_id": c.id,
                          "content": json.dumps(result, ensure_ascii=False)})
    return {"reply": "", "tool_events": tool_events}
