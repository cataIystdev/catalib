"""Тесты опциональности зависимости ``watchfiles`` (см. ADR-0005).

Требование: CLI ``catalib`` (команды ``build``/``init``/``version``) должен
работать без установленного ``watchfiles`` — это важно для установки на
телефоне (Termux/Pydroid), где Rust-бэкенд ``watchfiles`` собрать сложно.
Сама команда ``watch`` подключает пакет лениво и при его отсутствии даёт
понятную ошибку, а не голый ``ImportError`` на старте CLI.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
import typer
from typer.testing import CliRunner

from catalib import __version__
from catalib.cli import watch_command as wc
from catalib.cli.app import app

#: Корень репозитория (для запуска изолированного интерпретатора с src в пути).
_REPO_ROOT = Path(__file__).resolve().parents[3]

runner = CliRunner()


def _block_watchfiles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Сымитировать отсутствие пакета ``watchfiles``.

    ``None`` в ``sys.modules`` заставляет ``from watchfiles import watch``
    немедленно поднять ``ImportError``, не доходя до настоящего пакета.
    monkeypatch восстанавливает ``sys.modules`` после теста.
    """
    monkeypatch.setitem(sys.modules, "watchfiles", None)


def test_cli_imports_in_clean_interpreter_without_watchfiles() -> None:
    """В чистом интерпретаторе без ``watchfiles`` CLI импортируется и работает.

    Инвариант требования #1: импорт ``watchfiles`` отложен в тело команды
    ``watch``, поэтому импорт ``catalib.cli.app`` и команда ``version`` не
    должны его требовать. Проверяется в отдельном процессе (без влияния
    кеша импортов тестовой сессии): ``watchfiles`` заблокирован до импорта
    catalib; любой ранний импорт пакета упал бы с ``ImportError``.
    """
    script = (
        "import sys; sys.modules['watchfiles'] = None;"
        "from catalib.cli.app import app;"
        "from catalib import __version__;"
        "import typer.testing as t;"
        "r = t.CliRunner().invoke(app, ['version']);"
        "assert r.exit_code == 0, r.output;"
        "assert __version__ in r.stdout;"
        "print('OK')"
    )
    env = dict(os.environ, PYTHONPATH=str(_REPO_ROOT / "src"))
    proc = subprocess.run(
        [sys.executable, "-c", script],
        cwd=_REPO_ROOT,
        env=env,
        capture_output=True,
        text=True,
    )
    assert proc.returncode == 0, proc.stderr
    assert "OK" in proc.stdout


def test_version_works_without_watchfiles(monkeypatch: pytest.MonkeyPatch) -> None:
    _block_watchfiles(monkeypatch)
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_build_works_without_watchfiles(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    _block_watchfiles(monkeypatch)
    proj = tmp_path / "proj"
    init_result = runner.invoke(
        app, ["init", "Demo", "--id", "demo_nowatch", "--dir", str(proj)]
    )
    assert init_result.exit_code == 0, init_result.stdout
    build_result = runner.invoke(app, ["build", "--project", str(proj)])
    assert build_result.exit_code == 0, build_result.stdout
    assert (proj / "dist" / "demo_nowatch.py").is_file()


def test_watch_without_watchfiles_gives_clear_error(
    monkeypatch: pytest.MonkeyPatch, tmp_path
) -> None:
    _block_watchfiles(monkeypatch)
    result = runner.invoke(app, ["watch", "--project", str(tmp_path)])
    assert result.exit_code == 1
    assert "watchfiles" in result.stderr
    assert "catalib[watch]" in result.stderr


def test_load_watch_raises_typer_exit_when_missing(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_watchfiles(monkeypatch)
    with pytest.raises(typer.Exit) as exc_info:
        wc._load_watch()
    assert exc_info.value.exit_code == 1


def test_load_watch_returns_callable_when_available() -> None:
    """В dev-окружении ``watchfiles`` установлен — функция доступна."""
    watch = wc._load_watch()
    assert callable(watch)
