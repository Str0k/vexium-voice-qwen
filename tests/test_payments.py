import types

import integrations.payments_stripe as pay


def test_create_deposit_link(monkeypatch):
    created = {}

    def fake_create(**kw):
        created.update(kw)
        return types.SimpleNamespace(
            id="cs_test_123", url="https://checkout.stripe.com/c/pay/cs_test_123"
        )

    fake_stripe = types.SimpleNamespace(
        checkout=types.SimpleNamespace(Session=types.SimpleNamespace(create=fake_create))
    )
    out = pay.create_deposit_link(40.0, "Dental deposit", client=fake_stripe)
    assert out["url"].startswith("https://checkout.stripe.com")
    assert out["session_id"] == "cs_test_123"
    assert created["line_items"][0]["price_data"]["unit_amount"] == 4000  # cents
