import socket

import pytest

from model_verifier.url_safety import is_private_or_local_host, validate_public_base_url


def test_private_and_local_hosts_are_rejected():
    assert is_private_or_local_host("127.0.0.1") is True
    assert is_private_or_local_host("localhost") is True
    assert is_private_or_local_host("192.168.1.2") is True
    assert is_private_or_local_host("::1") is True


def test_benchmark_proxy_range_is_allowed():
    assert is_private_or_local_host("198.18.0.57") is False
    assert is_private_or_local_host("198.19.255.254") is False


def test_validate_public_base_url_normalizes_plain_domain(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("93.184.216.34", 443))])

    assert validate_public_base_url("gateway.example.test/") == "https://gateway.example.test"


def test_validate_public_base_url_rejects_localhost():
    with pytest.raises(ValueError, match="不能指向本机或内网地址"):
        validate_public_base_url("http://127.0.0.1:8000")


def test_validate_public_base_url_rejects_dns_private_resolution(monkeypatch):
    monkeypatch.setattr(socket, "getaddrinfo", lambda *args, **kwargs: [(socket.AF_INET, socket.SOCK_STREAM, 6, "", ("10.0.0.7", 443))])

    with pytest.raises(ValueError, match="不能指向本机或内网地址"):
        validate_public_base_url("https://gateway.example.test")
