import agent_config


def test_think_block_targets_qwen(monkeypatch):
    monkeypatch.setenv("DASHSCOPE_API_KEY", "sk-test")
    blk = agent_config._think_block("dental")
    assert blk["provider"]["type"] == "open_ai"
    assert "dashscope" in blk["endpoint"]["url"]
    assert blk["provider"]["model"].startswith("qwen")
    assert isinstance(blk["functions"], list) and blk["functions"]
