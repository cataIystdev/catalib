"""Тесты обхода дерева исходников плагина."""

from pathlib import Path

import pytest

from catalib.bundler.discovery import discover_sources
from catalib.bundler.model import DiscoveryError


def _make_tree(root: Path, files: dict[str, str]) -> Path:
    src = root / "src"
    for rel, content in files.items():
        target = src / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
    return src


def test_discovers_packages_and_submodules(tmp_path: Path) -> None:
    src = _make_tree(
        tmp_path,
        {
            "__init__.py": "ROOT = 1\n",
            "plugin.py": "ENTRY = 1\n",
            "utils.py": "X = 1\n",
            "pkg/__init__.py": "",
            "pkg/sub.py": "Y = 2\n",
            "pkg/inner/__init__.py": "",
            "pkg/inner/deep.py": "Z = 3\n",
        },
    )
    tree = discover_sources(src, entry="plugin")

    assert tree.root is not None
    assert tree.root.source == "ROOT = 1\n"
    names = {m.relname: m.is_package for m in tree.modules}
    assert names == {
        "": True,
        "plugin": False,
        "utils": False,
        "pkg": True,
        "pkg.sub": False,
        "pkg.inner": True,
        "pkg.inner.deep": False,
    }
    # Корневой модуль идёт первым.
    assert tree.modules[0].is_root
    # Подмодули отсортированы детерминированно.
    sub = [m.relname for m in tree.submodules]
    assert sub == sorted(sub)


def test_no_root_init_is_allowed(tmp_path: Path) -> None:
    src = _make_tree(tmp_path, {"plugin.py": "P = 1\n"})
    tree = discover_sources(src, entry="plugin")
    assert tree.root is None
    assert [m.relname for m in tree.submodules] == ["plugin"]


def test_missing_dir_rejected(tmp_path: Path) -> None:
    with pytest.raises(DiscoveryError, match="не найден"):
        discover_sources(tmp_path / "absent", entry="plugin")


def test_empty_src_rejected(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir()
    with pytest.raises(DiscoveryError, match="нет ни одного"):
        discover_sources(src, entry="plugin")


def test_package_without_init_rejected(tmp_path: Path) -> None:
    src = _make_tree(tmp_path, {"plugin.py": "P = 1\n", "pkg/sub.py": "Y = 1\n"})
    with pytest.raises(DiscoveryError, match=r"без __init__\.py"):
        discover_sources(src, entry="plugin")


def test_entry_not_found_lists_available(tmp_path: Path) -> None:
    src = _make_tree(tmp_path, {"plugin.py": "P = 1\n", "helpers.py": "H = 1\n"})
    with pytest.raises(DiscoveryError, match="helpers"):
        discover_sources(src, entry="missing")


def test_pycache_and_hidden_skipped(tmp_path: Path) -> None:
    src = _make_tree(
        tmp_path,
        {
            "plugin.py": "P = 1\n",
            "__pycache__/plugin.cpython-311.pyc.py": "junk\n",
            ".hidden/secret.py": "S = 1\n",
        },
    )
    tree = discover_sources(src, entry="plugin")
    assert {m.relname for m in tree.submodules} == {"plugin"}


def test_path_traversal_via_symlink_rejected(tmp_path: Path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text("EVIL = 1\n", encoding="utf-8")
    src = _make_tree(tmp_path, {"plugin.py": "P = 1\n"})
    link = src / "linked.py"
    link.symlink_to(outside)
    with pytest.raises(DiscoveryError, match="path traversal"):
        discover_sources(src, entry="plugin")
