"""Тесты обёртки adb."""

import subprocess

import pytest

from catalib.deploy import adb


def test_list_devices_parses_only_ready(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adb.shutil, "which", lambda _: "/usr/bin/adb")
    out = "List of devices attached\nABC123\tdevice\nDEF456\toffline\n"
    monkeypatch.setattr(
        adb.subprocess,
        "run",
        lambda *a, **k: subprocess.CompletedProcess(a, 0, out, ""),
    )
    assert adb.list_devices() == ["ABC123"]


def test_forward_builds_expected_command(monkeypatch: pytest.MonkeyPatch) -> None:
    captured: list[list[str]] = []

    def fake_run(args, **kwargs):
        captured.append(args)
        return subprocess.CompletedProcess(args, 0, "", "")

    monkeypatch.setattr(adb.shutil, "which", lambda _: "/usr/bin/adb")
    monkeypatch.setattr(adb.subprocess, "run", fake_run)
    adb.forward_dev_server(42690, serial="ABC123")
    assert captured[0] == [
        "adb",
        "-s",
        "ABC123",
        "forward",
        "tcp:42690",
        "tcp:42690",
    ]


def test_missing_adb_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adb.shutil, "which", lambda _: None)
    with pytest.raises(adb.AdbError, match="adb не найден"):
        adb.list_devices()


def test_called_process_error_wrapped(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adb.shutil, "which", lambda _: "/usr/bin/adb")

    def fake_run(args, **kwargs):
        raise subprocess.CalledProcessError(1, args, "", "boom")

    monkeypatch.setattr(adb.subprocess, "run", fake_run)
    with pytest.raises(adb.AdbError, match="завершилась с ошибкой"):
        adb.forward_dev_server(42690)


def test_remove_forward_ignores_errors(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(adb.shutil, "which", lambda _: "/usr/bin/adb")

    def fake_run(args, **kwargs):
        raise subprocess.CalledProcessError(1, args, "", "no such forward")

    monkeypatch.setattr(adb.subprocess, "run", fake_run)
    adb.remove_forward(42690)  # не должно бросать
