"""Тесты префлайт-диагностики ``catalib doctor``."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from catalib.cli.app import app
from catalib.deploy.adb import AdbError
from catalib.deploy.devserver import DevServerError
from catalib.diagnostics import FAIL, OK, WARN, has_failures, run_diagnostics

runner = CliRunner()

_VALID_MANIFEST = """
[plugin]
id = "demo"
name = "Demo"
version = "1.0"
"""


class _FakeClient:
    """Подмена :class:`DevServerClient` для проверок без устройства."""

    def __init__(self, *, pong: bool = True, error: str | None = None) -> None:
        self._pong = pong
        self._error = error
        self.closed = False

    def connect(self) -> None:
        if self._error is not None:
            raise DevServerError(self._error)

    def ping(self) -> bool:
        return self._pong

    def close(self) -> None:
        self.closed = True


def _by_name(checks: list, name: str):
    return next(check for check in checks if check.name == name)


def test_python_check_passes_on_supported_interpreter(tmp_path: Path) -> None:
    checks = run_diagnostics(tmp_path)
    assert _by_name(checks, "Python").status == OK
    assert _by_name(checks, "catalib").status == OK


def test_adb_missing_is_warning_not_failure(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr("catalib.diagnostics.shutil.which", lambda _name: None)
    checks = run_diagnostics(tmp_path)
    assert _by_name(checks, "adb").status == WARN
    assert _by_name(checks, "Устройство").status == WARN
    assert _by_name(checks, "Dev server").status == WARN
    assert not has_failures(checks)


def test_no_devices_warns(tmp_path: Path) -> None:
    checks = run_diagnostics(tmp_path, device_lister=lambda: [])
    assert _by_name(checks, "adb").status == OK
    assert _by_name(checks, "Устройство").status == WARN


def test_adb_error_while_listing_is_warning(tmp_path: Path) -> None:
    def boom() -> list[str]:
        raise AdbError("adb сломался")

    checks = run_diagnostics(tmp_path, device_lister=boom)
    device = _by_name(checks, "Устройство")
    assert device.status == WARN
    assert "adb сломался" in device.detail


def test_device_and_devserver_ok(tmp_path: Path) -> None:
    checks = run_diagnostics(
        tmp_path,
        device_lister=lambda: ["emulator-5554"],
        devserver_client=_FakeClient(pong=True),
    )
    assert _by_name(checks, "Устройство").status == OK
    assert _by_name(checks, "Dev server").status == OK


def test_devserver_unreachable_warns(tmp_path: Path) -> None:
    checks = run_diagnostics(
        tmp_path,
        device_lister=lambda: ["dev1"],
        devserver_client=_FakeClient(error="нет соединения"),
    )
    assert _by_name(checks, "Dev server").status == WARN


def test_devserver_no_pong_warns(tmp_path: Path) -> None:
    checks = run_diagnostics(
        tmp_path,
        device_lister=lambda: ["dev1"],
        devserver_client=_FakeClient(pong=False),
    )
    assert _by_name(checks, "Dev server").status == WARN


def test_project_missing_is_warning(tmp_path: Path) -> None:
    checks = run_diagnostics(tmp_path)
    project = _by_name(checks, "Проект")
    assert project.status == WARN
    assert not has_failures(checks)


def test_project_invalid_is_failure(tmp_path: Path) -> None:
    (tmp_path / "catalib.toml").write_text('[plugin]\nid = "X"\n', encoding="utf-8")
    checks = run_diagnostics(tmp_path)
    assert _by_name(checks, "Проект").status == FAIL
    assert has_failures(checks)


def test_project_valid_is_ok(tmp_path: Path) -> None:
    (tmp_path / "catalib.toml").write_text(_VALID_MANIFEST, encoding="utf-8")
    checks = run_diagnostics(tmp_path)
    project = _by_name(checks, "Проект")
    assert project.status == OK
    assert "demo" in project.detail


def test_doctor_cli_success_without_device(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr("catalib.diagnostics.shutil.which", lambda _name: None)
    (tmp_path / "catalib.toml").write_text(_VALID_MANIFEST, encoding="utf-8")
    result = runner.invoke(app, ["doctor", "--project", str(tmp_path)])
    assert result.exit_code == 0, result.output
    assert "Окружение готово." in result.output


def test_doctor_cli_fails_on_invalid_manifest(tmp_path: Path) -> None:
    (tmp_path / "catalib.toml").write_text("not = valid = toml", encoding="utf-8")
    result = runner.invoke(app, ["doctor", "--project", str(tmp_path)])
    assert result.exit_code == 1
    assert "критические проблемы" in result.output


# --- Android-ветка (устройство: Termux/Pydroid) ---------------------------


def _force_android(monkeypatch: pytest.MonkeyPatch, flavor: str = "termux") -> None:
    import catalib.diagnostics as diag

    monkeypatch.setattr(diag, "is_android", lambda: True)
    monkeypatch.setattr(diag, "android_flavor", lambda: flavor)
    label = {"termux": "Termux (Android)", "pydroid": "Pydroid 3 (Android)"}[flavor]
    monkeypatch.setattr(diag, "describe_environment", lambda: label)


def test_android_skips_adb_and_device_checks(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _force_android(monkeypatch)
    checks = run_diagnostics(tmp_path, devserver_client=_FakeClient(pong=True))
    names = {c.name for c in checks}
    assert "adb" not in names
    assert "Устройство" not in names
    assert _by_name(checks, "Среда").status == OK
    assert "Termux" in _by_name(checks, "Среда").detail


def test_android_devserver_direct_ok(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _force_android(monkeypatch)
    checks = run_diagnostics(tmp_path, devserver_client=_FakeClient(pong=True))
    ds = _by_name(checks, "Dev server")
    assert ds.status == OK
    assert "напрямую" in ds.detail


def test_android_devserver_direct_unreachable_warns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _force_android(monkeypatch)
    checks = run_diagnostics(tmp_path, devserver_client=_FakeClient(error="нет соединения"))
    assert _by_name(checks, "Dev server").status == WARN
    assert not has_failures(checks)  # нет dev server — не критично


def test_android_pydroid_env_note(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    _force_android(monkeypatch, flavor="pydroid")
    checks = run_diagnostics(tmp_path, devserver_client=_FakeClient(pong=True))
    env = _by_name(checks, "Среда")
    assert env.status == OK
    assert "subprocess" in env.detail


def test_android_invalid_manifest_still_fails(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    _force_android(monkeypatch)
    (tmp_path / "catalib.toml").write_text('[plugin]\nid = "X"\n', encoding="utf-8")
    checks = run_diagnostics(tmp_path, devserver_client=_FakeClient(pong=True))
    assert _by_name(checks, "Проект").status == FAIL
    assert has_failures(checks)
