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


# --- Полнота ядра (0.3.0): HookResult, BasePlugin, run_on_ui_thread ---


def test_hook_result_has_all_sdk_fields() -> None:
    r = sdk.HookResult(
        sdk.HookStrategy.MODIFY,
        params={"p": 1},
        request="req",
        response="resp",
        update="upd",
        updates="upds",
    )
    assert r.strategy == "MODIFY"
    assert r.params == {"p": 1}
    assert r.request == "req"
    assert r.response == "resp"
    assert r.update == "upd"
    assert r.updates == "upds"
    # Значения по умолчанию.
    d = sdk.HookResult()
    assert d.request is None and d.response is None
    assert d.update is None and d.updates is None


def test_base_plugin_settings_export_import() -> None:
    p = sdk.BasePlugin()
    p.set_setting("a", 1)
    p.set_setting("b", 2, reload_settings=True)
    assert p.export_settings() == {"a": 1, "b": 2}
    p.import_settings({"b": 20, "c": 3})
    assert p.get_setting("b") == 20
    assert p.get_setting("c") == 3


def test_base_plugin_menu_item_id_and_removal() -> None:
    p = sdk.BasePlugin()
    mid = p.add_menu_item({"text": "X"})
    assert mid is not None
    assert len(p.registered_menu_items) == 1
    p.remove_menu_item(mid)
    assert p.removed_menu_items == [mid]
    assert p.registered_menu_items == []


def test_base_plugin_add_hook_match_substring() -> None:
    p = sdk.BasePlugin()
    p.add_hook("messages.sendMessage")
    assert ("messages.sendMessage", 0) in p.registered_hooks
    p.add_hook("messages.", match_substring=True, priority=2)
    assert ("messages.", 2) in p.registered_hooks
    assert ("messages.", "substring") in p.registered_hooks


def test_base_plugin_hook_method_records_full_call() -> None:
    p = sdk.BasePlugin()
    h = p.hook_method(
        "m", "handler", priority=7, before_filters=["f"], before=lambda x: x
    )
    assert h == ("xposed", "m", "handler", 7)  # обратная совместимость
    call = p.hook_method_calls[0]
    assert call["priority"] == 7
    assert call["before_filters"] == ("f",)
    assert callable(call["before"])


def test_base_plugin_hook_all_methods_and_constructors() -> None:
    p = sdk.BasePlugin()
    hm = p.hook_all_methods("Clazz", "doStuff", "h")
    hc = p.hook_all_constructors("Clazz", "h")
    assert isinstance(hm, list) and isinstance(hc, list)
    assert ("xposed_all_methods", "Clazz", "doStuff", "h") in p.registered_hook_all
    assert ("xposed_all_constructors", "Clazz", "h") in p.registered_hook_all


def test_run_on_ui_thread_delay_offline_runs_immediately() -> None:
    seen: list[int] = []
    sdk.run_on_ui_thread(lambda: seen.append(1), delay=500)
    assert seen == [1]
