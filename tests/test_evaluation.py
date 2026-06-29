import json, types
import evaluation as ev

class _M:
    def __init__(self, c): self.content = c
class _Ch:
    def __init__(self, m): self.message = m
class _R:
    def __init__(self, m): self.choices = [_Ch(m)]

class FakeJudge:
    def __init__(self): self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))
    def _create(self, **kw):
        return _R(_M(json.dumps({"task_completion": 90, "tool_accuracy": 100,
                                 "hallucination": False, "notes": "booked + deposit sent"})))

def test_score_call_parses_judge_json():
    out = ev.score_call("user: quiero una limpieza el martes\nassistant: lista su cita",
                        [{"name": "book_appointment", "result": {"status": "confirmed"}}],
                        client=FakeJudge())
    assert out["task_completion"] == 90
    assert out["tool_accuracy"] == 100
    assert out["hallucination"] is False
    assert isinstance(out["notes"], str)

def test_score_call_coerces_bad_or_missing_fields():
    class BadJudge:
        def __init__(self): self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=lambda **k: _R(_M("{not json"))))
    out = ev.score_call("x", [], client=BadJudge())
    assert out["task_completion"] == 0 and out["hallucination"] is False and out["notes"] == ""
