"""Тесты мини-фреймворка: авторегистрация хуков, меню и настройки."""

import pytest

from catalib.support import CatalibPlugin, hook, menu_item, settings


class SamplePlugin(CatalibPlugin):
    def __init__(self) -> None:
        super().__init__()
        self.loaded = False

    @hook.send_message
    def on_send_message_hook(self, account, params):
        return None

    @hook.request("messages.sendMessage", priority=3)
    def on_request(self, *a):
        return None

    @menu_item("Открыть", item_type="DRAWER")
    def open_action(self):
        return "opened"

    def settings(self):
        return [
            settings.header("Sample"),
            settings.switch("enabled", "Включено", default=True),
            settings.text_input("token", "Токен", subtext="секрет"),
            settings.text("Инфо", subtext="строка"),
        ]

    def on_load(self) -> None:
        self.loaded = True


def test_hooks_collected_at_class_creation() -> None:
    kinds = {spec.kind for _name, spec in SamplePlugin._catalib_hooks}
    assert kinds == {"send_message", "request"}


def test_on_plugin_load_registers_hooks_and_menu_and_calls_on_load() -> None:
    plugin = SamplePlugin()
    plugin.on_plugin_load()

    assert ("send_message", 0) in plugin.registered_hooks
    assert ("messages.sendMessage", 0) in plugin.registered_hooks
    assert len(plugin.registered_menu_items) == 1
    assert plugin.registered_menu_items[0].text == "Открыть"
    assert plugin.loaded is True


def test_create_settings_builds_declared_items_offline() -> None:
    plugin = SamplePlugin()
    items = plugin.create_settings()
    kinds = [getattr(i, "kind", None) for i in items]
    assert kinds == ["header", "switch", "input", "text"]


def test_plugin_marked_for_loader_detection() -> None:
    assert SamplePlugin.__catalib_plugin__ is True


def test_send_message_hook_priority_fallback() -> None:
    class Strict(CatalibPlugin):
        @hook.send_message(priority=7)
        def on_send_message_hook(self, account, params):
            return None

        def add_on_send_message_hook(self, *args):
            if args:
                raise TypeError("старый SDK без приоритета")
            self.registered_hooks.append(("send_message", "no-arg"))

    plugin = Strict()
    plugin.on_plugin_load()
    assert ("send_message", "no-arg") in plugin.registered_hooks


def test_menu_item_requires_text() -> None:
    with pytest.raises(ValueError, match="непустой строкой"):
        menu_item("")


def test_hook_request_requires_name() -> None:
    with pytest.raises(ValueError, match="непустой строкой"):
        hook.request("")


def test_empty_plugin_has_no_registrations() -> None:
    class Empty(CatalibPlugin):
        pass

    plugin = Empty()
    plugin.on_plugin_load()
    assert plugin.registered_hooks == []
    assert plugin.registered_menu_items == []
    assert plugin.create_settings() == []
