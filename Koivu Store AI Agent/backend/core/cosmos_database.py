"""Azure Cosmos DB implementation of Koivu's owner-scoped persistence contract."""

from __future__ import annotations

import json
from datetime import datetime, timezone

from core.database import UserAlreadyExistsError, utc_now


class CosmosDatabase:
    """Cosmos-backed store. Containers and their partition keys are provisioned by Bicep."""

    def __init__(self, endpoint: str, database_name: str, managed_identity_client_id: str = "", *, client=None, credential=None, match_condition=None):
        if client is None or credential is None or match_condition is None:
            from azure.core import MatchConditions
            from azure.cosmos import CosmosClient
            from azure.identity import DefaultAzureCredential

            credential = credential or DefaultAzureCredential(
                managed_identity_client_id=managed_identity_client_id or None,
                exclude_interactive_browser_credential=True,
            )
            client = client or CosmosClient(endpoint, credential=credential)
            match_condition = match_condition or MatchConditions.IfNotModified
        self.credential = credential
        self.client = client
        self.match_condition = match_condition
        self.database = self.client.get_database_client(database_name)
        self.users = self.database.get_container_client("users")
        self.sessions = self.database.get_container_client("sessions")
        self.orders = self.database.get_container_client("orders")
        self.support_cases = self.database.get_container_client("support_cases")
        self.initialized = False

    def initialize(self) -> None:
        # Fail fast if IaC has not created the expected database/containers.
        self.database.read()
        for container in (self.users, self.sessions, self.orders, self.support_cases):
            container.read()
        self.initialized = True

    def close(self) -> None:
        self.client.close()
        self.credential.close()

    @staticmethod
    def _public(item: dict | None) -> dict | None:
        if item is None:
            return None
        return {key: value for key, value in item.items() if not key.startswith("_") and key != "ttl"}

    @staticmethod
    def _is_sdk_error(error: Exception, name: str, status_code: int) -> bool:
        return type(error).__name__ == name or getattr(error, "status_code", None) == status_code

    @staticmethod
    def _to_order(item: dict | None) -> dict | None:
        result = CosmosDatabase._public(item)
        if result is not None:
            result["total_cents"] = int(result.get("total_cents") or 0)
            result["items"] = result.get("items") or []
        return result

    @staticmethod
    def _to_case(item: dict | None) -> dict | None:
        result = CosmosDatabase._public(item)
        if result is not None:
            context = result.get("safe_context", {})
            result["safe_context"] = json.loads(context) if isinstance(context, str) else context
            result["demo_response"] = bool(result.get("demo_response", False))
        return result

    @staticmethod
    def _query_one(
        container,
        query: str,
        parameters: list[dict],
        partition_key=None,
        enable_cross_partition_query: bool = False,
    ) -> dict | None:
        results = list(container.query_items(
            query=query,
            parameters=parameters,
            partition_key=partition_key,
            enable_cross_partition_query=enable_cross_partition_query,
        ))
        return results[0] if results else None

    def create_user(self, user_id: str, email: str, password_hash: str) -> None:
        item = {
            "id": email,
            "user_id": user_id,
            "email": email,
            "password_hash": password_hash,
            "created_at": utc_now(),
        }
        try:
            self.users.create_item(item)
        except Exception as exc:
            if self._is_sdk_error(exc, "CosmosResourceExistsError", 409):
                raise UserAlreadyExistsError(email) from exc
            raise

    def get_user_by_email(self, email: str) -> dict | None:
        try:
            item = self.users.read_item(item=email, partition_key=email)
        except Exception as exc:
            if self._is_sdk_error(exc, "CosmosResourceNotFoundError", 404):
                return None
            raise
        return {"id": item["user_id"], "email": item["email"], "password_hash": item["password_hash"]}

    def get_public_user(self, user_id: str) -> dict | None:
        item = self._query_one(
            self.users,
            "SELECT TOP 1 c.user_id, c.email FROM c WHERE c.user_id = @user_id",
            [{"name": "@user_id", "value": user_id}],
            enable_cross_partition_query=True,
        )
        return {"id": item["user_id"], "email": item["email"]} if item else None

    def create_session(self, token_hash: str, user_id: str, expires_at: str) -> None:
        user = self.get_public_user(user_id)
        if user is None:
            raise ValueError("Cannot create a session for a missing user")
        expires = datetime.fromisoformat(expires_at)
        ttl = max(1, int((expires - datetime.now(timezone.utc)).total_seconds()))
        self.sessions.create_item({
            "id": token_hash,
            "token_hash": token_hash,
            "user_id": user_id,
            "email": user["email"],
            "expires_at": expires_at,
            "ttl": ttl,
        })

    def get_session_user(self, token_hash: str) -> dict | None:
        try:
            session = self.sessions.read_item(item=token_hash, partition_key=token_hash)
        except Exception as exc:
            if self._is_sdk_error(exc, "CosmosResourceNotFoundError", 404):
                return None
            raise
        if datetime.fromisoformat(session["expires_at"]) <= datetime.now(timezone.utc):
            self.delete_session(token_hash)
            return None
        return {"id": session["user_id"], "email": session["email"]}

    def delete_session(self, token_hash: str) -> None:
        try:
            self.sessions.delete_item(item=token_hash, partition_key=token_hash)
        except Exception as exc:
            if not self._is_sdk_error(exc, "CosmosResourceNotFoundError", 404):
                raise

    def create_demo_order(self, order_id: str, user_id: str) -> dict:
        return self.create_order(order_id, user_id, [], 0)

    def create_order(self, order_id: str, user_id: str, items: list[dict], total_cents: int) -> dict:
        item = {
            "id": order_id,
            "user_id": user_id,
            "status": "processing",
            "tracking_code": None,
            "created_at": utc_now(),
            "items": items,
            "total_cents": total_cents,
        }
        self.orders.create_item(item)
        return self._to_order(item) or {}

    def delete_owned_order(self, order_id: str, user_id: str) -> bool:
        try:
            self.orders.delete_item(item=order_id, partition_key=user_id)
            return True
        except Exception as exc:
            if self._is_sdk_error(exc, "CosmosResourceNotFoundError", 404):
                return False
            raise

    def get_owned_order(self, order_id: str, user_id: str) -> dict | None:
        try:
            item = self.orders.read_item(item=order_id, partition_key=user_id)
        except Exception as exc:
            if self._is_sdk_error(exc, "CosmosResourceNotFoundError", 404):
                return None
            raise
        return self._to_order(item)

    def get_latest_owned_order(self, user_id: str) -> dict | None:
        item = self._query_one(
            self.orders,
            "SELECT TOP 1 * FROM c WHERE c.user_id = @user_id ORDER BY c.created_at DESC",
            [{"name": "@user_id", "value": user_id}],
            partition_key=user_id,
        )
        return self._to_order(item)

    def list_owned_orders(self, user_id: str) -> list[dict]:
        items = self.orders.query_items(
            query="SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.created_at DESC",
            parameters=[{"name": "@user_id", "value": user_id}],
            partition_key=user_id,
        )
        return [self._to_order(item) for item in items]

    def find_open_support_case(self, user_id: str, question: str, reason: str) -> dict | None:
        item = self._query_one(
            self.support_cases,
            "SELECT TOP 1 * FROM c WHERE c.user_id = @user_id AND c.question = @question "
            "AND c.reason = @reason AND c.status = 'open' ORDER BY c.created_at DESC",
            [
                {"name": "@user_id", "value": user_id},
                {"name": "@question", "value": question},
                {"name": "@reason", "value": reason},
            ],
            partition_key=user_id,
        )
        return self._to_case(item)

    def find_latest_open_support_case(self, user_id: str, reason: str) -> dict | None:
        item = self._query_one(
            self.support_cases,
            "SELECT TOP 1 * FROM c WHERE c.user_id = @user_id AND c.reason = @reason "
            "AND c.status = 'open' ORDER BY c.created_at DESC",
            [{"name": "@user_id", "value": user_id}, {"name": "@reason", "value": reason}],
            partition_key=user_id,
        )
        return self._to_case(item)

    def create_support_case(
        self, case_id: str, user_id: str, question: str, reason: str, safe_context: dict
    ) -> dict:
        now = utc_now()
        item = {
            "id": case_id,
            "user_id": user_id,
            "question": question,
            "reason": reason,
            "safe_context": safe_context,
            "status": "open",
            "human_response": None,
            "demo_response": False,
            "created_at": now,
            "updated_at": now,
        }
        self.support_cases.create_item(item)
        return self._to_case(item) or {}

    def get_support_case(self, case_id: str, user_id: str | None = None) -> dict | None:
        if user_id is not None:
            try:
                item = self.support_cases.read_item(item=case_id, partition_key=user_id)
            except Exception as exc:
                if self._is_sdk_error(exc, "CosmosResourceNotFoundError", 404):
                    return None
                raise
            return self._to_case(item) if item.get("user_id") == user_id else None
        item = self._query_one(
            self.support_cases,
            "SELECT TOP 1 * FROM c WHERE c.id = @case_id",
            [{"name": "@case_id", "value": case_id}],
        )
        return self._to_case(item)

    def list_support_cases(self, status: str | None = None) -> list[dict]:
        query = "SELECT * FROM c"
        parameters = []
        if status:
            query += " WHERE c.status = @status"
            parameters.append({"name": "@status", "value": status})
        query += " ORDER BY c.created_at ASC"
        items = self.support_cases.query_items(query=query, parameters=parameters)
        return [self._to_case(item) for item in items]

    def list_user_support_cases(self, user_id: str) -> list[dict]:
        items = self.support_cases.query_items(
            query="SELECT * FROM c WHERE c.user_id = @user_id ORDER BY c.created_at DESC",
            parameters=[{"name": "@user_id", "value": user_id}],
            partition_key=user_id,
        )
        return [self._to_case(item) for item in items]

    def delete_user_support_cases(self, user_id: str) -> int:
        cases = self.list_user_support_cases(user_id)
        for case in cases:
            self.support_cases.delete_item(item=case["id"], partition_key=user_id)
        return len(cases)

    def _replace_case(self, case_id: str, update) -> dict | None:
        case = self.get_support_case(case_id)
        if case is None or case["status"] == "closed":
            return None
        try:
            stored = self.support_cases.read_item(item=case_id, partition_key=case["user_id"])
            updated = update(dict(stored))
            self.support_cases.replace_item(
                item=case_id,
                body=updated,
                etag=stored.get("_etag"),
                match_condition=self.match_condition,
            )
        except Exception as exc:
            if self._is_sdk_error(exc, "CosmosResourceNotFoundError", 404):
                return None
            if getattr(exc, "status_code", None) == 412:
                return None
            raise
        return self.get_support_case(case_id)

    def reply_to_support_case(self, case_id: str, response: str) -> dict | None:
        return self._replace_case(case_id, lambda case: {
            **case,
            "human_response": response,
            "demo_response": False,
            "status": "answered",
            "updated_at": utc_now(),
        })

    def demo_reply_to_user_support_case(self, case_id: str, user_id: str, response: str) -> dict | None:
        case = self.get_support_case(case_id, user_id)
        if case is None or case["status"] != "open":
            return None
        return self._replace_case(case_id, lambda stored: {
            **stored,
            "human_response": response,
            "demo_response": True,
            "status": "answered",
            "updated_at": utc_now(),
        })

    def close_support_case(self, case_id: str) -> dict | None:
        return self._replace_case(case_id, lambda case: {
            **case,
            "status": "closed",
            "updated_at": utc_now(),
        })
