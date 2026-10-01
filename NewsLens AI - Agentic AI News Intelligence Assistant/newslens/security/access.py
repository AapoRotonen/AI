def is_discord_user_allowed(
    user_id: int, allowed_user_ids: str, allow_public_commands: bool = False
) -> bool:
    """Authorize commands by explicit user ID, denying by default."""
    if allow_public_commands:
        return True
    if not allowed_user_ids.strip():
        return False
    try:
        allowed = {int(value.strip()) for value in allowed_user_ids.split(",") if value.strip()}
    except ValueError:
        return False
    return bool(allowed) and all(value > 0 for value in allowed) and user_id in allowed
