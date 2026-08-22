"""Deterministic test-suite safety boundaries."""

from __future__ import annotations

import socket
from typing import NoReturn

import pytest


class NetworkAccessDenied(RuntimeError):
    """Raised when a blocking test attempts network access."""


@pytest.fixture(autouse=True)
def deny_network_by_default(
    request: pytest.FixtureRequest,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Deny outbound sockets; explicitly live tests are skipped by the native gate."""

    if request.node.get_closest_marker("network") is not None:
        pytest.skip("live network tests are excluded from the deterministic native gate")

    def blocked(*_args: object, **_kwargs: object) -> NoReturn:
        raise NetworkAccessDenied("network access is denied during deterministic tests")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket, "getaddrinfo", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)
    monkeypatch.setattr(socket.socket, "sendto", blocked)
