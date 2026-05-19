"""Тесты детекта окружения ``catalib.platforms``.

Подменяется только файловый маркер ``_android_fs`` и `sys.platform` +
очищается окружение; функции-эвристики ``_looks_like_*`` тестируются
настоящие (через реальные переменные окружения).
"""

from __future__ import annotations

import pytest

from catalib import platforms


@pytest.fixture(autouse=True)
def _clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    for var in ("ANDROID_ROOT", "ANDROID_DATA", "TERMUX_VERSION", "PREFIX"):
        monkeypatch.delenv(var, raising=False)
    monkeypatch.setattr(platforms, "_android_fs", lambda: False)
    monkeypatch.setattr(platforms.sys, "platform", "linux")


def test_pc_is_not_android() -> None:
    assert platforms.is_android() is False
    assert platforms.android_flavor() == ""
    assert platforms.describe_environment() == "ПК (linux)"


def test_sys_platform_android(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platforms.sys, "platform", "android")
    assert platforms.is_android() is True


def test_android_env_vars(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setenv("ANDROID_ROOT", "/system")
    monkeypatch.setenv("ANDROID_DATA", "/data")
    assert platforms.is_android() is True


def test_android_fs_marker(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platforms, "_android_fs", lambda: True)
    assert platforms.is_android() is True


def test_partial_android_env_is_not_android(monkeypatch: pytest.MonkeyPatch) -> None:
    # Только одна из пары переменных — не считаем Android (меньше ложных).
    monkeypatch.setenv("ANDROID_ROOT", "/system")
    assert platforms.is_android() is False


def test_flavor_termux_via_real_heuristic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platforms.sys, "platform", "android")
    monkeypatch.setenv("TERMUX_VERSION", "0.118.0")
    assert platforms._looks_like_termux() is True
    assert platforms.android_flavor() == platforms.TERMUX
    assert platforms.describe_environment() == "Termux (Android)"


def test_flavor_pydroid_via_real_heuristic(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platforms.sys, "platform", "android")
    monkeypatch.setenv("HOME", "/data/data/ru.iiec.pydroid3/files/home")
    assert platforms._looks_like_termux() is False
    assert platforms._looks_like_pydroid() is True
    assert platforms.android_flavor() == platforms.PYDROID
    assert platforms.describe_environment() == "Pydroid 3 (Android)"


def test_flavor_generic_android(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platforms.sys, "platform", "android")
    assert platforms.android_flavor() == platforms.GENERIC_ANDROID
    assert platforms.describe_environment() == "Android"


def test_should_use_adb_explicit_overrides(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(platforms.sys, "platform", "android")
    assert platforms.should_use_adb(True) is True
    assert platforms.should_use_adb(False) is False


def test_should_use_adb_auto(monkeypatch: pytest.MonkeyPatch) -> None:
    assert platforms.should_use_adb() is True  # ПК -> adb
    monkeypatch.setattr(platforms.sys, "platform", "android")
    assert platforms.should_use_adb() is False  # устройство -> без adb
