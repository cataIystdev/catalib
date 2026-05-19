"""Тесты фильтрации логов и команды ``catalib logs``."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from catalib.cli.app import app
from catalib.deploy.adb import AdbError
from catalib.devicelogs import filter_log

runner = CliRunner()

_MANIFEST = '[plugin]\nid = "demo"\nname = "Demo"\nversion = "1.0"\n'
_LOG = "l1 noise\n[demo] hello\nl3 noise\n[DEMO] world\nl5 noise"


def test_filter_keeps_case_insensitive_matches() -> None:
    out = filter_log(_LOG, "demo")
    assert out == "[demo] hello\n[DEMO] world"


def test_filter_empty_needle_returns_all() -> None:
    assert filter_log(_LOG, "") == _LOG


def test_filter_no_match_shows_tail() -> None:
    out = filter_log("a\nb\nc\nd", "zzz", tail=2)
    assert 'Строк с "zzz" не найдено' in out
    assert out.endswith("c\nd")


def test_logs_cli_filters_by_manifest_id(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "catalib.toml").write_text(_MANIFEST, encoding="utf-8")
    monkeypatch.setattr(
        "catalib.cli.logs_command.logcat",
        lambda lines, serial, clear=False, use_adb=None: _LOG,
    )
    result = runner.invoke(app, ["logs", "--project", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "[demo] hello" in result.output
    assert "l1 noise" not in result.output


def test_logs_cli_all_disables_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "catalib.toml").write_text(_MANIFEST, encoding="utf-8")
    monkeypatch.setattr(
        "catalib.cli.logs_command.logcat",
        lambda lines, serial, clear=False, use_adb=None: _LOG,
    )
    result = runner.invoke(app, ["logs", "--project", str(tmp_path), "--all"])
    assert result.exit_code == 0
    assert "l1 noise" in result.output


def test_logs_cli_custom_filter(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(
        "catalib.cli.logs_command.logcat",
        lambda lines, serial, clear=False, use_adb=None: _LOG,
    )
    result = runner.invoke(app, ["logs", "--project", str(tmp_path), "--filter", "l3"])
    assert result.exit_code == 0
    assert "l3 noise" in result.output
    assert "[demo] hello" not in result.output


def test_logs_cli_no_manifest_warns_and_shows_all(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(
        "catalib.cli.logs_command.logcat",
        lambda lines, serial, clear=False, use_adb=None: _LOG,
    )
    result = runner.invoke(app, ["logs", "--project", str(tmp_path)])
    assert result.exit_code == 0
    assert "Нет валидного catalib.toml" in result.output
    assert "l1 noise" in result.output


def test_logs_cli_adb_error_exits_1(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    def boom(lines: int, serial: object, clear: bool = False, use_adb: object = None) -> str:
        raise AdbError("устройство не найдено")

    monkeypatch.setattr("catalib.cli.logs_command.logcat", boom)
    result = runner.invoke(app, ["logs", "--project", str(tmp_path)])
    assert result.exit_code == 1
    assert "Ошибка logs" in result.stderr


# --- Платформенный выбор logcat и подсказка на устройстве (T-304) ----------


def _capture_argv(monkeypatch: pytest.MonkeyPatch) -> list[list[str]]:
    """Подменить subprocess.run в adb.py и собрать переданные argv."""
    import types

    import catalib.deploy.adb as adbmod

    calls: list[list[str]] = []

    def fake_run(args, **kwargs):
        calls.append(list(args))
        return types.SimpleNamespace(stdout="[demo] hi\n", returncode=0)

    monkeypatch.setattr(adbmod.subprocess, "run", fake_run)
    monkeypatch.setattr(adbmod.shutil, "which", lambda _name: "/usr/bin/adb")
    return calls


def test_logcat_direct_on_device(monkeypatch: pytest.MonkeyPatch) -> None:
    import catalib.deploy.adb as adbmod

    calls = _capture_argv(monkeypatch)
    monkeypatch.setattr(adbmod, "should_use_adb", lambda explicit: False)
    out = adbmod.logcat(50)
    assert out == "[demo] hi"
    assert calls == [["logcat", "-d", "-t", "50"]]  # без adb-префикса


def test_logcat_via_adb_on_pc(monkeypatch: pytest.MonkeyPatch) -> None:
    import catalib.deploy.adb as adbmod

    calls = _capture_argv(monkeypatch)
    monkeypatch.setattr(adbmod, "should_use_adb", lambda explicit: True)
    adbmod.logcat(20, "SER1")
    assert calls == [["adb", "-s", "SER1", "logcat", "-d", "-t", "20"]]


def test_logs_cli_android_failure_shows_privilege_hint(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def boom(lines: int, serial: object, clear: bool = False, use_adb: object = None) -> str:
        raise AdbError("logcat недоступен: Permission denied")

    monkeypatch.setattr("catalib.cli.logs_command.logcat", boom)
    monkeypatch.setattr("catalib.cli.logs_command.is_android", lambda: True)
    result = runner.invoke(app, ["logs", "--project", str(tmp_path)])
    assert result.exit_code == 1
    assert "READ_LOGS" in result.stderr
    assert "Shizuku" in result.stderr
