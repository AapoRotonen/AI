"""API, account, order ownership, and support-case security regression tests."""

import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from core.config import Settings
from core.database import Database
from core.orders import OrderStatusService
from core.security import token_digest
from main import SESSION_COOKIE, create_app


class ApiSecurityTests(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.database = Database(Path(self.temp_dir.name) / "test.sqlite3")
        self.config = Settings(
            database_path=str(self.database.path),
            support_agent_api_key="test-support-key",
            catalog_setup_api_key="test-catalog-key",
            cookie_secure=False,
            openai_api_key="",
            tavily_api_key="",
            cors_allowed_origins="http://127.0.0.1:5500",
        )
        self.app = create_app(self.database, self.config)
        self.client_context = TestClient(self.app)
        self.client = self.client_context.__enter__()

    def tearDown(self):
        self.client_context.__exit__(None, None, None)
        self.temp_dir.cleanup()

    @staticmethod
    def credentials(email="customer@example.test", password="A-long-demo-password-42!"):
        return {"email": email, "password": password}

    def register(self, client=None, email="customer@example.test"):
        target = client or self.client
        response = target.post("/auth/register", json=self.credentials(email))
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def create_order(self, client=None):
        target = client or self.client
        response = target.post("/orders", json={"items": [{
            "product_id": "merino", "color": "Forest", "size": "M", "quantity": 1,
        }]})
        self.assertEqual(response.status_code, 201, response.text)
        return response.json()

    def test_registration_stores_only_a_salted_password_hash_and_issues_http_only_session(self):
        with self.assertLogs("koivu.events", level="INFO") as captured:
            response = self.client.post("/auth/register", json=self.credentials())
        self.assertEqual(response.status_code, 201)
        self.assertNotIn("password", response.json())
        self.assertNotIn(self.credentials()["email"], "".join(captured.output))
        self.assertNotIn(self.credentials()["password"], "".join(captured.output))
        cookie = self.client.cookies.get(SESSION_COOKIE)
        self.assertTrue(cookie)
        self.assertIn("httponly", response.headers["set-cookie"].lower())
        self.assertIn("samesite=strict", response.headers["set-cookie"].lower())
        user = self.database.get_user_by_email(self.credentials()["email"])
        self.assertNotEqual(user["password_hash"], self.credentials()["password"])
        self.assertTrue(user["password_hash"].startswith("pbkdf2_sha256$"))
        self.assertIsNotNone(self.database.get_session_user(token_digest(cookie)))

    def test_login_logout_and_protected_order_list(self):
        self.register()
        me = self.client.get("/auth/me")
        self.assertEqual(me.headers["cache-control"], "no-store")
        self.assertTrue(me.headers["x-request-id"])
        self.client.post("/auth/logout")
        self.assertEqual(self.client.get("/orders").status_code, 401)
        login = self.client.post("/auth/login", json=self.credentials())
        self.assertEqual(login.status_code, 200)
        order = self.create_order()
        self.assertEqual(self.client.get("/orders").json()[0]["id"], order["id"])
        self.assertEqual(self.client.post("/auth/logout").status_code, 200)
        self.assertEqual(self.client.get("/auth/me").json(), {"authenticated": False, "user": None})

    def test_login_errors_are_generic_and_registration_rejects_weak_password(self):
        invalid = self.client.post("/auth/login", json=self.credentials("nobody@example.test", "Wrong-password-44!"))
        self.assertEqual(invalid.status_code, 401)
        weak = self.client.post("/auth/register", json={"email": "weak@example.test", "password": "short"})
        self.assertEqual(weak.status_code, 422)

    def test_order_tool_is_bound_to_authenticated_owner_and_hides_foreign_orders(self):
        first_user = self.register()
        first_order = self.create_order()
        first_tool = OrderStatusService(self.database).as_agent_tool(first_user["id"])
        self.assertEqual(first_tool.invoke({"order_id": first_order["id"]})["status"], "processing")

        second_client = TestClient(self.app)
        with second_client:
            second_user = self.register(second_client, "second@example.test")
            second_order = self.create_order(second_client)
            second_tool = OrderStatusService(self.database).as_agent_tool(second_user["id"])
            self.assertIsNone(second_tool.invoke({"order_id": first_order["id"]}))
            self.assertEqual(second_client.get("/orders").json(), [second_order])

        with self.assertRaises(Exception):
            first_tool.invoke({"order_id": "../../database"})

    def test_order_cancellation_is_authenticated_and_owner_scoped(self):
        first_user = self.register()
        first_order = self.create_order()
        self.client.post("/auth/logout")
        self.assertEqual(self.client.delete(f"/orders/{first_order['id']}").status_code, 401)
        self.client.post("/auth/login", json=self.credentials())

        second_client = TestClient(self.app)
        with second_client:
            self.register(second_client, "second@example.test")
            second_order = self.create_order(second_client)
            self.assertEqual(second_client.delete(f"/orders/{first_order['id']}").status_code, 404)
            self.assertEqual(second_client.get("/orders").json(), [second_order])

        cancelled = self.client.delete(f"/orders/{first_order['id']}")
        self.assertEqual(cancelled.status_code, 204)
        self.assertEqual(cancelled.content, b"")
        self.assertEqual(self.client.get("/orders").json(), [])
        self.assertIsNone(self.database.get_owned_order(first_order["id"], first_user["id"]))

    def test_order_status_without_reference_uses_latest_owned_order(self):
        user = self.register()
        first = self.create_order()
        latest = self.create_order()
        tool = OrderStatusService(self.database).as_agent_tool(user["id"])
        result = tool.invoke({})
        self.assertEqual(result["order_id"], latest["id"])
        self.assertNotEqual(result["order_id"], first["id"])
        self.assertEqual(result["status"], "processing")

    def test_support_case_is_persisted_redacted_and_only_visible_to_owner(self):
        user = self.register()
        message = "Please call +358 40 123 4567 at anna@example.test about order ORD-12345678."
        created = self.client.post("/human-chat", json={"message": message, "history": []})
        self.assertEqual(created.status_code, 200, created.text)
        self.assertIn("kirjattu asiakaspalvelun", created.json()["answer"])
        case_id = created.json()["support_case_id"]
        repeated = self.client.post("/human-chat", json={"message": message, "history": []})
        self.assertEqual(repeated.json()["support_case_id"], case_id)
        self.assertEqual(len(self.database.list_user_support_cases(user["id"])), 1)
        stored = self.database.get_support_case(case_id, user["id"])
        self.assertNotIn("anna@example.test", stored["question"])
        self.assertNotIn("+358 40 123 4567", stored["question"])
        self.assertIn("ORD-12345678", stored["question"])
        self.assertEqual(stored["status"], "open")
        self.assertEqual(self.client.get(f"/support/cases/{case_id}").json()["status"], "open")
        self.assertEqual(self.client.get("/support/my-cases").json()[0]["id"], case_id)

        other = TestClient(self.app)
        with other:
            self.register(other, "other@example.test")
            self.assertEqual(other.get(f"/support/cases/{case_id}").status_code, 404)

    def test_customer_can_load_a_canned_demo_agent_reply_into_their_case(self):
        self.register()
        case_id = self.client.post("/human-chat", json={"message": "Saisinko ihmisen chattiin?", "history": []}).json()["support_case_id"]
        response = self.client.post(f"/support/my-cases/{case_id}/demo-reply")
        self.assertEqual(response.status_code, 200, response.text)
        self.assertEqual(response.json()["status"], "answered")
        self.assertTrue(response.json()["demo_response"])
        self.assertIn("demokäsittelijä", response.json()["human_response"].casefold())
        self.assertEqual(self.client.get(f"/support/cases/{case_id}").json()["human_response"], response.json()["human_response"])

    def test_support_agent_must_authenticate_to_reply_and_close(self):
        self.register()
        case_id = self.client.post("/human-chat", json={"message": "I need help", "history": []}).json()["support_case_id"]
        self.assertEqual(self.client.get("/support/cases").status_code, 401)
        self.assertEqual(
            self.client.get("/support/cases", headers={"X-Support-Agent-Key": "wrong"}).status_code,
            401,
        )
        staff = {"X-Support-Agent-Key": "test-support-key"}
        cases = self.client.get("/support/cases?status=open", headers=staff)
        self.assertEqual(cases.status_code, 200)
        self.assertEqual(cases.json()[0]["id"], case_id)
        reply = self.client.post(
            f"/support/cases/{case_id}/reply",
            headers=staff,
            json={"response": "Tarkistin asian. Palaamme asiaan pian."},
        )
        self.assertEqual(reply.status_code, 200)
        self.assertEqual(self.client.get(f"/support/cases/{case_id}").json()["human_response"], "Tarkistin asian. Palaamme asiaan pian.")
        closed = self.client.post(f"/support/cases/{case_id}/close", headers=staff)
        self.assertEqual(closed.json()["status"], "closed")

    def test_ordinary_escalation_does_not_create_a_support_case(self):
        user = self.register()
        self.database.create_demo_order("ORD-12345678", user["id"])
        result = {
            "answer": "En löytänyt lähteistä vastausta.",
            "intent": "product",
            "should_escalate": True,
            "path_taken": "RAG → automaattinen fallback",
            "create_support_case": False,
        }
        with patch("main.get_agent") as agent:
            agent.return_value.invoke.return_value = result
            response = self.client.post("/chat", json={"message": "Do you sell these shoes?", "history": []})
        self.assertEqual(response.status_code, 200)
        self.assertIsNone(response.json()["support_case_id"])
        self.assertEqual(self.database.list_user_support_cases(user["id"]), [])

    def test_escalation_requires_login_and_does_not_store_anonymous_request(self):
        result = {
            "answer": "fallback",
            "intent": "personal_support",
            "should_escalate": True,
            "path_taken": "Tilaustuki",
            "auth_required": True,
            "create_support_case": False,
            "escalation_reason": "order_not_found_or_not_owned",
        }
        with patch("main.get_agent") as agent:
            agent.return_value.invoke.return_value = result
            response = self.client.post("/chat", json={"message": "Where is my order 123?", "history": []})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["auth_required"])
        self.assertIsNone(response.json()["support_case_id"])
        self.assertEqual(self.database.list_support_cases(), [])


if __name__ == "__main__":
    unittest.main()
