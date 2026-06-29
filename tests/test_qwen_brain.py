import json, types
import qwen_brain

class _Msg:
    def __init__(self, content=None, tool_calls=None):
        self.content = content
        self.tool_calls = tool_calls or []
class _Call:
    def __init__(self, _id, name, args):
        self.id = _id
        self.type = "function"
        self.function = types.SimpleNamespace(name=name, arguments=json.dumps(args))
class _Choice:
    def __init__(self, msg): self.message = msg
class _Resp:
    def __init__(self, msg): self.choices = [_Choice(msg)]

class FakeClient:
    """First call -> requests check_availability; second call -> final text."""
    def __init__(self):
        self._step = 0
        self.chat = types.SimpleNamespace(completions=types.SimpleNamespace(create=self._create))
    def _create(self, **kw):
        self._step += 1
        if self._step == 1:
            return _Resp(_Msg(tool_calls=[_Call("c1", "check_availability",
                                                {"requested_datetime": "2026-07-07T14:00"})]))
        return _Resp(_Msg(content="Listo, su cita quedó agendada."))

def test_run_turn_executes_tool_then_returns_reply():
    tools = [{"type": "function", "function": {"name": "check_availability",
              "parameters": {"type": "object", "properties": {"requested_datetime": {"type": "string"}}}}}]
    out = qwen_brain.run_turn(
        messages=[{"role": "user", "content": "¿hay espacio el martes a las 2?"}],
        tools=tools, vertical="dental", client=FakeClient())
    assert out["reply"] == "Listo, su cita quedó agendada."
    assert out["tool_events"][0]["name"] == "check_availability"
    assert out["tool_events"][0]["result"]["available"] is True

def test_validate_args_repairs_bad_json():
    assert qwen_brain.validate_args("{bad json") == {}
    assert qwen_brain.validate_args('{"a": 1}') == {"a": 1}
