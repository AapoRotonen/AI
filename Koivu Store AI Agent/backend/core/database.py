"""Small SQLite persistence layer for demo accounts, orders, and support cases."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterator


def utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


class Database:
    def __init__(self, path: str | Path):
        self.path = Path(path)

    @contextmanager
    def connection(self) -> Iterator[sqlite3.Connection]:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        try:
            yield connection
            connection.commit()
        except Exception:
            connection.rollback()
            raise
        finally:
            connection.close()

    def initialize(self) -> None:
        with self.connection() as db:
            db.executescript(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id TEXT PRIMARY KEY,
                    email TEXT NOT NULL UNIQUE COLLATE NOCASE,
                    password_hash TEXT NOT NULL,
                    created_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS sessions (
                    token_hash TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    expires_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS sessions_user_id_idx ON sessions(user_id);
                CREATE TABLE IF NOT EXISTS orders (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    status TEXT NOT NULL,
                    tracking_code TEXT,
                    created_at TEXT NOT NULL,
                    items_json TEXT NOT NULL DEFAULT '[]',
                    total_cents INTEGER NOT NULL DEFAULT 0
                );
                CREATE INDEX IF NOT EXISTS orders_user_id_idx ON orders(user_id);
                CREATE TABLE IF NOT EXISTS support_cases (
                    id TEXT PRIMARY KEY,
                    user_id TEXT NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                    question TEXT NOT NULL,
                    reason TEXT NOT NULL,
                    safe_context TEXT NOT NULL,
                    status TEXT NOT NULL,
                    human_response TEXT,
                    demo_response INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS support_cases_status_idx ON support_cases(status);
                CREATE INDEX IF NOT EXISTS support_cases_user_id_idx ON support_cases(user_id);
                """
            )
            order_columns = {row["name"] for row in db.execute("PRAGMA table_info(orders)").fetchall()}
            if "items_json" not in order_columns:
                db.execute("ALTER TABLE orders ADD COLUMN items_json TEXT NOT NULL DEFAULT '[]'")
            if "total_cents" not in order_columns:
                db.execute("ALTER TABLE orders ADD COLUMN total_cents INTEGER NOT NULL DEFAULT 0")
            case_columns = {row["name"] for row in db.execute("PRAGMA table_info(support_cases)").fetchall()}
            if "demo_response" not in case_columns:
                db.execute("ALTER TABLE support_cases ADD COLUMN demo_response INTEGER NOT NULL DEFAULT 0")

    def create_user(self, user_id: str, email: str, password_hash: str) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT INTO users(id, email, password_hash, created_at) VALUES (?, ?, ?, ?)",
                (user_id, email, password_hash, utc_now()),
            )

    def get_user_by_email(self, email: str) -> dict | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT id, email, password_hash FROM users WHERE email = ? COLLATE NOCASE",
                (email,),
            ).fetchone()
        return dict(row) if row else None

    def get_public_user(self, user_id: str) -> dict | None:
        with self.connection() as db:
            row = db.execute("SELECT id, email FROM users WHERE id = ?", (user_id,)).fetchone()
        return dict(row) if row else None

    def create_session(self, token_hash: str, user_id: str, expires_at: str) -> None:
        with self.connection() as db:
            db.execute(
                "INSERT INTO sessions(token_hash, user_id, expires_at) VALUES (?, ?, ?)",
                (token_hash, user_id, expires_at),
            )

    def get_session_user(self, token_hash: str) -> dict | None:
        now = utc_now()
        with self.connection() as db:
            row = db.execute(
                "SELECT users.id, users.email FROM sessions "
                "JOIN users ON users.id = sessions.user_id "
                "WHERE sessions.token_hash = ? AND sessions.expires_at > ?",
                (token_hash, now),
            ).fetchone()
            if row is None:
                db.execute("DELETE FROM sessions WHERE token_hash = ? OR expires_at <= ?", (token_hash, now))
        return dict(row) if row else None

    def delete_session(self, token_hash: str) -> None:
        with self.connection() as db:
            db.execute("DELETE FROM sessions WHERE token_hash = ?", (token_hash,))

    def create_demo_order(self, order_id: str, user_id: str) -> dict:
        created_at = utc_now()
        with self.connection() as db:
            db.execute(
                "INSERT INTO orders(id, user_id, status, tracking_code, created_at) "
                "VALUES (?, ?, ?, ?, ?)",
                (order_id, user_id, "processing", None, created_at),
            )
        return self.get_owned_order(order_id, user_id) or {}

    def create_order(self, order_id: str, user_id: str, items: list[dict], total_cents: int) -> dict:
        created_at = utc_now()
        with self.connection() as db:
            db.execute(
                "INSERT INTO orders(id, user_id, status, tracking_code, created_at, items_json, total_cents) "
                "VALUES (?, ?, ?, ?, ?, ?, ?)",
                (order_id, user_id, "processing", None, created_at, json.dumps(items, ensure_ascii=False), total_cents),
            )
        return self.get_owned_order(order_id, user_id) or {}

    def delete_owned_order(self, order_id: str, user_id: str) -> bool:
        """Delete one local demo order only when it belongs to the signed-in user."""
        with self.connection() as db:
            cursor = db.execute("DELETE FROM orders WHERE id = ? AND user_id = ?", (order_id, user_id))
        return cursor.rowcount == 1

    def get_owned_order(self, order_id: str, user_id: str) -> dict | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM orders WHERE id = ? AND user_id = ?",
                (order_id, user_id),
            ).fetchone()
        return self._order_dict(row) if row else None

    def get_latest_owned_order(self, user_id: str) -> dict | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM orders "
                "WHERE user_id = ? ORDER BY created_at DESC, rowid DESC LIMIT 1",
                (user_id,),
            ).fetchone()
        return self._order_dict(row) if row else None

    def list_owned_orders(self, user_id: str) -> list[dict]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT * FROM orders "
                "WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [self._order_dict(row) for row in rows]

    @staticmethod
    def _order_dict(row: sqlite3.Row) -> dict:
        result = dict(row)
        raw_items = result.pop("items_json", "[]")
        try:
            result["items"] = json.loads(raw_items or "[]")
        except (TypeError, json.JSONDecodeError):
            result["items"] = []
        result["total_cents"] = int(result.get("total_cents") or 0)
        return result

    def find_open_support_case(self, user_id: str, question: str, reason: str) -> dict | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM support_cases "
                "WHERE user_id = ? AND question = ? AND reason = ? AND status = 'open' "
                "ORDER BY created_at DESC LIMIT 1",
                (user_id, question, reason),
            ).fetchone()
        return self._case_dict(row) if row else None

    def find_latest_open_support_case(self, user_id: str, reason: str) -> dict | None:
        with self.connection() as db:
            row = db.execute(
                "SELECT * FROM support_cases WHERE user_id = ? AND reason = ? AND status = 'open' "
                "ORDER BY created_at DESC LIMIT 1",
                (user_id, reason),
            ).fetchone()
        return self._case_dict(row) if row else None

    def create_support_case(
        self,
        case_id: str,
        user_id: str,
        question: str,
        reason: str,
        safe_context: dict,
    ) -> dict:
        now = utc_now()
        with self.connection() as db:
            db.execute(
                "INSERT INTO support_cases "
                "(id, user_id, question, reason, safe_context, status, created_at, updated_at) "
                "VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                (case_id, user_id, question, reason, json.dumps(safe_context), "open", now, now),
            )
        return self.get_support_case(case_id)

    def get_support_case(self, case_id: str, user_id: str | None = None) -> dict | None:
        query = "SELECT * FROM support_cases WHERE id = ?"
        params: tuple = (case_id,)
        if user_id is not None:
            query += " AND user_id = ?"
            params += (user_id,)
        with self.connection() as db:
            row = db.execute(query, params).fetchone()
        return self._case_dict(row) if row else None

    def list_support_cases(self, status: str | None = None) -> list[dict]:
        query = "SELECT * FROM support_cases"
        params: tuple = ()
        if status:
            query += " WHERE status = ?"
            params = (status,)
        query += " ORDER BY created_at ASC"
        with self.connection() as db:
            rows = db.execute(query, params).fetchall()
        return [self._case_dict(row) for row in rows]

    def list_user_support_cases(self, user_id: str) -> list[dict]:
        with self.connection() as db:
            rows = db.execute(
                "SELECT * FROM support_cases WHERE user_id = ? ORDER BY created_at DESC",
                (user_id,),
            ).fetchall()
        return [self._case_dict(row) for row in rows]

    def delete_user_support_cases(self, user_id: str) -> int:
        """Reset only the authenticated user's demo support history."""
        with self.connection() as db:
            cursor = db.execute("DELETE FROM support_cases WHERE user_id = ?", (user_id,))
        return cursor.rowcount

    def reply_to_support_case(self, case_id: str, response: str) -> dict | None:
        with self.connection() as db:
            cursor = db.execute(
                "UPDATE support_cases SET human_response = ?, demo_response = 0, status = 'answered', updated_at = ? "
                "WHERE id = ? AND status != 'closed'",
                (response, utc_now(), case_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_support_case(case_id)

    def demo_reply_to_user_support_case(self, case_id: str, user_id: str, response: str) -> dict | None:
        """Store a clearly marked canned demo reply on the owner's open case."""
        with self.connection() as db:
            cursor = db.execute(
                "UPDATE support_cases SET human_response = ?, demo_response = 1, status = 'answered', updated_at = ? "
                "WHERE id = ? AND user_id = ? AND status = 'open'",
                (response, utc_now(), case_id, user_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_support_case(case_id, user_id)

    def close_support_case(self, case_id: str) -> dict | None:
        with self.connection() as db:
            cursor = db.execute(
                "UPDATE support_cases SET status = 'closed', updated_at = ? WHERE id = ? AND status != 'closed'",
                (utc_now(), case_id),
            )
            if cursor.rowcount == 0:
                return None
        return self.get_support_case(case_id)

    @staticmethod
    def _case_dict(row: sqlite3.Row) -> dict:
        result = dict(row)
        result["safe_context"] = json.loads(result["safe_context"])
        result["demo_response"] = bool(result.get("demo_response", 0))
        return result
