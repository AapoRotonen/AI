import pytest

from newslens.security.providers import validate_provider_base_url


@pytest.mark.parametrize(
    ("url", "expected"),
    [
        ("https://api.example.com/v1/", "https://api.example.com/v1"),
        ("http://localhost:11434/v1", "http://localhost:11434/v1"),
        ("http://127.0.0.2:8000/v1", "http://127.0.0.2:8000/v1"),
    ],
)
def test_provider_base_url_allows_https_or_loopback_http(url: str, expected: str) -> None:
    assert validate_provider_base_url(url) == expected


@pytest.mark.parametrize(
    "url",
    [
        "http://api.example.com/v1",
        "file:///tmp/provider",
        "https://user:password@api.example.com/v1",
        "https://api.example.com/v1?token=secret",
        "https://api.example.com:invalid/v1",
    ],
)
def test_provider_base_url_rejects_cleartext_or_credential_urls(url: str) -> None:
    with pytest.raises(ValueError):
        validate_provider_base_url(url)
