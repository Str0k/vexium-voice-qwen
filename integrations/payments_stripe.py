import os
import uuid

def _default_client():
    import stripe
    stripe.api_key = os.environ["STRIPE_API_KEY"]
    return stripe

def create_deposit_link(amount_usd: float, description: str, *, client=None) -> dict:
    if client is None and not os.getenv("STRIPE_API_KEY", "").strip():
        # Demo mode — no Stripe key: return an obviously-fake link so the flow
        # completes end-to-end; /status reports payments as simulated.
        return {"url": f"https://demo-checkout.invalid/deposit-{int(round(amount_usd))}usd",
                "session_id": f"sim_{uuid.uuid4().hex[:10]}", "simulated": True}
    client = client or _default_client()
    session = client.checkout.Session.create(
        mode="payment",
        success_url=os.getenv("STRIPE_SUCCESS_URL", "https://example.com/paid"),
        line_items=[{
            "quantity": 1,
            "price_data": {
                "currency": "usd",
                "unit_amount": int(round(amount_usd * 100)),
                "product_data": {"name": description},
            },
        }],
    )
    return {"url": session.url, "session_id": session.id}
