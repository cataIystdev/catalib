"""Тесты карты соответствия модулей исходным файлам."""

from catalib.bundler.model import SourceModule, SourceTree
from catalib.bundler.sourcemap import (
    build_source_map,
    module_origin,
    runtime_fullname,
)


def test_runtime_fullname_root_and_submodule() -> None:
    assert runtime_fullname("my_plugin", "") == "my_plugin"
    assert runtime_fullname("my_plugin", "utils") == "my_plugin.utils"
    assert runtime_fullname("my_plugin", "pkg.sub") == "my_plugin.pkg.sub"


def test_module_origin_is_readable_and_stable() -> None:
    assert module_origin("my_plugin", "pkg/sub.py") == "<my_plugin>/pkg/sub.py"
    assert module_origin("my_plugin", "pkg/sub.py") == module_origin("my_plugin", "pkg/sub.py")


def test_build_source_map_covers_all_modules() -> None:
    tree = SourceTree(
        modules=(
            SourceModule("", "__init__.py", "", True),
            SourceModule("plugin", "plugin.py", "", False),
            SourceModule("pkg", "pkg/__init__.py", "", True),
            SourceModule("pkg.sub", "pkg/sub.py", "", False),
        ),
        entry="plugin",
    )
    mapping = build_source_map("demo", tree)
    assert mapping == {
        "demo": "<demo>/__init__.py",
        "demo.plugin": "<demo>/plugin.py",
        "demo.pkg": "<demo>/pkg/__init__.py",
        "demo.pkg.sub": "<demo>/pkg/sub.py",
    }
