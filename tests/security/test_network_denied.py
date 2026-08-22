from __future__ import annotations

import socket

import pytest


def test_outbound_network_is_denied_before_dns_or_connect() -> None:
    with pytest.raises(RuntimeError, match="network access is denied"):
        socket.create_connection(("example.invalid", 443), timeout=0.01)
