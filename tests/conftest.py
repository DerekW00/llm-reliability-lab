"""Tests execute without network access or model credentials."""

import os
import socket

import pytest

# Datagram sends and name lookups need no connect(), so blocking connect alone
# would leave real egress paths open. Same set as the wheel and offline gates.
SOCKET_METHODS = ("connect", "connect_ex", "send", "sendall", "sendto")
SOCKET_FUNCTIONS = ("create_connection", "getaddrinfo", "gethostbyname",
                    "gethostbyname_ex", "gethostbyaddr", "getfqdn", "getnameinfo")
CREDENTIAL_MARKERS = ("API_KEY", "API_TOKEN", "ACCESS_TOKEN", "AUTH_TOKEN", "SECRET",
                      "CREDENTIAL", "_TOKEN", "OPENAI", "ANTHROPIC", "AZURE", "AWS_")


@pytest.fixture(autouse=True)
def no_network_or_provider_credentials(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Runtime network access is forbidden in this offline project")

    for name in SOCKET_METHODS:
        monkeypatch.setattr(socket.socket, name, blocked)
    for name in SOCKET_FUNCTIONS:
        monkeypatch.setattr(socket, name, blocked)
    for key in list(os.environ):
        if any(marker in key.upper() for marker in CREDENTIAL_MARKERS):
            monkeypatch.delenv(key, raising=False)
