"""Тест границы сред: встраиваемый код не зависит от среды инструмента.

Исходники подпакетов ``runtime`` и ``support`` попадают внутрь собранного
плагина и исполняются под Chaquopy. Они обязаны зависеть только от
стандартной библиотеки и SDK exteraGram — никаких ``typer``/``watchfiles``
и никаких инструментальных подпакетов catalib (``cli``, ``bundler`` и т. п.).
"""

from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest

_EMBEDDABLE_DIRS = ("runtime", "support")
_SRC = Path(__file__).resolve().parents[2] / "src" / "catalib"

#: Модули, предоставляемые exteraGram SDK (не stdlib, но допустимы).
_SDK_ROOTS = {
    "base_plugin",
    "android_utils",
    "client_utils",
    "file_utils",
    "hook_utils",
    "ui",
    "extera_utils",
    "markdown_utils",
    "plugin_settings",
}

_FORBIDDEN_TOOL_SUBPACKAGES = {"cli", "manifest", "bundler", "deploy", "scaffold"}


def _iter_embeddable_files() -> list[Path]:
    files: list[Path] = []
    for name in _EMBEDDABLE_DIRS:
        files.extend(sorted((_SRC / name).rglob("*.py")))
    return files


def _imported_roots(source: str) -> set[str]:
    tree = ast.parse(source)
    roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                roots.add(alias.name.split(".")[0])
        elif isinstance(node, ast.ImportFrom) and node.level == 0 and node.module:
            roots.add(node.module.split(".")[0])
    return roots


@pytest.mark.parametrize("path", _iter_embeddable_files(), ids=lambda p: p.name)
def test_embeddable_module_imports_only_safe_roots(path: Path) -> None:
    roots = _imported_roots(path.read_text(encoding="utf-8"))
    for root in roots:
        if root == "catalib":
            pytest.fail(f"{path.name}: импорт инструментального пакета catalib запрещён")
        if root in _FORBIDDEN_TOOL_SUBPACKAGES:
            pytest.fail(f"{path.name}: импорт инструментального подпакета {root!r}")
        allowed = (
            root in sys.stdlib_module_names
            or root in _SDK_ROOTS
            or root == "catalib"  # обработано выше как ошибка
        )
        assert allowed, f"{path.name}: небезопасный импорт {root!r} во встраиваемом коде"
