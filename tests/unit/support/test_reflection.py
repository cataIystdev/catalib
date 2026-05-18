"""Тесты обёрток ``hook_utils`` (офлайн-контракт рефлексии)."""

from __future__ import annotations

from catalib.support import reflection


def test_find_class_reexported_and_none_offline() -> None:
    assert reflection.find_class("org.telegram.ui.ChatActivity") is None


def test_field_getters_return_none_offline() -> None:
    assert reflection.get_private_field(object(), "x") is None
    assert reflection.get_static_private_field(object(), "x") is None


def test_field_setters_return_false_offline() -> None:
    assert reflection.set_private_field(object(), "x", 1) is False
    assert reflection.set_static_private_field(object(), "x", 1) is False


def test_all_exports_present() -> None:
    for name in reflection.__all__:
        assert hasattr(reflection, name)
