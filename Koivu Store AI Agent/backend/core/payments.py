"""Test-only Stripe Checkout transport and webhook signature verification."""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import time
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen


STRIPE_CHECKOUT_SESSIONS_URL = "https://api.stripe.com/v1/checkout/sessions"


class StripeCheckoutError(RuntimeError):
    """A safe-to-report payment-provider failure without response secrets."""


def create_test_checkout_session(
    *,
    secret_key: str,
    idempotency_key: str,
    order_id: str,
    user_id: str,
    items: list[dict],
    success_url: str,
    cancel_url: str,
    timeout_seconds: float = 10.0,
) -> dict:
    """Create a Stripe-hosted Checkout Session using only a test-mode key."""
    if not secret_key.startswith("sk_test_"):
        raise StripeCheckoutError("Only a Stripe test-mode secret key is accepted.")
    fields: list[tuple[str, str]] = [
        ("mode", "payment"),
        ("success_url", success_url),
        ("cancel_url", cancel_url),
        ("client_reference_id", order_id),
        ("payment_method_types[0]", "card"),
        ("metadata[order_id]", order_id),
        ("metadata[user_id]", user_id),
    ]
    for index, item in enumerate(items):
        fields.extend((
            (f"line_items[{index}][price_data][currency]", "eur"),
            (f"line_items[{index}][price_data][unit_amount]", str(item["unit_price_cents"])),
            (f"line_items[{index}][price_data][product_data][name]", item["name"]),
            (f"line_items[{index}][quantity]", str(item["quantity"])),
        ))
    authorization = base64.b64encode(f"{secret_key}:".encode("utf-8")).decode("ascii")
    request = Request(
        STRIPE_CHECKOUT_SESSIONS_URL,
        data=urlencode(fields).encode("utf-8"),
        headers={
            "Authorization": f"Basic {authorization}",
            "Content-Type": "application/x-www-form-urlencoded",
            "Idempotency-Key": idempotency_key,
        },
        method="POST",
    )
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            result = json.loads(response.read().decode("utf-8"))
    except (HTTPError, URLError, TimeoutError, OSError, ValueError) as exc:
        raise StripeCheckoutError("Stripe test checkout could not be created.") from exc
    session_id = result.get("id") if isinstance(result, dict) else None
    checkout_url = result.get("url") if isinstance(result, dict) else None
    if not isinstance(session_id, str) or not session_id.startswith("cs_test_"):
        raise StripeCheckoutError("Stripe returned an invalid test checkout session.")
    if not isinstance(checkout_url, str) or not checkout_url.startswith("https://checkout.stripe.com/"):
        raise StripeCheckoutError("Stripe returned an invalid checkout URL.")
    return {"id": session_id, "url": checkout_url}


def parse_verified_webhook(
    payload: bytes,
    signature_header: str,
    endpoint_secret: str,
    *,
    now: int | None = None,
    tolerance_seconds: int = 300,
    max_payload_bytes: int = 1_000_000,
) -> dict:
    """Verify a Stripe webhook over its original raw bytes and parse its JSON."""
    if len(payload) > max_payload_bytes:
        raise ValueError("Webhook body is too large")
    if not signature_header or len(signature_header) > 4096:
        raise ValueError("Missing or invalid Stripe signature")
    timestamp: int | None = None
    signatures: list[str] = []
    for piece in signature_header.split(","):
        key, separator, value = piece.partition("=")
        if not separator:
            continue
        if key == "t" and timestamp is None:
            try:
                timestamp = int(value)
            except ValueError as exc:
                raise ValueError("Invalid Stripe signature timestamp") from exc
        elif key == "v1":
            signatures.append(value)
    current_time = int(time.time()) if now is None else now
    if timestamp is None or abs(current_time - timestamp) > tolerance_seconds or not signatures:
        raise ValueError("Missing, stale, or invalid Stripe signature")
    signed_payload = str(timestamp).encode("ascii") + b"." + payload
    expected = hmac.new(endpoint_secret.encode("utf-8"), signed_payload, hashlib.sha256).hexdigest()
    if not any(hmac.compare_digest(expected, candidate) for candidate in signatures):
        raise ValueError("Invalid Stripe signature")
    try:
        event = json.loads(payload)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ValueError("Invalid Stripe event body") from exc
    if not isinstance(event, dict) or not isinstance(event.get("type"), str):
        raise ValueError("Invalid Stripe event object")
    return event
