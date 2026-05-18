"""Тесты шаблонов ``catalib init --template``: структура и сборка."""

from __future__ import annotations

from pathlib import Path

import pytest
from typer.testing import CliRunner

from catalib.cli._pipeline import build_bundle
from catalib.cli.app import app
from catalib.scaffold import ScaffoldError, create_project
from catalib.scaffold.templates import DEFAULT_TEMPLATE, TEMPLATES

runner = CliRunner()


@pytest.mark.parametrize("template", sorted(TEMPLATES))
def test_every_template_builds(tmp_path: Path, template: str) -> None:
    """Каждый шаблон собирается ``build_bundle`` без правок."""
    project = tmp_path / template
    create_project(project, "demo", "Demo", "catalyst", template)
    outcome = build_bundle(project, write=True)
    assert outcome.output_path.is_file()
    assert outcome.output_path.name == "demo.py"


def test_default_template_is_hook() -> None:
    assert DEFAULT_TEMPLATE == "hook"
    assert "hook" in TEMPLATES


def test_hook_template_structure_unchanged(tmp_path: Path) -> None:
    """Шаблон по умолчанию даёт прежний набор файлов (обратная совместимость)."""
    created = create_project(tmp_path / "p", "demo", "Demo")
    names = {p.relative_to(tmp_path / "p").as_posix() for p in created}
    assert names == {
        "catalib.toml",
        "pyproject.toml",
        ".gitignore",
        "README.md",
        "conftest.py",
        "src/__init__.py",
        "src/greeting.py",
        "src/plugin.py",
        "tests/test_plugin.py",
    }


def test_menu_template_has_menu_item(tmp_path: Path) -> None:
    create_project(tmp_path / "m", "demo", "Demo", template="menu")
    plugin_src = (tmp_path / "m" / "src" / "plugin.py").read_text(encoding="utf-8")
    assert "@menu_item(" in plugin_src
    assert "class DemoPlugin(CatalibPlugin)" in plugin_src
    assert (tmp_path / "m" / "src" / "actions.py").is_file()


def test_settings_template_has_settings(tmp_path: Path) -> None:
    create_project(tmp_path / "s", "demo", "Demo", template="settings")
    plugin_src = (tmp_path / "s" / "src" / "plugin.py").read_text(encoding="utf-8")
    assert "settings.switch(" in plugin_src
    assert "settings.text_input(" in plugin_src
    assert (tmp_path / "s" / "src" / "format.py").is_file()


def test_minimal_template_has_no_hook(tmp_path: Path) -> None:
    create_project(tmp_path / "min", "demo", "Demo", template="minimal")
    plugin_src = (tmp_path / "min" / "src" / "plugin.py").read_text(encoding="utf-8")
    assert "@hook" not in plugin_src
    assert "def on_load(self)" in plugin_src


def test_unknown_template_rejected(tmp_path: Path) -> None:
    with pytest.raises(ScaffoldError, match="неизвестный шаблон"):
        create_project(tmp_path / "x", "demo", "Demo", template="nope")


def test_cli_template_option(tmp_path: Path) -> None:
    proj = tmp_path / "proj"
    result = runner.invoke(
        app,
        ["init", "Demo", "--id", "demo", "--dir", str(proj), "--template", "menu"],
    )
    assert result.exit_code == 0, result.stdout
    assert "menu" in result.stdout
    assert (proj / "src" / "actions.py").is_file()


def test_cli_unknown_template_fails(tmp_path: Path) -> None:
    result = runner.invoke(
        app,
        ["init", "Demo", "--id", "demo", "--dir", str(tmp_path / "p"), "-t", "zzz"],
    )
    assert result.exit_code == 1
    assert "неизвестный шаблон" in result.stderr
