"""Minimal structured operational logging; never accepts prompt or response text."""

from __future__ import annotations

import json
import logging


logger = logging.getLogger("koivu.events")


def log_event(event: str, **fields) -> None:
    record = {"event": event, **fields}
    logger.info(json.dumps(record, separators=(",", ":"), sort_keys=True))


def token_usage(response) -> tuple[int, int]:
    """Return provider-reported input/output token counts without exposing content."""
    usage = getattr(response, "usage_metadata", None) or {}
    if not usage:
        metadata = getattr(response, "response_metadata", None) or {}
        usage = metadata.get("token_usage") or metadata.get("usage") or {}
    input_tokens = usage.get("input_tokens", usage.get("prompt_tokens", 0)) or 0
    output_tokens = usage.get("output_tokens", usage.get("completion_tokens", 0)) or 0
    return int(input_tokens), int(output_tokens)
