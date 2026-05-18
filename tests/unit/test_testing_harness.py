"""Тесты помощников офлайн-тестирования ``catalib.testing``."""

from __future__ import annotations

import pytest

from catalib.support import CatalibPlugin, HookResult, HookStrategy, hook, menu_item
from catalib.testing import PluginHarness, load_plugin, make_context, make_params


class _HookPlugin(CatalibPlugin):
    @hook.send_message
    def on_send_message_hook(self, account, params):
        if not params.message.startswith(".up "):
            return HookResult()
        params.message = params.message[4:].upper()
        return HookResult(strategy=HookStrategy.MODIFY, params=params)


class _MenuPlugin(CatalibPlugin):
    @menu_item("Лог", "MESSAGE_CONTEXT_MENU")
    def on_log(self, context):
        self.log("clicked:" + context.get("message", ""))


class _SettingsPlugin(CatalibPlugin):
    @hook.send_message
    def on_send_message_hook(self, account, params):
        if not self.get_setting("on", False):
            return HookResult()
        params.message = params.message + self.get_setting("suffix", "")
        return HookResult(strategy=HookStrategy.MODIFY, params=params)


def test_make_params_is_mutable_namespace() -> None:
    params = make_params("hi", peer=42)
    assert params.message == "hi"
    assert params.peer == 42
    params.message = "bye"
    assert params.message == "bye"


def test_make_context_is_plain_dict() -> None:
    assert make_context(message="m", user=1) == {"message": "m", "user": 1}


def test_harness_send_message_modifies_params() -> None:
    harness = PluginHarness.load(_HookPlugin)
    result = harness.send_message(".up hello")
    assert result.strategy == HookStrategy.MODIFY
    assert harness.last_params.message == "HELLO"
    assert ("send_message", 0) in harness.registered_hooks


def test_harness_send_message_default_passthrough() -> None:
    harness = PluginHarness.load(_HookPlugin)
    assert harness.send_message("plain").strategy == HookStrategy.DEFAULT


def test_harness_raises_without_send_message_hook() -> None:
    harness = PluginHarness.load(_MenuPlugin)
    with pytest.raises(LookupError, match=r"@hook\.send_message"):
        harness.send_message("x")


def test_harness_click_menu_invokes_handler() -> None:
    harness = PluginHarness.load(_MenuPlugin)
    assert [item.text for item in harness.menu_items] == ["Лог"]
    harness.click_menu("Лог", message="ctx")
    assert harness.logged == ["clicked:ctx"]


def test_harness_click_menu_unknown_raises() -> None:
    harness = PluginHarness.load(_MenuPlugin)
    with pytest.raises(LookupError, match="пункт меню не найден"):
        harness.click_menu("нет такого")


def test_harness_applies_settings() -> None:
    harness = load_plugin(_SettingsPlugin, settings={"on": True}, suffix="!")
    result = harness.send_message("hey")
    assert result.strategy == HookStrategy.MODIFY
    assert harness.last_params.message == "hey!"


def test_load_plugin_is_harness_load_synonym() -> None:
    assert isinstance(load_plugin(_HookPlugin), PluginHarness)
