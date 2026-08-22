"""Blocking tests cannot silently consult ambient network state."""

import socket

import pytest


def test_ambient_socket_connections_are_denied() -> None:
    with (
        socket.socket() as connection,
        pytest.raises(RuntimeError, match="network access is denied"),
    ):
        connection.connect(("127.0.0.1", 9))
