"""Тесты безопасной проверки обновлений catalib через PyPI.

Сеть в тестах не используется: ``_fetch_latest_version`` подменяется
monkeypatch'ем, кеш изолируется через ``XDG_CACHE_HOME``.
"""

from __future__ import annotations

import json

import pytest

import catalib
from catalib.cli import app as cli_app


@pytest.fixture(autouse=True)
def _isolated_cache(tmp_path, monkeypatch):
    """Кеш проверки — во временном каталоге; opt-out по умолчанию снят."""
    monkeypatch.setenv("XDG_CACHE_HOME", str(tmp_path))
    monkeypatch.delenv("CATALIB_NO_UPDATE_CHECK", raising=False)


# --- Сравнение версий ---


@pytest.mark.parametrize(
    ("latest", "current", "newer"),
    [
        ("0.4.0", "0.3.0", True),
        ("0.3.1", "0.3.0", True),
        ("1.0.0", "0.3.0", True),
        ("0.3.0", "0.3.0", False),
        ("0.2.9", "0.3.0", False),
        ("0.3.0a1", "0.3.0", False),  # пред-релиз не новее (грубое сравнение)
        ("garbage", "0.3.0", False),
    ],
)
def test_is_newer(latest, current, newer) -> None:
    assert catalib._is_newer(latest, current) is newer


# --- Поведение check_for_updates ---


def test_opt_out_env_disables_check(monkeypatch) -> None:
    monkeypatch.setenv("CATALIB_NO_UPDATE_CHECK", "1")

    def _boom(*_a, **_k):
        raise AssertionError("сеть не должна вызываться при opt-out")

    monkeypatch.setattr(catalib, "_fetch_latest_version", _boom)
    assert catalib.check_for_updates() is None


def test_network_error_returns_none(monkeypatch) -> None:
    monkeypatch.setattr(catalib, "_fetch_latest_version", lambda timeout: None)
    assert catalib.check_for_updates() is None


def test_newer_version_detected_and_cached(monkeypatch) -> None:
    calls: list[int] = []

    def _fetch(timeout):
        calls.append(1)
        return "99.0.0"

    monkeypatch.setattr(catalib, "_fetch_latest_version", _fetch)
    assert catalib.check_for_updates() == "99.0.0"
    # Кеш записан и используется повторно (без новой загрузки).
    with open(catalib._cache_path(), encoding="utf-8") as handle:
        assert json.load(handle)["latest"] == "99.0.0"
    assert catalib.check_for_updates() == "99.0.0"
    assert calls == [1]  # сеть дёрнули один раз


def test_not_newer_returns_none(monkeypatch) -> None:
    monkeypatch.setattr(catalib, "_fetch_latest_version", lambda timeout: "0.0.1")
    assert catalib.check_for_updates() is None


def test_fresh_cache_skips_network(monkeypatch) -> None:
    import time

    catalib._write_cache(time.time(), "99.9.9")

    def _boom(timeout):
        raise AssertionError("свежий кеш — сеть не нужна")

    monkeypatch.setattr(catalib, "_fetch_latest_version", _boom)
    assert catalib.check_for_updates() == "99.9.9"


def test_corrupt_cache_is_safe(monkeypatch) -> None:
    import os

    path = catalib._cache_path()
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write("{ не json")
    monkeypatch.setattr(catalib, "_fetch_latest_version", lambda timeout: "0.1.0")
    # Битый кеш игнорируется, фолбэк на загрузку; 0.1.0 не новее.
    assert catalib.check_for_updates() is None


# --- CLI-уведомление ---


def test_cli_notify_prints_when_newer(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_app, "check_for_updates", lambda: "99.0.0")
    cli_app._notify_update()
    err = capsys.readouterr().err
    assert "99.0.0" in err
    assert "pip install -U catalib" in err


def test_cli_notify_silent_when_uptodate(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli_app, "check_for_updates", lambda: None)
    cli_app._notify_update()
    assert capsys.readouterr().err == ""


def test_cli_notify_never_raises(monkeypatch) -> None:
    def _boom():
        raise RuntimeError("сбой проверки")

    monkeypatch.setattr(cli_app, "check_for_updates", _boom)
    cli_app._notify_update()  # не должно бросать


def test_version_command_still_works(monkeypatch) -> None:
    from typer.testing import CliRunner

    # Проверка обновлений отключена — команда version не делает сеть.
    monkeypatch.setenv("CATALIB_NO_UPDATE_CHECK", "1")
    result = CliRunner().invoke(cli_app.app, ["version"])
    assert result.exit_code == 0
    assert catalib.__version__ in result.stdout
