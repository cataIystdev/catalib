"""Тесты доменной модели манифеста и её инвариантов."""

import pytest

from catalib.manifest.model import (
    BuildConfig,
    ManifestError,
    PluginManifest,
)


def test_valid_manifest_creates_and_exposes_output_filename() -> None:
    manifest = PluginManifest(id="my_plugin", name="My Plugin", version="1.0.0")
    assert manifest.output_filename == "my_plugin.py"
    assert manifest.build.src == "src"
    assert manifest.requirements == ()


def test_full_manifest_with_constraints_and_requirements() -> None:
    manifest = PluginManifest(
        id="demo2",
        name="Demo",
        version="1.2.3.4",
        description="d",
        author="a",
        icon="exteraPlugins/1",
        min_version=">=12.5.1",
        sdk_version=">=1.4.4",
        requirements=("tinydb", "mpmath"),
        build=BuildConfig(src="plugin_src", entry="app.main", out="build"),
    )
    assert manifest.min_version == ">=12.5.1"
    assert manifest.build.entry == "app.main"


@pytest.mark.parametrize(
    "bad_id",
    ["A", "1plugin", "my-plugin", "x", "_plugin", "плагин", "a" * 33, ""],
)
def test_invalid_plugin_id_rejected(bad_id: str) -> None:
    with pytest.raises(ManifestError, match=r"plugin\.id"):
        PluginManifest(id=bad_id, name="N", version="1.0.0")


@pytest.mark.parametrize("bad_version", ["", "1.0.0-beta", "v1", "1.", "a.b", "1.2.3.4.5"])
def test_invalid_version_rejected(bad_version: str) -> None:
    with pytest.raises(ManifestError, match=r"plugin\.version"):
        PluginManifest(id="ok", name="N", version=bad_version)


@pytest.mark.parametrize("name", ["", "   "])
def test_empty_name_rejected(name: str) -> None:
    with pytest.raises(ManifestError, match=r"plugin\.name"):
        PluginManifest(id="ok", name=name, version="1.0.0")


@pytest.mark.parametrize("constraint", ["abc", ">>1.0", "12.x", ">=v1"])
def test_invalid_app_constraint_rejected(constraint: str) -> None:
    with pytest.raises(ManifestError, match="min_version"):
        PluginManifest(id="ok", name="N", version="1.0.0", min_version=constraint)


def test_blank_requirement_rejected() -> None:
    with pytest.raises(ManifestError, match="requirements"):
        PluginManifest(id="ok", name="N", version="1.0.0", requirements=("valid", "  "))


@pytest.mark.parametrize("field_name", ["src", "out"])
def test_absolute_build_path_rejected(field_name: str) -> None:
    kwargs = {"src": "src", "out": "dist"}
    kwargs[field_name] = "/abs/path"
    with pytest.raises(ManifestError, match=f"build.{field_name}"):
        BuildConfig(**kwargs)


def test_blank_build_field_rejected() -> None:
    with pytest.raises(ManifestError, match=r"build\.entry"):
        BuildConfig(entry="  ")
