"""Тесты поставляемых SDK-стабов и команды ``catalib stubs``."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest
from typer.testing import CliRunner

from catalib.cli.app import app
from catalib.sdk_stubs import install_stubs, stub_files

runner = CliRunner()


def test_py_typed_marker_present() -> None:
    import catalib

    root = Path(catalib.__file__).parent
    assert (root / "py.typed").is_file()


def test_ships_expected_stub_modules() -> None:
    names = {p.name for p in stub_files()}
    for must in (
        "base_plugin.pyi",
        "client_utils.pyi",
        "android_utils.pyi",
        "file_utils.pyi",
        "hook_utils.pyi",
        "settings.pyi",
        "alert.pyi",
        "bulletin.pyi",
        "text_formatting.pyi",
        "classes.pyi",
    ):
        assert must in names, must


def test_all_stubs_are_valid_python() -> None:
    for path in stub_files():
        ast.parse(path.read_text(encoding="utf-8"), str(path))


def test_install_copies_tree_and_respects_force(tmp_path: Path) -> None:
    dest = tmp_path / "typings"
    written = install_stubs(dest)
    assert written
    assert (dest / "base_plugin.pyi").is_file()
    assert (dest / "ui" / "settings.pyi").is_file()
    assert (dest / "extera_utils" / "classes.pyi").is_file()

    with pytest.raises(FileExistsError, match="--force"):
        install_stubs(dest)

    again = install_stubs(dest, force=True)
    assert len(again) == len(written)


def test_stubs_command_success(tmp_path: Path) -> None:
    result = runner.invoke(app, ["stubs", "--dir", str(tmp_path / "typings")])
    assert result.exit_code == 0, result.output
    assert "Установлено стабов" in result.output
    assert (tmp_path / "typings" / "base_plugin.pyi").is_file()


def test_stubs_command_conflict_without_force(tmp_path: Path) -> None:
    d = str(tmp_path / "typings")
    assert runner.invoke(app, ["stubs", "--dir", d]).exit_code == 0
    conflict = runner.invoke(app, ["stubs", "--dir", d])
    assert conflict.exit_code == 1
    assert "Ошибка stubs" in conflict.stderr
    assert runner.invoke(app, ["stubs", "--dir", d, "--force"]).exit_code == 0
