"""The upstream ending a call must also release the browser receive task."""

import asyncio
import json

import pytest

import server


@pytest.mark.asyncio
async def test_upstream_close_cancels_browser_receive(monkeypatch):
    receive_stopped = asyncio.Event()

    class Browser:
        query_params = {}
        closed = False

        async def accept(self):
            pass

        async def receive(self):
            try:
                await asyncio.Event().wait()
            finally:
                receive_stopped.set()

        async def close(self):
            self.closed = True

        async def send_text(self, message):
            pytest.fail(f"Unexpected bridge error: {message}")

    class Upstream:
        closed = False

        async def __aenter__(self):
            return self

        async def __aexit__(self, *args):
            await self.close()

        async def send(self, message):
            assert json.loads(message)["type"] == "Settings"

        async def close(self):
            self.closed = True

        async def __aiter__(self):
            await asyncio.sleep(0)
            if False:
                yield b""

    upstream = Upstream()
    browser = Browser()
    monkeypatch.setattr(server, "API_KEY", "test-placeholder")
    monkeypatch.setattr(server, "build_settings", lambda vertical: {"type": "Settings"})
    monkeypatch.setattr(server.websockets, "connect", lambda *args, **kwargs: upstream)
    await asyncio.wait_for(server.ws_endpoint(browser), timeout=1)
    assert receive_stopped.is_set()
    assert browser.closed and upstream.closed
