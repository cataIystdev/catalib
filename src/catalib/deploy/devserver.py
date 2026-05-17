"""Клиент dev server exteraGram (TCP, JSON-протокол).

Протокол (см. ADR-0004): TCP-сокет, сообщения — JSON-объекты вида
``{"@": action, "#": request_id, ...}``; ответ содержит то же ``"#"``.
Поддерживаемые действия: ``ping``, ``get_plugins``, ``write_plugin``,
``reload_plugin``, ``set_plugin_enabled``, ``delete_plugin``.
"""

from __future__ import annotations

import json
import socket
import time
from collections.abc import Callable
from typing import Any, Protocol


class DevServerError(RuntimeError):
    """Ошибка соединения или обмена с dev server."""


class _SocketLike(Protocol):
    """Минимальный интерфейс сокета (для подмены в тестах)."""

    def sendall(self, data: bytes) -> None: ...

    def recv(self, bufsize: int) -> bytes: ...

    def close(self) -> None: ...


def _default_socket_factory(host: str, port: int, timeout: float) -> _SocketLike:
    """Открыть реальное TCP-соединение к dev server.

    Возможный ``OSError`` оборачивается в :class:`DevServerError` в
    :meth:`DevServerClient.connect`.
    """
    sock = socket.create_connection((host, port), timeout=timeout)
    sock.settimeout(timeout)
    return sock


class DevServerClient:
    """Синхронный клиент dev server с сопоставлением запрос/ответ по ``#``."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 42690,
        timeout: float = 30.0,
        socket_factory: Callable[[str, int, float], _SocketLike] | None = None,
    ) -> None:
        self._host = host
        self._port = port
        self._timeout = timeout
        self._factory = socket_factory or _default_socket_factory
        self._sock: _SocketLike | None = None
        self._request_id = 0

    def __enter__(self) -> DevServerClient:
        self.connect()
        return self

    def __exit__(self, *exc: object) -> None:
        self.close()

    def connect(self) -> None:
        """Установить соединение, если оно ещё не открыто."""
        if self._sock is None:
            try:
                self._sock = self._factory(self._host, self._port, self._timeout)
            except OSError as exc:
                raise DevServerError(
                    f"не удалось подключиться к dev server "
                    f"{self._host}:{self._port} — приложение запущено и включён "
                    f"режим разработчика? ({exc})"
                ) from exc

    def close(self) -> None:
        """Закрыть соединение (повторный вызов безопасен)."""
        if self._sock is not None:
            try:
                self._sock.close()
            finally:
                self._sock = None

    def _send(self, action: str, **args: Any) -> dict[str, Any]:
        """Отправить запрос и вернуть ответ с совпадающим ``#``."""
        if self._sock is None:
            raise DevServerError("соединение не открыто")
        self._request_id += 1
        request_id = self._request_id
        message = {"@": action, "#": request_id, **args}
        try:
            self._sock.sendall(json.dumps(message).encode("utf-8"))
        except OSError as exc:
            raise DevServerError(f"ошибка отправки запроса {action!r}: {exc}") from exc

        buffer = b""
        deadline = time.monotonic() + self._timeout
        decoder = json.JSONDecoder()
        while time.monotonic() < deadline:
            try:
                chunk = self._sock.recv(65536)
            except TimeoutError:
                continue
            except OSError as exc:
                raise DevServerError(f"ошибка чтения ответа: {exc}") from exc
            if not chunk:
                break
            buffer += chunk
            try:
                obj, _end = decoder.raw_decode(buffer.decode("utf-8", "replace").strip())
            except json.JSONDecodeError:
                continue
            if obj.get("#") == request_id:
                return obj
        raise DevServerError(f"таймаут ожидания ответа на {action!r}")

    def ping(self) -> bool:
        """Проверить доступность dev server."""
        return bool(self._send("ping").get("pong"))

    def get_plugins(self) -> dict[str, Any]:
        """Вернуть список установленных плагинов (без служебного ``#``)."""
        response = self._send("get_plugins")
        response.pop("#", None)
        return response

    def write_plugin(self, plugin_id: str, content: str) -> None:
        """Записать файл плагина на устройство."""
        self._send("write_plugin", plugin_id=plugin_id, content=content)

    def reload_plugin(self, plugin_id: str) -> None:
        """Перезагрузить плагин на устройстве."""
        self._send("reload_plugin", plugin_id=plugin_id)

    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> None:
        """Включить или выключить плагин."""
        self._send("set_plugin_enabled", plugin_id=plugin_id, enabled=enabled)

    def delete_plugin(self, plugin_id: str) -> None:
        """Удалить плагин с устройства."""
        self._send("delete_plugin", plugin_id=plugin_id)
