"""Tests execute without network access or model credentials."""

import socket

import pytest


@pytest.fixture(autouse=True)
def no_network_or_provider_credentials(monkeypatch):
    def blocked(*args, **kwargs):
        raise AssertionError("Runtime network access is forbidden in this offline project")

    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    for key in ("OPENAI_API_KEY", "ANTHROPIC_API_KEY", "GEMINI_API_KEY",
                "GOOGLE_API_KEY", "AZURE_OPENAI_API_KEY", "MISTRAL_API_KEY"):
        monkeypatch.delenv(key, raising=False)
