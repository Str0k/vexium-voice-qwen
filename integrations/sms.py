import json
import os


def _alibaba(to: str, body: str) -> dict:
    from alibabacloud_dysmsapi20170525 import models as sms_models
    from alibabacloud_dysmsapi20170525.client import Client
    from alibabacloud_tea_openapi import models as om

    cfg = om.Config(
        access_key_id=os.environ["ALIBABA_SMS_ACCESS_KEY_ID"],
        access_key_secret=os.environ["ALIBABA_SMS_ACCESS_KEY_SECRET"],
    )
    cfg.endpoint = "dysmsapi.ap-southeast-1.aliyuncs.com"
    req = sms_models.SendSmsRequest(
        phone_numbers=to,
        sign_name=os.environ["ALIBABA_SMS_SIGN_NAME"],
        template_code=os.environ["ALIBABA_SMS_TEMPLATE_CODE"],
        template_param=json.dumps({"msg": body}),
    )
    resp = Client(cfg).send_sms(req)
    return {"status": "sent", "provider": "alibaba", "detail": resp.body.code}


def _twilio(to: str, body: str) -> dict:
    from twilio.rest import Client

    c = Client(os.environ["TWILIO_ACCOUNT_SID"], os.environ["TWILIO_AUTH_TOKEN"])
    m = c.messages.create(to=to, from_=os.environ["TWILIO_PHONE_NUMBER"], body=body)
    return {"status": "sent", "provider": "twilio", "detail": m.sid}


def send_sms(to: str, body: str, *, provider=None) -> dict:
    if provider is not None:
        return provider(to, body)
    kind = os.getenv("SMS_PROVIDER", "none").lower()
    try:
        if kind == "alibaba":
            return _alibaba(to, body)
        if kind == "twilio":
            return _twilio(to, body)
        return {"status": "skipped", "provider": "none", "detail": "no SMS provider configured"}
    except Exception as exc:
        return {"status": "error", "provider": kind, "detail": str(exc)}
