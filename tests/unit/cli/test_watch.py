"""Тесты итерации пересборки команды watch (без бесконечного цикла слежения)."""

from __future__ import annotations

from pathlib import Path

import pytest

from catalib.cli import watch_command as wc
from catalib.cli._pipeline import BuildFailure, BuildOutcome
from catalib.deploy.devserver import DevServerError


class _Bundle:
    text = "print(1)"
    module_count = 3


class _Manifest:
    id = "demo"


def _outcome(tmp_path: Path) -> BuildOutcome:
    return BuildOutcome(
        manifest=_Manifest(),
        bundle=_Bundle(),
        output_path=tmp_path / "dist" / "demo.py",
        plugin_path=tmp_path / "dist" / "demo.plugin",
    )


def test_rebuild_reports_build_failure(monkeypatch: pytest.MonkeyPatch, capsys) -> None:
    monkeypatch.setattr(
        wc, "build_bundle", lambda *a, **k: (_ for _ in ()).throw(BuildFailure("боль"))
    )
    wc._rebuild(Path("."), do_deploy=False, serial=None, port=42690)
    assert "Сборка не удалась" in capsys.readouterr().err


def test_rebuild_without_deploy(monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys) -> None:
    monkeypatch.setattr(wc, "build_bundle", lambda *a, **k: _outcome(tmp_path))
    called = []
    monkeypatch.setattr(wc, "deploy_plugin", lambda *a, **k: called.append(1))
    wc._rebuild(tmp_path, do_deploy=False, serial=None, port=42690)
    assert called == []
    assert "Собрано" in capsys.readouterr().out


def test_rebuild_with_deploy_success(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    monkeypatch.setattr(wc, "build_bundle", lambda *a, **k: _outcome(tmp_path))

    class Report:
        enabled = True

    monkeypatch.setattr(wc, "deploy_plugin", lambda *a, **k: Report())
    wc._rebuild(tmp_path, do_deploy=True, serial="S1", port=42690)
    assert "Задеплоено" in capsys.readouterr().out


def test_rebuild_deploy_failure_reported(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path, capsys
) -> None:
    monkeypatch.setattr(wc, "build_bundle", lambda *a, **k: _outcome(tmp_path))

    def boom(*a, **k):
        raise DevServerError("нет связи")

    monkeypatch.setattr(wc, "deploy_plugin", boom)
    wc._rebuild(tmp_path, do_deploy=True, serial=None, port=42690)
    assert "Деплой не удался" in capsys.readouterr().err
