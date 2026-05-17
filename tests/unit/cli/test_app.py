"""Тесты CLI catalib (через typer CliRunner)."""

from pathlib import Path

from typer.testing import CliRunner

from catalib import __version__
from catalib.cli.app import app

runner = CliRunner()


def test_version_command() -> None:
    result = runner.invoke(app, ["version"])
    assert result.exit_code == 0
    assert __version__ in result.stdout


def test_init_then_build_roundtrip(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    init_result = runner.invoke(
        app, ["init", "Demo Plugin", "--id", "demo_plugin", "--dir", str(proj)]
    )
    assert init_result.exit_code == 0, init_result.stdout

    build_result = runner.invoke(app, ["build", "--project", str(proj)])
    assert build_result.exit_code == 0, build_result.stdout
    out_file = proj / "dist" / "demo_plugin.py"
    assert out_file.is_file()
    text = out_file.read_text(encoding="utf-8")
    assert "__id__ = " in text and "catalib_install(" in text


def test_build_check_does_not_write(tmp_path: Path) -> None:
    proj = tmp_path / "p"
    runner.invoke(app, ["init", "P", "--id", "checkp", "--dir", str(proj)])
    result = runner.invoke(app, ["build", "--project", str(proj), "--check"])
    assert result.exit_code == 0
    assert "Проверка пройдена" in result.stdout
    assert not (proj / "dist").exists()


def test_build_missing_manifest_fails(tmp_path: Path) -> None:
    result = runner.invoke(app, ["build", "--project", str(tmp_path)])
    assert result.exit_code == 1
    assert "Ошибка сборки" in result.stderr


def test_init_invalid_id_fails(tmp_path: Path) -> None:
    result = runner.invoke(app, ["init", "X", "--id", "Bad-Id", "--dir", str(tmp_path / "x")])
    assert result.exit_code == 1
    assert "Ошибка init" in result.stderr


def test_no_args_shows_help() -> None:
    result = runner.invoke(app, [])
    # no_args_is_help: click показывает справку и выходит с кодом 2.
    assert result.exit_code in (0, 2)
    combined = result.output + (result.stderr or "")
    assert "build" in combined and "watch" in combined
