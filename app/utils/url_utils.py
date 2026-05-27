"""URL canonicalization and SSRF-safe resolution.

Two surfaces:

* ``canonicalize_url`` produces the value stored in ``products.source_url``.
  Two pastes of the same product with different tracking tails must
  canonicalize to identical strings.
* ``resolve_url_safely`` is the mandatory pre-fetch gate. It validates
  the scheme, resolves DNS, rejects any non-publicly-routable IP, and
  pins the resolved IP to defeat DNS rebind on the subsequent fetch.
"""

from __future__ import annotations

import ipaddress
import socket
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

from app.config.limits import URL_MAX_LENGTH

_TRACKING_PARAMS = frozenset(
    {
        "utm_source",
        "utm_medium",
        "utm_campaign",
        "utm_term",
        "utm_content",
        "fbclid",
        "gclid",
        "ref",
        "_ga",
        "igshid",
        "mc_eid",
        "mc_cid",
    }
)

_PER_DOMAIN_DROP = {
    "amazon": frozenset(
        {"psc", "pf_rd_p", "pf_rd_r", "pf_rd_s", "pf_rd_t", "pf_rd_i", "tag", "linkCode", "creative"}
    ),
    "ebay": frozenset({"_trkparms", "_trksid", "hash", "epid"}),
}

_PRIVATE_NETWORKS: tuple[ipaddress.IPv4Network | ipaddress.IPv6Network, ...] = (
    ipaddress.ip_network("127.0.0.0/8"),
    ipaddress.ip_network("0.0.0.0/8"),
    ipaddress.ip_network("169.254.0.0/16"),
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
    ipaddress.ip_network("100.64.0.0/10"),
    ipaddress.ip_network("::1/128"),
    ipaddress.ip_network("fc00::/7"),
    ipaddress.ip_network("fe80::/10"),
    ipaddress.ip_network("::ffff:0:0/96"),
)


class UnsafeURLError(ValueError):
    pass


def canonicalize_url(url: str) -> str:
    if not url or len(url) > URL_MAX_LENGTH:
        raise UnsafeURLError("url length out of range")
    parts = urlsplit(url.strip())
    if parts.scheme.lower() not in {"http", "https"}:
        raise UnsafeURLError(f"unsupported scheme: {parts.scheme}")
    if not parts.hostname:
        raise UnsafeURLError("missing host")

    scheme = parts.scheme.lower()
    host = parts.hostname.lower()
    netloc = host if parts.port is None else f"{host}:{parts.port}"

    path = parts.path or "/"
    if path != "/" and path.endswith("/"):
        path = path.rstrip("/") or "/"

    drop = set(_TRACKING_PARAMS)
    for token, extras in _PER_DOMAIN_DROP.items():
        if token in host:
            drop |= extras

    pairs = [
        (k, v)
        for k, v in parse_qsl(parts.query, keep_blank_values=True)
        if k.lower() not in drop and not k.lower().startswith("utm_")
    ]
    pairs.sort()
    query = urlencode(pairs, doseq=True)

    return urlunsplit((scheme, netloc, path, query, ""))


def domain_of(url: str) -> str:
    host = urlsplit(url).hostname or ""
    return host.lower()


def resolve_url_safely(url: str) -> tuple[str, str]:
    """Validate + DNS-resolve. Returns ``(url, pinned_ip)``.

    Caller must use ``pinned_ip`` for the actual connection (e.g. via
    ``socket.create_connection((pinned_ip, port))`` or by setting the
    Host header explicitly).
    """
    if len(url) > URL_MAX_LENGTH:
        raise UnsafeURLError("url too long")
    parts = urlsplit(url)
    if parts.scheme.lower() not in {"http", "https"}:
        raise UnsafeURLError(f"unsupported scheme: {parts.scheme}")
    if not parts.hostname:
        raise UnsafeURLError("missing host")

    try:
        infos = socket.getaddrinfo(parts.hostname, None)
    except socket.gaierror as exc:
        raise UnsafeURLError(f"dns resolution failed: {exc}") from exc

    pinned: str | None = None
    for _family, _type, _proto, _canon, sockaddr in infos:
        ip_str = sockaddr[0]
        try:
            ip = ipaddress.ip_address(ip_str)
        except ValueError as exc:
            raise UnsafeURLError(f"unparseable ip: {ip_str}") from exc

        for net in _PRIVATE_NETWORKS:
            if ip.version == net.version and ip in net:
                raise UnsafeURLError(f"non-public ip: {ip_str}")

        if pinned is None:
            pinned = ip_str

    if pinned is None:
        raise UnsafeURLError("no ip resolved")
    return url, pinned
