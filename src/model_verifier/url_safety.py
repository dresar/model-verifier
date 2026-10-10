import ipaddress
import socket
from urllib.parse import urlparse


def normalize_base_url(value: str) -> str:
    text = (value or "").strip().rstrip("/")
    if text and not text.startswith(("http://", "https://")):
        text = "https://" + text
    return text


def is_private_or_local_host(host: str) -> bool:
    normalized = host.strip().strip("[]").lower()
    if normalized in {"localhost", "ip6-localhost"} or normalized.endswith(".localhost"):
        return True
    try:
        ip = ipaddress.ip_address(normalized)
        if ip in ipaddress.ip_network("198.18.0.0/15"):
            return False
        return (
            ip.is_private
            or ip.is_loopback
            or ip.is_link_local
            or ip.is_multicast
            or ip.is_reserved
            or ip.is_unspecified
        )
    except ValueError:
        return False


def validate_public_base_url(base_url: str) -> str:
    normalized = normalize_base_url(base_url)
    parsed = urlparse(normalized)
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise ValueError("临时接入地址无效")
    if is_private_or_local_host(parsed.hostname):
        raise ValueError("临时接入地址不能指向本机或内网地址")
    try:
        addresses = socket.getaddrinfo(parsed.hostname, parsed.port, type=socket.SOCK_STREAM)
    except socket.gaierror:
        return normalized
    for address in addresses:
        ip = address[4][0]
        if is_private_or_local_host(ip):
            raise ValueError("临时接入地址不能指向本机或内网地址")
    return normalized

