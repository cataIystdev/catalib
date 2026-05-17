"""Тесты генератора шаблона проекта."""

from pathlib import Path

import pytest

from catalib import scaffold as scaffold_mod
from catalib.scaffold import ScaffoldError, create_project


def test_creates_expected_structure(tmp_path: Path) -> None:
    created = create_project(tmp_path / "proj", "my_plugin", "My Plugin", "catalyst")
    names = {p.relative_to(tmp_path / "proj").as_posix() for p in created}
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
    manifest = (tmp_path / "proj" / "catalib.toml").read_text(encoding="utf-8")
    assert 'id = "my_plugin"' in manifest
    plugin_src = (tmp_path / "proj" / "src" / "plugin.py").read_text(encoding="utf-8")
    assert "class MyPluginPlugin(CatalibPlugin)" in plugin_src
    assert "from .greeting import build_greeting" in plugin_src


def test_class_name_derivation() -> None:
    assert scaffold_mod._class_name("my_plugin") == "MyPluginPlugin"
    assert scaffold_mod._class_name("demo") == "DemoPlugin"


def test_invalid_plugin_id_rejected(tmp_path: Path) -> None:
    with pytest.raises(ScaffoldError, match="невалиден"):
        create_project(tmp_path / "p", "Bad-Id", "Name")


def test_empty_name_rejected(tmp_path: Path) -> None:
    with pytest.raises(ScaffoldError, match="имя плагина"):
        create_project(tmp_path / "p", "ok", "  ")


def test_non_empty_directory_rejected(tmp_path: Path) -> None:
    target = tmp_path / "proj"
    target.mkdir()
    (target / "existing.txt").write_text("x", encoding="utf-8")
    with pytest.raises(ScaffoldError, match="не пуст"):
        create_project(target, "ok", "Name")


def test_greeting_template_is_valid_logic(tmp_path: Path) -> None:
    create_project(tmp_path / "proj", "greet", "Greet")
    namespace: dict = {}
    exec((tmp_path / "proj" / "src" / "greeting.py").read_text(encoding="utf-8"), namespace)
    assert namespace["build_greeting"]("Алиса") == "Привет, Алиса!"
    assert namespace["build_greeting"]("  ") == "Привет, мир!"
