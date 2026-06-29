import os

def _default_client():
    import stripe
    stripe.api_key = os.environ["STRIPE_API_KEY"]
    return stripe

def create_deposit_link(amount_usd: float, description: str, *, client=None) -> dict:
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
