import pytest

from newslens.security.access import is_discord_user_allowed


@pytest.mark.parametrize(
    ("user_id", "allowed_ids", "allow_public", "expected"),
    [
        (123, "", False, False),
        (123, "123, 456", False, True),
        (789, "123, 456", False, False),
        (123, "not-an-id", False, False),
        (123, "0,123", False, False),
        (123, "", True, True),
    ],
)
def test_discord_command_authorization(user_id, allowed_ids, allow_public, expected) -> None:
    assert is_discord_user_allowed(user_id, allowed_ids, allow_public) is expected
