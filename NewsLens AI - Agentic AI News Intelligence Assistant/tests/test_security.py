import pytest

from newslens.security.urls import UnsafeURLError, canonicalize_url, validate_public_url


def test_canonical_url_removes_tracking_and_fragment() -> None:
    assert (
        canonicalize_url("https://News.Example/path?utm_source=x&id=3#section")
        == "https://news.example/path?id=3"
    )


def test_canonical_url_encodes_markdown_link_delimiters() -> None:
    assert canonicalize_url("https://example.com/story).md?x=one two") == (
        "https://example.com/story%29.md?x=one+two"
    )


@pytest.mark.parametrize(
    "url", ["file:///etc/passwd", "http://user:pass@example.com/a", "//example.com/a"]
)
def test_non_http_or_credential_url_is_rejected(url: str) -> None:
    with pytest.raises(UnsafeURLError):
        canonicalize_url(url)


@pytest.mark.asyncio
async def test_localhost_ip_is_rejected() -> None:
    with pytest.raises(UnsafeURLError):
        await validate_public_url("http://127.0.0.1/admin")
