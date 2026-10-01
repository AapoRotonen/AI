from __future__ import annotations

import asyncio
import ipaddress
import socket
from urllib.parse import parse_qsl, quote, urlencode, urlsplit, urlunsplit


class UnsafeURLError(ValueError):
    """The URL is outside the public HTTP(S) boundary."""


def canonicalize_url(url: str) -> str:
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"} or not parts.hostname:
        raise UnsafeURLError("Only absolute HTTP(S) URLs are supported")
    if parts.username or parts.password:
        raise UnsafeURLError("URLs containing credentials are not allowed")
    host = parts.hostname.encode("idna").decode("ascii").lower().rstrip(".")
    port = parts.port
    host_for_netloc = f"[{host}]" if ":" in host else host
    netloc = (
        host_for_netloc
        if port in (None, 80 if parts.scheme.lower() == "http" else 443)
        else f"{host_for_netloc}:{port}"
    )
    query = [
        (key, value)
        for key, value in parse_qsl(parts.query)
        if not key.lower().startswith("utm_")
        and key.lower() not in {"fbclid", "gclid", "ref", "source"}
    ]
    query.sort(key=lambda item: item[0].lower())
    path = quote(parts.path or "/", safe="/%:@!$&'*+,;=-._~")
    return urlunsplit((parts.scheme.lower(), netloc, path, urlencode(query, doseq=True), ""))


def _validate_address(host: str) -> None:
    try:
        literal = ipaddress.ip_address(host)
        addresses = [literal]
    except ValueError:
        try:
            records = socket.getaddrinfo(host, None, type=socket.SOCK_STREAM)
        except OSError as exc:
            raise UnsafeURLError("The host could not be resolved") from exc
        addresses = [ipaddress.ip_address(record[4][0]) for record in records]
    if not addresses or any(not address.is_global for address in addresses):
        raise UnsafeURLError("Private, local, and reserved network addresses are not allowed")


async def validate_public_url(url: str) -> str:
    canonical = canonicalize_url(url)
    host = urlsplit(canonical).hostname
    if host is None:
        raise UnsafeURLError("URL has no host")
    await asyncio.to_thread(_validate_address, host)
    return canonical
