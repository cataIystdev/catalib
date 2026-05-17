"""Тесты загрузчика манифеста ``catalib.toml``."""

import pytest

from catalib.manifest.loader import (
    MANIFEST_FILENAME,
    load_manifest,
    load_manifest_text,
)
from catalib.manifest.model import ManifestError

VALID = """
[plugin]
id = "demo_plugin"
name = "Demo"
version = "1.0.0"
description = "desc"
author = "catalyst"
icon = "exteraPlugins/1"
min_version = ">=12.5.1"
sdk_version = ">=1.4.4"
requirements = ["tinydb", "mpmath"]

[build]
src = "src"
entry = "app.main"
out = "dist"
"""


def test_load_valid_manifest_text() -> None:
    manifest = load_manifest_text(VALID)
    assert manifest.id == "demo_plugin"
    assert manifest.requirements == ("tinydb", "mpmath")
    assert manifest.build.entry == "app.main"


def test_minimal_manifest_uses_build_defaults() -> None:
    manifest = load_manifest_text('[plugin]\nid = "mini"\nname = "Mini"\nversion = "1.0"\n')
    assert manifest.build.src == "src"
    assert manifest.build.out == "dist"


def test_missing_plugin_section_rejected() -> None:
    with pytest.raises(ManifestError, match=r"\[plugin\]"):
        load_manifest_text('[build]\nsrc = "x"\n')


def test_missing_required_keys_rejected() -> None:
    with pytest.raises(ManifestError, match="обязательных ключей"):
        load_manifest_text('[plugin]\nid = "x"\n')


def test_unknown_plugin_key_rejected() -> None:
    with pytest.raises(ManifestError, match="неизвестные ключи в \\[plugin\\]"):
        load_manifest_text('[plugin]\nid = "ok"\nname = "N"\nversion = "1.0"\nextra = "?"\n')


def test_unknown_top_section_rejected() -> None:
    with pytest.raises(ManifestError, match="неизвестные секции"):
        load_manifest_text('[plugin]\nid = "ok"\nname = "N"\nversion = "1.0"\n[deploy]\nx = 1\n')


def test_wrong_type_rejected() -> None:
    with pytest.raises(ManifestError, match=r"plugin\.version должен быть строкой"):
        load_manifest_text('[plugin]\nid = "ok"\nname = "N"\nversion = 1.0\n')


def test_requirements_must_be_list_of_strings() -> None:
    with pytest.raises(ManifestError, match="requirements"):
        load_manifest_text(
            '[plugin]\nid = "ok"\nname = "N"\nversion = "1.0"\nrequirements = "tinydb"\n'
        )


def test_invalid_toml_reports_error() -> None:
    with pytest.raises(ManifestError, match="разбора TOML"):
        load_manifest_text("[plugin\nid = ")


def test_load_from_directory(tmp_path) -> None:
    (tmp_path / MANIFEST_FILENAME).write_text(VALID, encoding="utf-8")
    manifest = load_manifest(tmp_path)
    assert manifest.name == "Demo"


def test_missing_file_reports_error(tmp_path) -> None:
    with pytest.raises(ManifestError, match="не найден"):
        load_manifest(tmp_path)
