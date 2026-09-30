"""Password, session-token, and support-case text helpers."""

from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets
import uuid


PASSWORD_HASH_ITERATIONS = 600_000


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PASSWORD_HASH_ITERATIONS)
    return "pbkdf2_sha256${}${}${}".format(
        PASSWORD_HASH_ITERATIONS,
        base64.urlsafe_b64encode(salt).decode("ascii"),
        base64.urlsafe_b64encode(digest).decode("ascii"),
    )


def verify_password(password: str, encoded: str) -> bool:
    try:
        algorithm, rounds_text, salt_text, digest_text = encoded.split("$", 3)
        if algorithm != "pbkdf2_sha256":
            return False
        rounds = int(rounds_text)
        if rounds < 100_000 or rounds > 2_000_000:
            return False
        salt = base64.urlsafe_b64decode(salt_text.encode("ascii"))
        expected = base64.urlsafe_b64decode(digest_text.encode("ascii"))
        candidate = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, rounds)
        return hmac.compare_digest(candidate, expected)
    except (ValueError, TypeError, UnicodeError):
        return False


def new_session_token() -> str:
    return secrets.token_urlsafe(32)


def token_digest(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def new_user_id() -> str:
    return str(uuid.uuid4())


def new_order_reference() -> str:
    return f"ORD-{secrets.token_hex(4).upper()}"


def new_case_id() -> str:
    return f"CASE-{secrets.token_hex(4).upper()}"


_EMAIL = re.compile(r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b", re.IGNORECASE)
_PHONE = re.compile(r"(?<!\w)(?:\+?\d[\d ()-]{6,}\d)(?!\w)")
_LONG_NUMBER = re.compile(r"(?<!\d)\d{13,19}(?!\d)")
_BEARER = re.compile(r"(?i)\b(?:bearer\s+)?[A-Za-z0-9_-]{32,}\b")
_ORDER_ID = re.compile(r"\bORD-[A-F0-9]{8}\b", re.IGNORECASE)


def sanitize_support_text(text: str) -> str:
    """Remove common contact, payment, and credential-like values before persistence."""
    value = text[:4000]
    order_ids = []

    def preserve_order_id(match):
        order_ids.append(match.group(0))
        return f"[order-ref-{len(order_ids) - 1}]"

    value = _ORDER_ID.sub(preserve_order_id, value)
    value = _EMAIL.sub("[email redacted]", value)
    value = _LONG_NUMBER.sub("[number redacted]", value)
    value = _PHONE.sub("[phone redacted]", value)
    value = _BEARER.sub("[token redacted]", value)
    for index, order_id in enumerate(order_ids):
        value = value.replace(f"[order-ref-{index}]", order_id)
    return " ".join(value.split())
