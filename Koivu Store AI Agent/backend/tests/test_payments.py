"""Offline tests for test-mode Checkout and signed, idempotent payment events."""

from __future__ import annotations

import hashlib
import hmac
import json
import tempfile
import time
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch
from urllib.parse import parse_qs

from fastapi.testclient import TestClient

from core.config import Settings
from core.database import Database
from core.payments import create_test_checkout_session, parse_verified_webhook
from main import create_app


class StripeTestCheckoutTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "payments.sqlite3")
        self.webhook_secret = "whsec_test_only_value"
        self.settings = Settings(
            app_environment="local",
            database_backend="sqlite",
            database_path=str(self.database.path),
            cookie_secure=False,
            openai_api_key="",
            tavily_api_key="",
            stripe_secret_key="sk_test_unit_test_only",
            stripe_webhook_secret=self.webhook_secret,
            public_app_url="http://testserver",
        )
        self.context = TestClient(create_app(self.database, self.settings))
        self.client = self.context.__enter__()

    def tearDown(self):
        self.context.__exit__(None, None, None)
        self.temp_dir.cleanup()

    @staticmethod
    def sign(payload: bytes, secret: str, timestamp: int | None = None) -> str:
        stamp = int(time.time()) if timestamp is None else timestamp
        digest = hmac.new(secret.encode(), str(stamp).encode() + b"." + payload, hashlib.sha256).hexdigest()
        return f"t={stamp},v1={digest}"

    def register(self):
        result = self.client.post("/auth/register", json={
            "email": "payment@example.test",
            "password": "A-long-demo-password-42!",
        })
        self.assertEqual(result.status_code, 201, result.text)
        return result.json()

    def test_checkout_uses_server_price_and_signed_webhook_updates_order_once(self):
        user = self.register()
        provider_response = MagicMock()
        provider_response.__enter__.return_value = provider_response
        provider_response.read.return_value = json.dumps({
            "id": "cs_test_example_session",
            "url": "https://checkout.stripe.com/c/pay/cs_test_example_session",
        }).encode()
        with patch("core.payments.urlopen", return_value=provider_response) as mocked_urlopen:
            checkout = self.client.post("/payments/checkout-session", json={"items": [{
                "product_id": "merino", "color": "Forest", "size": "M", "quantity": 1,
            }]})
        self.assertEqual(checkout.status_code, 200, checkout.text)
        self.assertEqual(checkout.json()["checkout_url"], "https://checkout.stripe.com/c/pay/cs_test_example_session")
        self.assertNotIn("sk_test", checkout.text)
        request = mocked_urlopen.call_args.args[0]
        form = parse_qs(request.data.decode())
        self.assertEqual(form["line_items[0][price_data][unit_amount]"], ["8900"])
        self.assertEqual(form["line_items[0][quantity]"], ["1"])
        self.assertEqual(form["metadata[user_id]"], [user["id"]])
        self.assertEqual(form["success_url"], ["http://testserver/?payment=success"])
        self.assertTrue(request.get_header("Idempotency-key"))

        order = self.database.list_owned_orders(user["id"])[0]
        self.assertEqual(order["status"], "pending_payment")
        self.assertEqual(order["total_cents"], 8900)
        self.assertEqual(order["checkout_session_id"], "cs_test_example_session")
        self.assertEqual(self.client.delete(f"/orders/{order['id']}").status_code, 404)

        event = {
            "id": "evt_test_paid",
            "type": "checkout.session.completed",
            "data": {"object": {
                "id": "cs_test_example_session",
                "payment_status": "paid",
                "metadata": {"order_id": order["id"], "user_id": user["id"]},
            }},
        }
        raw = json.dumps(event, separators=(",", ":")).encode()
        headers = {"Stripe-Signature": self.sign(raw, self.webhook_secret)}
        first = self.client.post("/payments/webhook", content=raw, headers=headers)
        second = self.client.post("/payments/webhook", content=raw, headers=headers)
        self.assertEqual(first.status_code, 200, first.text)
        self.assertEqual(second.status_code, 200, second.text)
        self.assertEqual(self.database.get_owned_order(order["id"], user["id"])["status"], "paid")

    def test_invalid_signature_does_not_change_order(self):
        self.register()
        body = json.dumps({"type": "checkout.session.completed", "data": {"object": {}}}).encode()
        response = self.client.post("/payments/webhook", content=body, headers={"Stripe-Signature": "t=1,v1=wrong"})
        self.assertEqual(response.status_code, 400)

    def test_unconfigured_checkout_is_disabled(self):
        self.client.post("/auth/logout")
        app = create_app(self.database, Settings(
            app_environment="local",
            database_backend="sqlite",
            database_path=str(self.database.path),
            cookie_secure=False,
            openai_api_key="",
            tavily_api_key="",
        ))
        with TestClient(app) as client:
            self.assertEqual(client.get("/payments/config").json(), {"test_checkout_enabled": False})
            registered = client.post("/auth/register", json={
                "email": "disabled@example.test",
                "password": "A-long-demo-password-42!",
            })
            self.assertEqual(registered.status_code, 201, registered.text)
            response = client.post("/payments/checkout-session", json={"items": [{
                "product_id": "merino", "color": "Forest", "size": "M", "quantity": 1,
            }]})
            self.assertEqual(response.status_code, 503)

    def test_checkout_session_persist_failure_cleans_up_unreachable_order(self):
        user = self.register()
        provider_response = MagicMock()
        provider_response.__enter__.return_value = provider_response
        provider_response.read.return_value = json.dumps({
            "id": "cs_test_orphaned_session",
            "url": "https://checkout.stripe.com/c/pay/cs_test_orphaned_session",
        }).encode()
        with patch("core.payments.urlopen", return_value=provider_response), patch.object(
            Database, "set_checkout_session", return_value=False
        ):
            response = self.client.post("/payments/checkout-session", json={"items": [{
                "product_id": "merino", "color": "Forest", "size": "M", "quantity": 1,
            }]})
        self.assertEqual(response.status_code, 503)
        self.assertEqual(self.database.list_owned_orders(user["id"]), [])

    def test_webhook_verifier_checks_age_and_exact_payload(self):
        payload = b'{"type":"checkout.session.completed"}'
        timestamp = 1_700_000_000
        valid_header = self.sign(payload, self.webhook_secret, timestamp)
        with self.assertRaisesRegex(ValueError, "stale"):
            parse_verified_webhook(payload, valid_header, self.webhook_secret, now=timestamp + 301)
        with self.assertRaisesRegex(ValueError, "signature"):
            parse_verified_webhook(payload + b" ", valid_header, self.webhook_secret, now=timestamp)

    def test_only_test_mode_keys_are_accepted(self):
        with self.assertRaisesRegex(ValueError, "test-mode"):
            Settings(stripe_secret_key="sk_live_not_allowed", stripe_webhook_secret="whsec_test", public_app_url="https://koivu.example")

    def test_partial_stripe_test_configuration_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "requires STRIPE_SECRET_KEY"):
            Settings(stripe_secret_key="sk_test_only_one", stripe_webhook_secret="", public_app_url="")


class StripeTransportTests(unittest.TestCase):
    def test_live_key_is_rejected_before_network_access(self):
        with patch("core.payments.urlopen") as urlopen:
            with self.assertRaisesRegex(Exception, "test-mode"):
                create_test_checkout_session(
                    secret_key="sk_live_never_allowed",
                    idempotency_key="koivu-order-1",
                    order_id="ORD-12345678",
                    user_id="user-1",
                    items=[],
                    success_url="https://koivu.example/?payment=success",
                    cancel_url="https://koivu.example/?payment=cancelled",
                )
        urlopen.assert_not_called()


if __name__ == "__main__":
    unittest.main()
