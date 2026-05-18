"""Тесты опции [build].vendor манифеста."""

import pytest

from catalib.manifest.loader import load_manifest_text
from catalib.manifest.model import BuildConfig, ManifestError

_BASE = '[plugin]\nid = "pp"\nname = "P"\nversion = "1.0.0"\n'


def test_default_vendor_is_auto() -> None:
    assert BuildConfig().vendor == "auto"
    manifest = load_manifest_text(_BASE)
    assert manifest.build.vendor == "auto"


def test_explicit_full() -> None:
    manifest = load_manifest_text(_BASE + '[build]\nvendor = "full"\n')
    assert manifest.build.vendor == "full"


def test_invalid_vendor_rejected_model() -> None:
    with pytest.raises(ManifestError, match=r"build\.vendor"):
        BuildConfig(vendor="partial")


def test_invalid_vendor_rejected_manifest() -> None:
    with pytest.raises(ManifestError, match=r"build\.vendor"):
        load_manifest_text(_BASE + '[build]\nvendor = "nope"\n')


def test_unknown_build_key_still_rejected() -> None:
    with pytest.raises(ManifestError, match=r"\[build\]"):
        load_manifest_text(_BASE + '[build]\nvendoring = "full"\n')
