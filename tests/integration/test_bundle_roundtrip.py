"""Сборка модульного дерева и исполнение результата как делает exteraGram.

Проверяет ядро catalib целиком в одном процессе: компиляция, импорт
собранного файла под именем ``<plugin_id>``, работа подмодулей и
относительных импортов, поднятие класса плагина на верхний уровень,
указание трейсбека на исходный файл, изоляция двух плагинов и безопасная
повторная загрузка.
"""

from __future__ import annotations

import importlib
import importlib.util
import sys
import traceback
from collections.abc import Iterator
from pathlib import Path

import pytest

from catalib.bundler.compiler import compile_plugin
from catalib.bundler.discovery import discover_sources
from catalib.manifest.model import PluginManifest

PLUGIN_FILES = {
    "__init__.py": "ROOT_RAN = True\nfrom . import shared\n",
    "shared.py": "VALUE = 41\n",
    "sdkstub.py": "class BasePlugin:\n    pass\n",
    "plugin.py": (
        "from . import shared\n"
        "from .sdkstub import BasePlugin\n"
        "from .pkg.tool import boom\n"
        "\n"
        "boom  # держим ссылку, чтобы импорт не вырезали\n"
        "\n"
        "class MyPlugin(BasePlugin):\n"
        "    COMPUTED = shared.VALUE + 1\n"
    ),
    "pkg/__init__.py": "",
    "pkg/tool.py": "def boom():\n    raise ValueError('synthetic failure')\n",
}


def _write_tree(root: Path, files: dict[str, str]) -> Path:
    src = root / "src"
    for rel, content in files.items():
        target = src / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return src


def _build(tmp_path: Path, plugin_id: str, files: dict[str, str]) -> Path:
    src = _write_tree(tmp_path / plugin_id, files)
    tree = discover_sources(src, entry="plugin")
    manifest = PluginManifest(id=plugin_id, name="Demo", version="1.0.0")
    result = compile_plugin(manifest, tree)
    out = tmp_path / result.filename
    out.write_text(result.text, encoding="utf-8")
    return out


def _import_as_plugin(path: Path, plugin_id: str):
    """Импортировать собранный файл так же, как это делает exteraGram."""
    spec = importlib.util.spec_from_file_location(plugin_id, path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[plugin_id] = module
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def import_cleanup() -> Iterator[None]:
    meta_before = list(sys.meta_path)
    modules_before = set(sys.modules)
    yield
    sys.meta_path[:] = meta_before
    for name in set(sys.modules) - modules_before:
        del sys.modules[name]


def test_bundle_executes_and_exposes_plugin_class(tmp_path: Path, import_cleanup: None) -> None:
    path = _build(tmp_path, "demo_plugin", PLUGIN_FILES)
    module = _import_as_plugin(path, "demo_plugin")

    assert module.ROOT_RAN is True  # тело src/__init__.py исполнено в этом модуле
    assert hasattr(module, "MyPlugin")  # класс плагина поднят на верхний уровень
    assert module.MyPlugin.COMPUTED == 42  # относительный импорт shared сработал
    assert "demo_plugin.pkg.tool" in sys.modules  # ленивая загрузка подмодуля


def test_traceback_points_to_original_source(tmp_path: Path, import_cleanup: None) -> None:
    path = _build(tmp_path, "tb_plugin", PLUGIN_FILES)
    _import_as_plugin(path, "tb_plugin")
    tool = importlib.import_module("tb_plugin.pkg.tool")
    try:
        tool.boom()
    except ValueError:
        text = traceback.format_exc()
    assert "<tb_plugin>/pkg/tool.py" in text
    assert "raise ValueError('synthetic failure')" in text


def test_two_plugins_are_isolated(tmp_path: Path, import_cleanup: None) -> None:
    files_b = dict(PLUGIN_FILES)
    files_b["shared.py"] = "VALUE = 100\n"
    path_a = _build(tmp_path, "plugin_a", PLUGIN_FILES)
    path_b = _build(tmp_path, "plugin_b", files_b)

    mod_a = _import_as_plugin(path_a, "plugin_a")
    mod_b = _import_as_plugin(path_b, "plugin_b")

    assert mod_a.MyPlugin.COMPUTED == 42
    assert mod_b.MyPlugin.COMPUTED == 101
    assert sys.modules["plugin_a.shared"] is not sys.modules["plugin_b.shared"]


def test_reload_is_safe(tmp_path: Path, import_cleanup: None) -> None:
    path = _build(tmp_path, "reload_plugin", PLUGIN_FILES)
    _import_as_plugin(path, "reload_plugin")
    # Повторная загрузка (как dev-server reload): не должно быть дублей finder'ов.
    _import_as_plugin(path, "reload_plugin")
    finders = [f for f in sys.meta_path if getattr(f, "_catalib_plugin", None) == "reload_plugin"]
    assert len(finders) == 1
    assert importlib.import_module("reload_plugin.shared").VALUE == 41
