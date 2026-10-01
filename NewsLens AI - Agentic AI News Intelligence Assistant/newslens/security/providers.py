from __future__ import annotations

import ipaddress
from urllib.parse import urlsplit


def validate_provider_base_url(value: str) -> str:
    """Require TLS for hosted model providers; allow cleartext only to loopback."""
    parts = urlsplit(value.strip())
    try:
        _ = parts.port
    except ValueError as exc:
        raise ValueError("The model provider URL has an invalid port") from exc
    host = (parts.hostname or "").lower().rstrip(".")
    if (
        not host
        or parts.username is not None
        or parts.password is not None
        or parts.query
        or parts.fragment
    ):
        raise ValueError("The model provider URL must not contain credentials, query, or fragment")
    if parts.scheme.lower() == "https":
        return value.strip().rstrip("/")
    if parts.scheme.lower() == "http":
        try:
            is_loopback = ipaddress.ip_address(host).is_loopback
        except ValueError:
            is_loopback = host == "localhost"
        if is_loopback:
            return value.strip().rstrip("/")
    raise ValueError("Model provider URLs must use HTTPS, except for localhost development")
