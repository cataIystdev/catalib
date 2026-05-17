"""Тесты клиента dev server (через поддельный сокет)."""

import json

import pytest

from catalib.deploy.devserver import DevServerClient, DevServerError


class FakeSocket:
    """Поддельный сокет: на каждый запрос отвечает JSON с тем же ``#``.

    :param responder: функция ``(action, message) -> dict`` для тела ответа.
    :param chunk: размер порции при ``recv`` (проверка склейки буфера).
    """

    def __init__(self, responder, chunk: int = 4):
        self._responder = responder
        self._chunk = chunk
        self._outbox = b""
        self.sent: list[dict] = []
        self.closed = False

    def sendall(self, data: bytes) -> None:
        message = json.loads(data.decode("utf-8"))
        self.sent.append(message)
        body = self._responder(message["@"], message)
        body["#"] = message["#"]
        self._outbox += json.dumps(body).encode("utf-8")

    def recv(self, bufsize: int) -> bytes:
        if not self._outbox:
            return b""
        piece, self._outbox = self._outbox[: self._chunk], self._outbox[self._chunk :]
        return piece

    def close(self) -> None:
        self.closed = True


def _client(responder) -> tuple[DevServerClient, FakeSocket]:
    holder: dict[str, FakeSocket] = {}

    def factory(host, port, timeout):
        holder["sock"] = FakeSocket(responder)
        return holder["sock"]

    client = DevServerClient(socket_factory=factory, timeout=2.0)
    client.connect()
    return client, holder["sock"]


def test_ping_true_when_pong() -> None:
    client, _ = _client(lambda action, msg: {"pong": True})
    assert client.ping() is True


def test_get_plugins_strips_request_id() -> None:
    client, _ = _client(lambda action, msg: {"demo": {"enabled": True}})
    plugins = client.get_plugins()
    assert plugins == {"demo": {"enabled": True}}
    assert "#" not in plugins


def test_write_reload_enable_delete_sequence() -> None:
    client, sock = _client(lambda action, msg: {"ok": True})
    client.write_plugin("demo", "print(1)")
    client.reload_plugin("demo")
    client.set_plugin_enabled("demo", True)
    client.delete_plugin("demo")
    actions = [m["@"] for m in sock.sent]
    assert actions == ["write_plugin", "reload_plugin", "set_plugin_enabled", "delete_plugin"]
    assert sock.sent[0]["content"] == "print(1)"
    assert sock.sent[2]["enabled"] is True


def test_request_ids_are_unique_and_matched() -> None:
    client, sock = _client(lambda action, msg: {"pong": True})
    client.ping()
    client.ping()
    assert [m["#"] for m in sock.sent] == [1, 2]


def test_buffer_reassembled_across_chunks() -> None:
    # chunk=4 в FakeSocket гарантирует многократный recv.
    client, _ = _client(lambda action, msg: {"plugins": "x" * 50})
    assert client._send("get_plugins")["plugins"] == "x" * 50


def test_timeout_when_no_response() -> None:
    class SilentSocket(FakeSocket):
        def sendall(self, data: bytes) -> None:
            self.sent.append(json.loads(data.decode()))

    def factory(host, port, timeout):
        return SilentSocket(lambda a, m: {})

    client = DevServerClient(socket_factory=factory, timeout=0.2)
    client.connect()
    with pytest.raises(DevServerError, match="таймаут"):
        client.ping()


def test_connection_failure_wrapped() -> None:
    def factory(host, port, timeout):
        raise OSError("connection refused")

    client = DevServerClient(socket_factory=factory)
    with pytest.raises(DevServerError, match="не удалось подключиться"):
        client.connect()
