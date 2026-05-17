"""Тесты безопасных импортов SDK и заглушек."""

from catalib.support import sdk


def test_offline_marks_sdk_unavailable() -> None:
    # В тестовом окружении exteraGram отсутствует.
    assert sdk.SDK_AVAILABLE is False


def test_stub_base_plugin_records_registration() -> None:
    plugin = sdk.BasePlugin()
    plugin.add_on_send_message_hook(5)
    plugin.add_hook("messages.sendMessage")
    plugin.add_menu_item({"text": "X"})
    assert plugin.registered_hooks == [("send_message", 5), ("messages.sendMessage", 0)]
    assert plugin.registered_menu_items == [{"text": "X"}]


def test_stub_settings_roundtrip() -> None:
    plugin = sdk.BasePlugin()
    assert plugin.get_setting("k", "d") == "d"
    plugin.set_setting("k", "v")
    assert plugin.get_setting("k") == "v"


def test_hook_result_defaults_to_default_strategy() -> None:
    assert sdk.HookResult().strategy == sdk.HookStrategy.DEFAULT
    assert sdk.HookResult(sdk.HookStrategy.CANCEL).strategy == "CANCEL"


def test_log_and_ui_thread_are_safe_offline() -> None:
    sdk.log("сообщение")  # не должно бросать
    seen = []
    sdk.run_on_ui_thread(lambda: seen.append(1))
    assert seen == [1]


def test_get_plugins_dir_returns_path_offline() -> None:
    assert isinstance(sdk.get_plugins_dir(), str)
    assert sdk.get_plugins_dir()
