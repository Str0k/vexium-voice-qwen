import json
import os

from qwen_brain import build_client, validate_args

JUDGE_SYSTEM = (
    "You are a strict QA judge for an AI voice receptionist. Given the call transcript and "
    "the list of tool calls it made, return ONLY a JSON object with keys: "
    "task_completion (integer 0-100, how fully the caller's goal was met), "
    "tool_accuracy (integer 0-100, whether the right tools were called with sane arguments), "
    "hallucination (boolean, true if the agent stated facts not grounded in tools/business data), "
    "notes (short string). Return strictly JSON."
)


def _coerce(d: dict) -> dict:
    def _int(x):
        try:
            return max(0, min(100, int(x)))
        except (TypeError, ValueError):
            return 0

    return {
        "task_completion": _int(d.get("task_completion", 0)),
        "tool_accuracy": _int(d.get("tool_accuracy", 0)),
        "hallucination": bool(d.get("hallucination", False)),
        "notes": str(d.get("notes", "") or ""),
    }


def _extract_json(text: str) -> str:
    """Judges love wrapping verdicts in ```json fences or prose — pull out the
    outermost {...} so a well-scored call never silently coerces to 0/0."""
    t = (text or "").strip()
    start, end = t.find("{"), t.rfind("}")
    return t[start : end + 1] if start != -1 and end > start else t


def score_call(transcript: str, tool_events: list, *, client=None, model=None) -> dict:
    client = client or build_client()
    model = model or os.getenv("QWEN_BRAIN_MODEL", "qwen3-max")
    user = (
        f"Transcript:\n{transcript}\n\nTool calls (JSON):\n"
        f"{json.dumps(tool_events, ensure_ascii=False)}\n\nScore this call. Return JSON only."
    )
    resp = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": JUDGE_SYSTEM}, {"role": "user", "content": user}],
        temperature=0,
    )
    return _coerce(validate_args(_extract_json(resp.choices[0].message.content)))
