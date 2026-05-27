from __future__ import annotations

from unittest.mock import patch

import pytest

from app.utils.url_utils import (
    UnsafeURLError,
    canonicalize_url,
    domain_of,
    resolve_url_safely,
)


class TestCanonicalize:
    def test_strips_tracking_params(self) -> None:
        result = canonicalize_url(
            "https://example.com/p?utm_source=ads&utm_medium=cpc&id=1&fbclid=abc"
        )
        assert result == "https://example.com/p?id=1"

    def test_lowercases_scheme_and_host_preserves_path_case(self) -> None:
        result = canonicalize_url("HTTPS://Example.com/Path/To/Item")
        assert result == "https://example.com/Path/To/Item"

    def test_drops_fragment(self) -> None:
        assert canonicalize_url("https://e.com/p#section") == "https://e.com/p"

    def test_sorts_query(self) -> None:
        result = canonicalize_url("https://e.com/p?b=2&a=1&c=3")
        assert result == "https://e.com/p?a=1&b=2&c=3"

    def test_amazon_drops_per_domain_extras(self) -> None:
        result = canonicalize_url(
            "https://amazon.com/dp/B000?psc=1&tag=affiliate-20&pf_rd_p=x&keepme=1"
        )
        assert result == "https://amazon.com/dp/B000?keepme=1"

    def test_normalizes_trailing_slash(self) -> None:
        assert canonicalize_url("https://e.com/p/") == "https://e.com/p"
        assert canonicalize_url("https://e.com/") == "https://e.com/"

    def test_rejects_non_https_scheme(self) -> None:
        with pytest.raises(UnsafeURLError):
            canonicalize_url("ftp://e.com/file")

    def test_rejects_too_long(self) -> None:
        with pytest.raises(UnsafeURLError):
            canonicalize_url("https://e.com/" + "x" * 4000)


class TestSSRFGuard:
    @pytest.mark.parametrize(
        "url",
        [
            "ftp://example.com",
            "javascript:alert(1)",
            "file:///etc/passwd",
            "gopher://example.com",
        ],
    )
    def test_rejects_non_http_schemes(self, url: str) -> None:
        with pytest.raises(UnsafeURLError):
            resolve_url_safely(url)

    @pytest.mark.parametrize(
        "ip",
        [
            "127.0.0.1",
            "10.0.0.1",
            "172.16.5.5",
            "192.168.1.1",
            "169.254.169.254",
            "100.64.0.1",
            "0.0.0.0",
            "::1",
            "fe80::1",
        ],
    )
    def test_rejects_private_or_link_local_ips(self, ip: str) -> None:
        with patch(
            "app.utils.url_utils.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", (ip, 0))],
        ):
            with pytest.raises(UnsafeURLError):
                resolve_url_safely("https://attacker.example/")

    def test_accepts_public_ip(self) -> None:
        with patch(
            "app.utils.url_utils.socket.getaddrinfo",
            return_value=[(2, 1, 6, "", ("93.184.216.34", 0))],
        ):
            url, ip = resolve_url_safely("https://example.com/p")
            assert url == "https://example.com/p"
            assert ip == "93.184.216.34"

    def test_rejects_dns_failure(self) -> None:
        import socket as _socket

        with patch(
            "app.utils.url_utils.socket.getaddrinfo",
            side_effect=_socket.gaierror("name not known"),
        ):
            with pytest.raises(UnsafeURLError):
                resolve_url_safely("https://nx.example/")


def test_domain_of() -> None:
    assert domain_of("https://www.amazon.com/dp/B000") == "www.amazon.com"
    assert domain_of("https://EXAMPLE.org/x") == "example.org"
