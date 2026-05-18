"""Тесты помодульного отбора вендоренных модулей catalib (tree-shaking)."""

from __future__ import annotations

from pathlib import Path

import pytest

from catalib.bundler.discovery import discover_sources
from catalib.bundler.treeshake import plan_vendor
from catalib.bundler.vendor import all_vendor_modules

_HEAVY = {
    "catalib.support.android",
    "catalib.support.client",
    "catalib.support.files",
    "catalib.support.reflection",
    "catalib.support.dialogs",
    "catalib.support.bulletins",
    "catalib.support.formatting",
    "catalib.support.proxy",
    "catalib.support.classes",
}


def _tree(tmp_path: Path, plugin_src: str):
    src = tmp_path / "src"
    src.mkdir(parents=True, exist_ok=True)
    (src / "__init__.py").write_text("", encoding="utf-8")
    (src / "plugin.py").write_text(plugin_src, encoding="utf-8")
    return discover_sources(src, entry="plugin")


def test_minimal_plugin_prunes_heavy_modules(tmp_path: Path) -> None:
    tree = _tree(
        tmp_path,
        "from catalib.support import CatalibPlugin, hook, HookResult\n"
        "class P(CatalibPlugin):\n"
        "    @hook.send_message\n"
        "    def on_send_message_hook(self, a, p):\n"
        "        return HookResult()\n",
    )
    plan = plan_vendor(tree, "auto")
    assert plan.full is False
    assert "catalib.support.plugin" in plan.kept
    assert "catalib.support.hooks" in plan.kept
    assert "catalib.support.sdk" in plan.kept
    assert _HEAVY.issubset(set(plan.pruned))
    # catalib.support вшит как урезанный __init__.
    init = next(m for m in plan.modules if m.relname == "catalib.support")
    compile(init.source, "<init>", "exec")  # синтаксически валиден
    assert "CatalibPlugin" in init.source and "hook" in init.source
    assert "android" not in init.source


def test_area_import_keeps_only_that_area(tmp_path: Path) -> None:
    tree = _tree(
        tmp_path,
        "from catalib.support import CatalibPlugin\n"
        "from catalib.support import client\n"
        "class P(CatalibPlugin):\n    pass\n",
    )
    plan = plan_vendor(tree, "auto")
    assert "catalib.support.client" in plan.kept
    assert "catalib.support.android" in plan.pruned


def test_direct_submodule_import_kept(tmp_path: Path) -> None:
    tree = _tree(
        tmp_path,
        "from catalib.support import CatalibPlugin\n"
        "from catalib.support.files import get_plugins_dir\n"
        "class P(CatalibPlugin):\n    pass\n",
    )
    plan = plan_vendor(tree, "auto")
    assert "catalib.support.files" in plan.kept
    assert "catalib.support.client" in plan.pruned


@pytest.mark.parametrize(
    "src",
    [
        "import catalib.support\n",
        "from catalib import support\n",
        "from catalib.support import *\n",
        "from catalib.support import CatalibPlugin, NoSuchSymbol\n",
        "import catalib.runtime\n",
    ],
)
def test_ambiguous_usage_falls_back_to_full(tmp_path: Path, src: str) -> None:
    tree = _tree(tmp_path, src + "X = 1\n")
    plan = plan_vendor(tree, "auto")
    assert plan.full is True
    assert plan.warnings  # есть причина
    assert len(plan.modules) == len(all_vendor_modules())


def test_no_catalib_usage_yields_empty(tmp_path: Path) -> None:
    tree = _tree(tmp_path, "VALUE = 1\n")
    plan = plan_vendor(tree, "auto")
    assert plan.full is False
    assert plan.modules == ()
    assert set(plan.pruned) == set(all_vendor_modules())


def test_full_mode_keeps_everything(tmp_path: Path) -> None:
    tree = _tree(
        tmp_path,
        "from catalib.support import CatalibPlugin\nclass P(CatalibPlugin):\n    pass\n",
    )
    plan = plan_vendor(tree, "full")
    assert plan.full is True
    assert {m.relname for m in plan.modules} == set(all_vendor_modules())
    assert plan.pruned == ()


def test_compile_plugin_reports_pruning(tmp_path: Path) -> None:
    from catalib.bundler.compiler import compile_plugin
    from catalib.manifest.model import BuildConfig, PluginManifest

    tree = _tree(
        tmp_path,
        "from catalib.support import CatalibPlugin, hook, HookResult\n"
        "class P(CatalibPlugin):\n"
        "    @hook.send_message\n"
        "    def on_send_message_hook(self, a, p):\n"
        "        return HookResult()\n",
    )
    auto = compile_plugin(PluginManifest(id="pp", name="P", version="1.0.0"), tree)
    assert auto.vendor_full is False
    assert auto.vendored_pruned
    assert "'catalib.support.client'" not in auto.text  # отсечён из таблицы

    full = compile_plugin(
        PluginManifest(id="pp", name="P", version="1.0.0", build=BuildConfig(vendor="full")),
        tree,
    )
    assert full.vendor_full is True
    assert full.vendored_pruned == ()
    assert "'catalib.support.client'" in full.text


def test_trimmed_init_exposes_reexported_submodule(tmp_path: Path) -> None:
    tree = _tree(
        tmp_path,
        "from catalib.support import CatalibPlugin, settings\nclass P(CatalibPlugin):\n    pass\n",
    )
    plan = plan_vendor(tree, "auto")
    init = next(m for m in plan.modules if m.relname == "catalib.support")
    assert "from catalib.support import settings" in init.source
    assert "catalib.support.settings" in plan.kept
