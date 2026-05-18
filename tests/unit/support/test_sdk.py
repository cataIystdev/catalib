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


# --- Расширенный SDK: события приложения и Xposed (офлайн-заглушки) ---


def test_app_event_constants() -> None:
    assert sdk.AppEvent.START == "START"
    assert sdk.AppEvent.STOP == "STOP"
    assert sdk.AppEvent.PAUSE == "PAUSE"
    assert sdk.AppEvent.RESUME == "RESUME"


def test_method_hook_is_subclassable_and_noop() -> None:
    class MyHook(sdk.MethodHook):
        def after_hooked_method(self, param):
            param.append("after")

    h = MyHook()
    assert h.before_hooked_method(object()) is None  # базовый no-op
    seen: list[str] = []
    h.after_hooked_method(seen)
    assert seen == ["after"]
    assert isinstance(h, sdk.BaseHook)


def test_method_replacement_is_subclassable() -> None:
    class Repl(sdk.MethodReplacement):
        def replace_hooked_method(self, param):
            return param * 2

    assert Repl().replace_hooked_method(21) == 42
    assert sdk.MethodReplacement().replace_hooked_method(object()) is None


def test_hook_filter_constants_and_markers() -> None:
    assert sdk.HookFilter.RESULT_NOT_NULL == "RESULT_NOT_NULL"
    assert sdk.HookFilter.ArgumentIsInstanceOf(0, "C") == ("ArgumentIsInstanceOf", 0, "C")
    assert sdk.HookFilter.ResultEqual(7) == ("ResultEqual", 7)
    assert sdk.HookFilter.Or("a", "b") == ("Or", "a", "b")
    assert sdk.HookFilter.Condition("x > 1")[0] == "Condition"


def test_hook_filters_decorator_records_filters_offline() -> None:
    @sdk.hook_filters(sdk.HookFilter.RESULT_NOT_NULL, sdk.HookFilter.ArgumentNotNull(0))
    def handler(param):
        return param

    assert handler(123) == 123  # функция не изменена
    assert handler.__catalib_filters__ == (
        "RESULT_NOT_NULL",
        ("ArgumentNotNull", 0),
    )


def test_find_class_returns_none_offline() -> None:
    assert sdk.find_class("org.telegram.ui.ChatActivity") is None
