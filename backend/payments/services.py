import base64
import hashlib
import hmac
import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings


class RazorpayError(Exception):
    pass


def razorpay_is_configured():
    return bool(
        settings.RAZORPAY_KEY_ID.startswith("rzp_test_")
        and settings.RAZORPAY_KEY_SECRET
    )


def _request(path, method="GET", payload=None):
    credentials = f"{settings.RAZORPAY_KEY_ID}:{settings.RAZORPAY_KEY_SECRET}".encode()
    authorization = base64.b64encode(credentials).decode("ascii")
    data = json.dumps(payload).encode("utf-8") if payload is not None else None
    request = Request(
        f"https://api.razorpay.com/v1/{path.lstrip('/')}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
    )
    try:
        with urlopen(request, timeout=15) as response:
            return json.loads(response.read())
    except (HTTPError, URLError, TimeoutError, OSError, json.JSONDecodeError) as error:
        raise RazorpayError("Razorpay could not complete the request.") from error


def create_razorpay_order(amount_paise, receipt, notes):
    result = _request(
        "orders",
        method="POST",
        payload={
            "amount": amount_paise,
            "currency": "INR",
            "receipt": receipt,
            "notes": notes,
        },
    )
    if not isinstance(result, dict) or not isinstance(result.get("id"), str):
        raise RazorpayError("Razorpay returned an invalid order response.")
    return result


def fetch_razorpay_payment(payment_id):
    result = _request(f"payments/{payment_id}")
    if not isinstance(result, dict):
        raise RazorpayError("Razorpay returned an invalid payment response.")
    return result


def verify_razorpay_signature(order_id, payment_id, signature):
    message = f"{order_id}|{payment_id}".encode("utf-8")
    expected = hmac.new(
        settings.RAZORPAY_KEY_SECRET.encode("utf-8"),
        message,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected, signature)
