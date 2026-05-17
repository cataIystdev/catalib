"""Прямые unit-тесты встраиваемого загрузчика.

Интеграционные тесты исполняют загрузчик из встроенной строки (coverage его
не видит). Здесь он тестируется напрямую как модуль.
"""

from __future__ import annotations

import sys
import types
from collections.abc import Iterator

import pytest

from catalib.runtime import bootstrap


@pytest.fixture
def import_cleanup() -> Iterator[None]:
    meta_before = list(sys.meta_path)
    modules_before = set(sys.modules)
    yield
    sys.meta_path[:] = meta_before
    for name in set(sys.modules) - modules_before:
        del sys.modules[name]


def _install(plugin_id: str, sources: dict, entry: str) -> types.ModuleType:
    module = types.ModuleType(plugin_id)
    sys.modules[plugin_id] = module
    bootstrap.catalib_install(plugin_id, module.__dict__, sources, entry)
    return module


def test_install_imports_entry_and_lifts_plugin_class(import_cleanup: None) -> None:
    sources = {
        "utp.pkg": ("VALUE = 41\n", True, "<utp>/pkg/__init__.py"),
        "utp.pkg.tool": (
            "from . import VALUE\n\ndef compute():\n    return VALUE + 1\n",
            False,
            "<utp>/pkg/tool.py",
        ),
        "utp.app": (
            "from .pkg.tool import compute\n"
            "\n"
            "class BasePlugin:\n    pass\n"
            "\n"
            "class AppPlugin(BasePlugin):\n"
            "    __catalib_plugin__ = True\n"
            "    RESULT = compute()\n",
            False,
            "<utp>/app.py",
        ),
    }
    module = _install("utp", sources, "utp.app")
    assert hasattr(module, "AppPlugin")
    assert module.AppPlugin.RESULT == 42
    assert module.__name__ == "utp"
    assert module.__package__ == "utp"


def test_reload_keeps_single_finder_and_purges_submodules(import_cleanup: None) -> None:
    sources = {
        "rl.app": (
            "class BasePlugin:\n    pass\n\nclass P(BasePlugin):\n    pass\n",
            False,
            "<rl>/a.py",
        ),
    }
    _install("rl", sources, "rl.app")
    _install("rl", sources, "rl.app")
    finders = [f for f in sys.meta_path if getattr(f, "_catalib_plugin", None) == "rl"]
    assert len(finders) == 1


def test_root_body_executed_in_module(import_cleanup: None) -> None:
    sources = {
        "rb": ("ROOT_FLAG = True\n", True, "<rb>/__init__.py"),
        "rb.app": (
            "class BasePlugin:\n    pass\n\nclass P(BasePlugin):\n    pass\n",
            False,
            "<rb>/a.py",
        ),
    }
    module = _install("rb", sources, "rb.app")
    assert module.ROOT_FLAG is True


def test_find_plugin_class_filters_by_entry_module() -> None:
    class BasePlugin:
        pass

    class Imported(BasePlugin):  # имитация импортированного CatalibPlugin
        __catalib_plugin__ = True

    class Own(BasePlugin):
        __catalib_plugin__ = True

    Imported.__module__ = "catalib.support.plugin"
    Own.__module__ = "plug.app"
    namespace = {"Imported": Imported, "Own": Own, "x": 1}
    found = bootstrap._find_plugin_class(namespace, "plug.app")
    assert found is Own


def test_find_plugin_class_returns_none_when_absent() -> None:
    assert bootstrap._find_plugin_class({"a": 1, "b": object}, "m") is None


def test_stale_vendored_catalib_is_purged(import_cleanup: None) -> None:
    """Устаревший catalib.* из прошлого деплоя вычищается при install."""
    import importlib
    import importlib.machinery

    stale = types.ModuleType("catalib.support")
    stale.__spec__ = importlib.machinery.ModuleSpec(
        "catalib.support", loader=None, origin="<catalib-vendor>/old.py"
    )
    stale.MARKER = "OLD"
    sys.modules["catalib.support"] = stale

    sources = {
        "vp.app": (
            "import catalib.support as cs\n"
            "class BasePlugin:\n    pass\n"
            "class P(BasePlugin):\n    VALUE = cs.MARKER\n",
            False,
            "<vp>/app.py",
        ),
        "catalib": ("", True, "<catalib-vendor>/catalib/__init__.py"),
        "catalib.support": ('MARKER = "NEW"\n', True, "<catalib-vendor>/catalib/support/__init__.py"),
    }
    module = _install("vp", sources, "vp.app")
    assert module.P.VALUE == "NEW"
    assert sys.modules["catalib.support"].MARKER == "NEW"


def test_real_host_catalib_not_purged(import_cleanup: None) -> None:
    """Настоящий host-catalib (origin-файл) не трогается очисткой."""
    before = sys.modules.get("catalib")
    sources = {
        "hp.app": (
            "class BasePlugin:\n    pass\nclass P(BasePlugin):\n    pass\n",
            False,
            "<hp>/app.py",
        ),
    }
    _install("hp", sources, "hp.app")
    assert sys.modules.get("catalib") is before
    assert before is not None and not getattr(before.__spec__, "origin", "").startswith("<")
