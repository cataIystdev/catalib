"""Тесты компилятора выходного файла плагина."""

import pytest

from catalib.bundler.compiler import CompilerError, compile_plugin
from catalib.bundler.model import SourceModule, SourceTree
from catalib.manifest.metadata import extract_metadata
from catalib.manifest.model import PluginManifest


def _tree() -> SourceTree:
    return SourceTree(
        modules=(
            SourceModule("", "__init__.py", "ROOT = 1\n", True),
            SourceModule("plugin", "plugin.py", "class P:\n    pass\n", False),
        ),
        entry="plugin",
    )


def _manifest(**kw) -> PluginManifest:
    base = {"id": "demo", "name": "Demo", "version": "1.0.0"}
    base.update(kw)
    return PluginManifest(**base)


def test_output_is_valid_python_with_literal_metadata() -> None:
    result = compile_plugin(_manifest(icon="exteraPlugins/1", min_version=">=12.5.1"), _tree())
    assert result.filename == "demo.py"
    compile(result.text, "demo.py", "exec")  # синтаксически валиден
    meta = extract_metadata(result.text)
    assert meta["id"] == "demo"
    assert meta["version"] == "1.0.0"
    assert "catalib_install('demo', globals(), _CATALIB_SOURCES, _CATALIB_ENTRY)" in result.text


def test_requirements_block_emitted_only_when_present() -> None:
    without = compile_plugin(_manifest(), _tree())
    assert "__requirements__" not in without.text

    withr = compile_plugin(_manifest(requirements=("tinydb",)), _tree())
    assert "__requirements__ = ['tinydb']" in withr.text
    assert withr.requirements == ("tinydb",)


def test_build_is_deterministic() -> None:
    a = compile_plugin(_manifest(), _tree())
    b = compile_plugin(_manifest(), _tree())
    assert a.text == b.text
    assert a.module_count == 2


def test_binary_requirement_propagates_error() -> None:
    from catalib.bundler.requirements import RequirementsError

    with pytest.raises(RequirementsError):
        compile_plugin(_manifest(requirements=("numpy",)), _tree())


def test_dynamic_metadata_would_fail_validation(monkeypatch: pytest.MonkeyPatch) -> None:
    # Подменяем блок метаданных на динамический и проверяем, что компилятор
    # ловит это через AST-валидацию.
    import catalib.bundler.compiler as compiler_mod

    monkeypatch.setattr(compiler_mod, "_metadata_block", lambda m: "NAME = 'x'\n__id__ = NAME\n")
    with pytest.raises((CompilerError, ValueError)):
        compile_plugin(_manifest(), _tree())
