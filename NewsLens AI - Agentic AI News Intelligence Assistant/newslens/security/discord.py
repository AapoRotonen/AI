from __future__ import annotations

import re

from newslens.security.urls import canonicalize_url


def escape_discord_text(value: str) -> str:
    """Flatten and escape untrusted text before placing it in a Discord Markdown message."""
    text = " ".join(str(value).split())
    text = re.sub(r"@(everyone|here)\b", "@\u200b\\1", text, flags=re.IGNORECASE)
    for character in ("\\", "*", "_", "~", "`", "|", "[", "]", "<", ">", "#"):
        text = text.replace(character, "\\" + character)
    return text


def discord_link_url(value: str) -> str | None:
    """Return a canonical HTTP(S) URL safe to embed in a Discord Markdown link."""
    try:
        return canonicalize_url(value)
    except ValueError:
        return None
