"""Тесты слияния и валидации зависимостей плагина."""

import pytest

from catalib.bundler.model import SourceModule
from catalib.bundler.requirements import (
    RequirementsError,
    merge_requirements,
)


def _mod(relname: str, source: str) -> SourceModule:
    return SourceModule(relname=relname, relpath=f"{relname}.py", source=source, is_package=False)


def test_manifest_requirements_preserved_and_deduplicated() -> None:
    result = merge_requirements(["tinydb", "mpmath", "tinydb"], [])
    assert result == ("tinydb", "mpmath")


def test_module_requirements_merged_after_manifest() -> None:
    modules = [
        _mod("a", '__requirements__ = ["mpmath"]\n'),
        _mod("b", '__requirements__ = ["humanize", "mpmath"]\n'),
    ]
    result = merge_requirements(["tinydb"], modules)
    assert result == ("tinydb", "mpmath", "humanize")


@pytest.mark.parametrize(
    "requirement",
    ["numpy", "numpy>=1.0", "pandas==2.0", "opencv-python", "Cryptography", "scipy"],
)
def test_binary_packages_rejected(requirement: str) -> None:
    with pytest.raises(RequirementsError, match="бинарный пакет"):
        merge_requirements([requirement], [])


def test_blank_requirement_rejected() -> None:
    with pytest.raises(RequirementsError, match="пустое требование"):
        merge_requirements(["  "], [])


def test_name_normalization_detects_blocklisted() -> None:
    with pytest.raises(RequirementsError, match="бинарный пакет"):
        merge_requirements(["opencv_python >= 4.5"], [])


def test_pure_python_with_extras_and_specifiers_allowed() -> None:
    result = merge_requirements(["requests[socks]>=2,<3", "tinydb ; python_version>'3'"], [])
    assert result == ("requests[socks]>=2,<3", "tinydb ; python_version>'3'")


def test_module_without_requirements_ignored() -> None:
    result = merge_requirements([], [_mod("x", "X = 1\n")])
    assert result == ()
