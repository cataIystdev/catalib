"""Тесты статической (AST) валидации метаданных плагина."""

import pytest

from catalib.manifest.metadata import (
    MetadataError,
    extract_metadata,
    validate_metadata,
)

GOOD = """
__id__ = "my_plugin"
__name__ = "My Plugin"
__version__ = "1.0.0"
__requirements__ = ["tinydb", "mpmath"]

from base_plugin import BasePlugin


class P(BasePlugin):
    pass
"""


def test_extract_reads_literal_metadata() -> None:
    meta = extract_metadata(GOOD)
    assert meta["id"] == "my_plugin"
    assert meta["name"] == "My Plugin"
    assert meta["requirements"] == ["tinydb", "mpmath"]


def test_extract_ignores_dynamic_values() -> None:
    meta = extract_metadata('NAME = "x"\n__id__ = NAME\n__name__ = "ok"\n')
    assert "id" not in meta
    assert meta["name"] == "ok"


def test_validate_accepts_good_metadata() -> None:
    validate_metadata(GOOD, expected_id="my_plugin")


def test_validate_rejects_dynamic_id() -> None:
    src = 'NAME = "x"\n__id__ = NAME\n__name__ = "n"\n__version__ = "1.0"\n'
    with pytest.raises(MetadataError, match="__id__ должен быть строковым литералом"):
        validate_metadata(src, expected_id="x")


def test_validate_rejects_fstring_id() -> None:
    src = '__id__ = f"a{1}"\n__name__ = "n"\n__version__ = "1.0"\n'
    with pytest.raises(MetadataError, match="__id__ должен быть строковым литералом"):
        validate_metadata(src, expected_id="a1")


def test_validate_rejects_id_filename_mismatch() -> None:
    src = '__id__ = "other"\n__name__ = "n"\n__version__ = "1.0"\n'
    with pytest.raises(MetadataError, match="не совпадает с именем файла"):
        validate_metadata(src, expected_id="expected")


def test_validate_reports_missing_required() -> None:
    with pytest.raises(MetadataError, match="отсутствует обязательный дандер __version__"):
        validate_metadata('__id__ = "x"\n__name__ = "n"\n', expected_id="x")


def test_validate_rejects_bad_version() -> None:
    src = '__id__ = "x"\n__name__ = "n"\n__version__ = "1.0-beta"\n'
    with pytest.raises(MetadataError, match="__version__"):
        validate_metadata(src, expected_id="x")


def test_validate_rejects_non_list_requirements() -> None:
    src = '__id__ = "x"\n__name__ = "n"\n__version__ = "1.0"\n__requirements__ = "tinydb"\n'
    with pytest.raises(MetadataError, match="__requirements__ должен быть списком"):
        validate_metadata(src, expected_id="x")


def test_syntax_error_reported() -> None:
    with pytest.raises(MetadataError, match="синтаксическая ошибка"):
        extract_metadata("def (:\n")
