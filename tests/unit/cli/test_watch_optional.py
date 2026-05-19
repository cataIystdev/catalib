"""Тесты работы без ``watchfiles`` (см. ADR-0005, ревизия в ADR-0011).

Требование: CLI ``catalib`` (``build``/``init``/``version``) работает без
``watchfiles`` — важно на телефоне (Termux/Pydroid), где Rust-бэкенд не
собрать. Сама команда ``watch`` при отсутствии пакета **не падает**, а
переключается на stdlib-поллинг.
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

import pytest
from typer.testing import CliRunner

from catalib import __version__, watching
from catalib.cli.app import app

#: Корень репозитория (для запуска изолированного интерпретатора с src в пути).
_REPO_ROOT = Path(__file__).resolve().parents[3]

runner = CliRunner()


def _block_watchfiles(monkeypatch: pytest.MonkeyPatch) -> None:
    """Сымитировать отсутствие пакета ``watchfiles``.

    ``None`` в ``sys.modules`` заставляет ``import watchfiles`` немедленно
    поднять ``ImportError``; monkeypatch восстанавливает состояние.
    """
    monkeypatch.setitem(sys.modules, "watchfiles", None)


def test_cli_imports_in_clean_interpreter_without_watchfiles() -> None:
    """В чистом интерпретаторе без ``watchfiles`` CLI импортируется и работает.

    Импорт ``watchfiles`` отложен в бэкенд слежения, поэтому импорт
    ``catalib.cli.app`` и команда ``version`` его не требуют. Проверяется
    в отдельном процессе: ``watchfiles`` заблокирован до импорта catalib.
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


def test_build_works_without_watchfiles(monkeypatch: pytest.MonkeyPatch, tmp_path: Path) -> None:
    _block_watchfiles(monkeypatch)
    proj = tmp_path / "proj"
    init_result = runner.invoke(app, ["init", "Demo", "--id", "demo_nowatch", "--dir", str(proj)])
    assert init_result.exit_code == 0, init_result.stdout
    build_result = runner.invoke(app, ["build", "--project", str(proj)])
    assert build_result.exit_code == 0, build_result.stdout
    assert (proj / "dist" / "demo_nowatch.py").is_file()


def test_backend_is_polling_without_watchfiles(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _block_watchfiles(monkeypatch)
    assert watching._has_watchfiles() is False
    assert watching.watching_backend() == "polling"


def test_watch_without_watchfiles_does_not_error_about_watchfiles(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Без ``watchfiles`` ``watch`` не жалуется на него (фолбэк на поллинг).

    Каталог без ``catalib.toml`` — команда доходит до загрузки манифеста
    (это уже за бывшим watchfiles-гейтом) и падает на манифесте, а не на
    ``watchfiles``.
    """
    _block_watchfiles(monkeypatch)
    result = runner.invoke(app, ["watch", "--project", str(tmp_path)])
    assert result.exit_code == 1
    # Прежний гейт-месседж исчез (проверяем конкретную фразу, а не голую
    # подстроку "watchfiles" — она встречается в пути tmp_path).
    assert "опциональная зависимость watchfiles" not in result.stderr
    assert "catalib[watch]" not in result.stderr
    assert "манифест" in result.stderr
