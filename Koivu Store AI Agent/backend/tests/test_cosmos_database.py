"""Offline contract tests for Cosmos partition scoping and conflict behavior."""

import unittest
from datetime import datetime, timedelta, timezone

from core.cosmos_database import CosmosDatabase
from core.database import UserAlreadyExistsError


class CosmosResourceNotFoundError(Exception):
    status_code = 404


class CosmosResourceExistsError(Exception):
    status_code = 409


class FakeContainer:
    partition_fields = {
        "users": "email",
        "sessions": "token_hash",
        "orders": "user_id",
        "support_cases": "user_id",
    }

    def __init__(self, name):
        self.name = name
        self.partition_field = self.partition_fields[name]
        self.items = {}

    def read(self):
        return {}

    def create_item(self, item):
        key = (item["id"], item[self.partition_field])
        if key in self.items:
            raise CosmosResourceExistsError("duplicate")
        item = dict(item)
        item["_etag"] = "etag-1"
        self.items[key] = item
        return item

    def read_item(self, item, partition_key):
        try:
            return dict(self.items[(item, partition_key)])
        except KeyError as exc:
            raise CosmosResourceNotFoundError("missing") from exc

    def delete_item(self, item, partition_key):
        try:
            del self.items[(item, partition_key)]
        except KeyError as exc:
            raise CosmosResourceNotFoundError("missing") from exc

    def query_items(self, query, parameters, partition_key=None):
        candidates = list(self.items.values())
        if partition_key is not None:
            candidates = [item for item in candidates if item[self.partition_field] == partition_key]
        if "c.user_id = @user_id" in query:
            value = next(p["value"] for p in parameters if p["name"] == "@user_id")
            candidates = [item for item in candidates if item.get("user_id") == value]
        if "c.id = @case_id" in query:
            value = next(p["value"] for p in parameters if p["name"] == "@case_id")
            candidates = [item for item in candidates if item.get("id") == value]
        if "c.user_id = @user_id AND c.question = @question" in query:
            values = {p["name"]: p["value"] for p in parameters}
            candidates = [
                item for item in candidates
                if item.get("question") == values["@question"] and item.get("reason") == values["@reason"]
            ]
        if "c.user_id = @user_id AND c.reason = @reason" in query:
            value = next(p["value"] for p in parameters if p["name"] == "@reason")
            candidates = [item for item in candidates if item.get("reason") == value]
        if "c.status = @status" in query:
            value = next(p["value"] for p in parameters if p["name"] == "@status")
            candidates = [item for item in candidates if item.get("status") == value]
        if "c.user_id = @user_id" in query and "@user_id" in [p["name"] for p in parameters]:
            value = next(p["value"] for p in parameters if p["name"] == "@user_id")
            candidates = [item for item in candidates if item.get("user_id") == value]
        if "ORDER BY c.created_at DESC" in query:
            candidates.sort(key=lambda item: item.get("created_at", ""), reverse=True)
        elif "ORDER BY c.created_at ASC" in query:
            candidates.sort(key=lambda item: item.get("created_at", ""))
        if "SELECT TOP 1" in query:
            candidates = candidates[:1]
        return iter(dict(item) for item in candidates)

    def replace_item(self, item, body, etag, match_condition):
        key = (item, body[self.partition_field])
        current = self.items.get(key)
        if current is None:
            raise CosmosResourceNotFoundError("missing")
        if etag != current.get("_etag") or match_condition != "IfNotModified":
            raise AssertionError("replace must use optimistic concurrency")
        updated = dict(body)
        updated["_etag"] = "etag-2"
        self.items[key] = updated
        return updated


class FakeDatabase:
    def __init__(self):
        self.containers = {name: FakeContainer(name) for name in FakeContainer.partition_fields}

    def get_container_client(self, name):
        return self.containers[name]

    def read(self):
        return {}


class FakeClient:
    def __init__(self):
        self.database = FakeDatabase()

    def get_database_client(self, name):
        return self.database

    def close(self):
        pass


class FakeCredential:
    def close(self):
        pass


class CosmosDatabaseTests(unittest.TestCase):
    def setUp(self):
        self.db = CosmosDatabase(
            "https://example.documents.azure.com:443/",
            "koivu",
            client=FakeClient(),
            credential=FakeCredential(),
            match_condition="IfNotModified",
        )

    def test_normalized_email_conflict_uses_shared_database_error(self):
        self.db.create_user("user-1", "customer@example.test", "pbkdf2-hash")
        with self.assertRaises(UserAlreadyExistsError):
            self.db.create_user("user-2", "customer@example.test", "other-hash")
        self.assertEqual(self.db.get_user_by_email("customer@example.test")["id"], "user-1")

    def test_session_is_partitioned_by_digest_and_expires(self):
        self.db.create_user("user-1", "customer@example.test", "pbkdf2-hash")
        expires_at = (datetime.now(timezone.utc) + timedelta(hours=12)).isoformat()
        self.db.create_session("token-digest", "user-1", expires_at)
        self.assertEqual(self.db.get_session_user("token-digest"), {"id": "user-1", "email": "customer@example.test"})
        self.db.delete_session("token-digest")
        self.assertIsNone(self.db.get_session_user("token-digest"))

    def test_order_reads_and_deletes_are_owner_partition_scoped(self):
        order = self.db.create_order("ORD-12345678", "user-1", [{"product_id": "merino"}], 8900)
        self.assertEqual(order["total_cents"], 8900)
        self.assertEqual(self.db.get_owned_order(order["id"], "user-1")["items"][0]["product_id"], "merino")
        self.assertIsNone(self.db.get_owned_order(order["id"], "user-2"))
        self.assertFalse(self.db.delete_owned_order(order["id"], "user-2"))
        self.assertTrue(self.db.delete_owned_order(order["id"], "user-1"))

    def test_support_read_is_owner_scoped_and_update_uses_etag(self):
        case = self.db.create_support_case("case-1", "user-1", "Where is my order?", "review", {"intent": "support"})
        self.assertIsNone(self.db.get_support_case(case["id"], "user-2"))
        replied = self.db.reply_to_support_case(case["id"], "We will review it.")
        self.assertEqual(replied["status"], "answered")
        self.assertEqual(replied["human_response"], "We will review it.")


if __name__ == "__main__":
    unittest.main()
