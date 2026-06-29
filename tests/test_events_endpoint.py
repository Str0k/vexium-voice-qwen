from fastapi.testclient import TestClient
import server, metrics

def test_summary_route(monkeypatch):
    monkeypatch.setattr(metrics, "summary", lambda t: {"bookings": 2, "revenue_usd": 80,
                                                       "calls": 3, "handoffs": 0, "after_hours": 1})
    c = TestClient(server.app)
    r = c.get("/summary?tenant=dental")
    assert r.status_code == 200 and r.json()["bookings"] == 2
