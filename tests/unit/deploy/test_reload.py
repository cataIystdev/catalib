"""Тесты высокоуровневого деплоя плагина."""

import pytest

from catalib.deploy import reload as reload_mod
from catalib.deploy.devserver import DevServerError
from catalib.deploy.reload import deploy_plugin


class FakeClient:
    """Поддельный клиент dev server, фиксирующий последовательность вызовов."""

    def __init__(self, *, pong: bool = True, enabled: bool = True):
        self._pong = pong
        self._enabled = enabled
        self.calls: list[str] = []

    def connect(self) -> None:
        self.calls.append("connect")

    def ping(self) -> bool:
        self.calls.append("ping")
        return self._pong

    def write_plugin(self, plugin_id: str, content: str) -> None:
        self.calls.append(f"write:{plugin_id}")

    def reload_plugin(self, plugin_id: str) -> None:
        self.calls.append(f"reload:{plugin_id}")

    def set_plugin_enabled(self, plugin_id: str, enabled: bool) -> None:
        self.calls.append(f"enable:{enabled}")

    def get_plugins(self) -> dict:
        self.calls.append("get_plugins")
        return {"demo": {"enabled": self._enabled}}

    def close(self) -> None:
        self.calls.append("close")


def test_deploy_sequence_with_enable() -> None:
    client = FakeClient()
    report = deploy_plugin("demo", "print(1)", enable=True, client=client)
    assert report.plugin_id == "demo"
    assert report.reloaded is True
    assert report.enabled is True
    assert client.calls == [
        "connect",
        "ping",
        "write:demo",
        "reload:demo",
        "enable:True",
        "reload:demo",
        "get_plugins",
    ]


def test_deploy_without_enable_skips_enable() -> None:
    client = FakeClient(enabled=False)
    report = deploy_plugin("demo", "x", enable=False, client=client)
    assert "enable:True" not in client.calls
    assert report.enabled is False


def test_ping_failure_raises() -> None:
    client = FakeClient(pong=False)
    with pytest.raises(DevServerError, match="не ответил на ping"):
        deploy_plugin("demo", "x", client=client)


def test_injected_client_not_closed_by_deploy() -> None:
    client = FakeClient()
    deploy_plugin("demo", "x", client=client)
    assert "close" not in client.calls


def _patch_forward(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Подменить adb-проброс и DevServerClient; вернуть журнал adb-вызовов."""
    log: list[str] = []
    monkeypatch.setattr(
        reload_mod, "forward_dev_server", lambda port, serial: log.append(f"fwd:{port}")
    )
    monkeypatch.setattr(
        reload_mod, "remove_forward", lambda port, serial: log.append(f"rm:{port}")
    )
    monkeypatch.setattr(reload_mod, "DevServerClient", lambda port=42690: FakeClient())
    return log


def test_no_adb_skips_forward(monkeypatch: pytest.MonkeyPatch) -> None:
    log = _patch_forward(monkeypatch)
    report = deploy_plugin("demo", "x", use_adb=False)
    assert log == []  # на устройстве adb forward не вызывается
    assert report.reloaded is True


def test_adb_path_forwards_and_removes(monkeypatch: pytest.MonkeyPatch) -> None:
    log = _patch_forward(monkeypatch)
    deploy_plugin("demo", "x", local_port=42699, use_adb=True)
    assert log == ["fwd:42699", "rm:42699"]


def test_auto_consults_should_use_adb(monkeypatch: pytest.MonkeyPatch) -> None:
    log = _patch_forward(monkeypatch)
    seen: list[bool | None] = []

    def fake_should(explicit: bool | None) -> bool:
        seen.append(explicit)
        return False  # имитируем устройство

    monkeypatch.setattr(reload_mod, "should_use_adb", fake_should)
    deploy_plugin("demo", "x")  # use_adb=None -> авто
    assert seen == [None]
    assert log == []  # авто-режим устройства: без forward
