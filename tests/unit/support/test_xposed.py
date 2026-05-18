"""Тесты декларативных Xposed-хуков.

Офлайн ``find_class`` всегда ``None``, поэтому фейковый класс/метод
подставляется monkeypatch'ем ``catalib.support.sdk.find_class``. Проверяются:
валидация декоратора, сбор спецификаций, регистрация (метод/конструктор/
перегрузка), проброс ``HookFilter``, делегирование моста, авто-``unhook`` и
устойчивость к ошибкам рефлексии, а также обратная совместимость.
"""

from __future__ import annotations

import pytest

import catalib.support.sdk as sdk_mod
from catalib.support import CatalibPlugin, hook, menu_item
from catalib.support.sdk import HookFilter
from catalib.support.xposed import XposedSpec, xposed


class _FakeMember:
    def __init__(self, name: str, args: tuple) -> None:
        self.name = name
        self.args = args


class _FakeClass:
    def __init__(self, fqn: str) -> None:
        self.fqn = fqn

    def getDeclaredMethod(self, name, *args):
        return _FakeMember(name, args)

    def getDeclaredConstructor(self, *args):
        return _FakeMember("<init>", args)


def _patch_find_class(monkeypatch: pytest.MonkeyPatch, mapping: dict) -> None:
    monkeypatch.setattr(sdk_mod, "find_class", lambda fqn: mapping.get(fqn))


# --- Валидация декоратора ---


def test_decorator_validation() -> None:
    with pytest.raises(ValueError, match="class_fqn"):
        xposed("")
    with pytest.raises(ValueError, match="phase"):
        xposed("a.B", "m", phase="around")
    with pytest.raises(ValueError, match="method_name"):
        xposed("a.B")  # не конструктор и без имени метода


def test_spec_attached_and_collected() -> None:
    class P(CatalibPlugin):
        @xposed("org.telegram.ui.ChatActivity", "onBackPressed", phase="before")
        def on_back(self, param):
            return None

    names = {n for n, _s in P._catalib_xposed}
    assert names == {"on_back"}
    _name, spec = P._catalib_xposed[0]
    assert isinstance(spec, XposedSpec)
    assert spec.phase == "before"
    assert spec.priority == 10


# --- Регистрация и делегирование ---


def test_after_hook_registers_and_delegates(monkeypatch: pytest.MonkeyPatch) -> None:
    fqn = "org.telegram.ui.ChatActivity"
    _patch_find_class(monkeypatch, {fqn: _FakeClass(fqn)})

    class P(CatalibPlugin):
        def __init__(self) -> None:
            super().__init__()
            self.seen: list[str] = []

        @xposed(fqn, "onBackPressed")
        def on_back(self, param):
            self.seen.append(f"after:{param}")
            return "done"

    plugin = P()
    plugin.on_plugin_load()

    assert len(plugin.registered_xposed) == 1
    kind, member, bridge, priority = plugin.registered_xposed[0]
    assert kind == "xposed"
    assert member.name == "onBackPressed"
    assert priority == 10
    # Мост делегирует в связанный метод плагина.
    assert bridge.after_hooked_method("P1") == "done"
    assert plugin.seen == ["after:P1"]


def test_before_and_replace_phases(monkeypatch: pytest.MonkeyPatch) -> None:
    fqn = "a.B"
    _patch_find_class(monkeypatch, {fqn: _FakeClass(fqn)})

    class P(CatalibPlugin):
        @xposed(fqn, "m", phase="before")
        def b(self, param):
            return "B"

        @xposed(fqn, "m", phase="replace")
        def r(self, param):
            return param * 2

    plugin = P()
    plugin.on_plugin_load()
    bridges = {h[1].name: h[2] for h in plugin.registered_xposed}
    # Обе регистрации на метод "m"; различаем по фазе через наличие метода.
    handlers = [h[2] for h in plugin.registered_xposed]
    before = next(h for h in handlers if hasattr(h, "before_hooked_method"))
    replace = next(h for h in handlers if hasattr(h, "replace_hooked_method"))
    assert before.before_hooked_method(None) == "B"
    assert replace.replace_hooked_method(21) == 42
    assert set(bridges) == {"m"}


def test_constructor_and_arg_types(monkeypatch: pytest.MonkeyPatch) -> None:
    fqn = "a.B"
    argfqn = "a.Arg"
    _patch_find_class(
        monkeypatch, {fqn: _FakeClass(fqn), argfqn: _FakeClass(argfqn)}
    )

    class P(CatalibPlugin):
        @xposed(fqn, is_constructor=True, arg_types=[argfqn])
        def ctor(self, param):
            return None

    plugin = P()
    plugin.on_plugin_load()
    member = plugin.registered_xposed[0][1]
    assert member.name == "<init>"
    # Тип аргумента разрешён через find_class в фейковый класс.
    assert len(member.args) == 1
    assert isinstance(member.args[0], _FakeClass)


def test_filters_passed_to_bridge(monkeypatch: pytest.MonkeyPatch) -> None:
    fqn = "a.B"
    _patch_find_class(monkeypatch, {fqn: _FakeClass(fqn)})

    class P(CatalibPlugin):
        @xposed(
            fqn,
            "m",
            filters=[HookFilter.RESULT_NOT_NULL, HookFilter.ArgumentNotNull(0)],
        )
        def h(self, param):
            return None

    plugin = P()
    plugin.on_plugin_load()
    bridge = plugin.registered_xposed[0][2]
    # hook_filters (офлайн-заглушка) записывает фильтры на функцию фазы.
    assert bridge.after_hooked_method.__catalib_filters__ == (
        "RESULT_NOT_NULL",
        ("ArgumentNotNull", 0),
    )


# --- Устойчивость (pitfall #7) ---


def test_class_not_found_is_skipped_and_logged(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _patch_find_class(monkeypatch, {})  # find_class -> None

    class P(CatalibPlugin):
        @xposed("missing.Class", "m")
        def h(self, param):
            return None

    plugin = P()
    plugin.on_plugin_load()  # не должно бросать
    assert plugin.registered_xposed == []
    assert any("не найден" in m for m in plugin.logged)


def test_reflection_error_is_caught(monkeypatch: pytest.MonkeyPatch) -> None:
    class Boom:
        def getDeclaredMethod(self, *a):
            raise RuntimeError("рефлексия сломалась")

    monkeypatch.setattr(sdk_mod, "find_class", lambda fqn: Boom())

    class P(CatalibPlugin):
        @xposed("a.B", "m")
        def h(self, param):
            return None

    plugin = P()
    plugin.on_plugin_load()  # не должно бросать
    assert plugin.registered_xposed == []
    assert any("ошибка регистрации" in m for m in plugin.logged)


# --- Авто-unhook и обратная совместимость ---


def test_unload_unhooks_all_and_calls_on_unload(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fqn = "a.B"
    _patch_find_class(monkeypatch, {fqn: _FakeClass(fqn)})

    class P(CatalibPlugin):
        def __init__(self) -> None:
            super().__init__()
            self.unloaded = False

        @xposed(fqn, "m")
        def h(self, param):
            return None

        def on_unload(self) -> None:
            self.unloaded = True

    plugin = P()
    plugin.on_plugin_load()
    handle = plugin.registered_xposed[0]
    plugin.on_plugin_unload()
    assert plugin.unhooked == [handle]
    assert plugin.unloaded is True


def test_empty_plugin_unload_is_noop_backward_compatible() -> None:
    class Empty(CatalibPlugin):
        pass

    plugin = Empty()
    plugin.on_plugin_load()
    plugin.on_plugin_unload()  # без Xposed/on_unload — ничего не делает
    assert plugin.unhooked == []
    assert plugin.registered_xposed == []


def test_direct_on_plugin_unload_override_still_works() -> None:
    class Raw(CatalibPlugin):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[str] = []

        def on_plugin_unload(self) -> None:
            self.calls.append("custom")

    plugin = Raw()
    plugin.on_plugin_unload()
    assert plugin.calls == ["custom"]


def test_xposed_does_not_disturb_hooks_and_menu(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    fqn = "a.B"
    _patch_find_class(monkeypatch, {fqn: _FakeClass(fqn)})

    class Mixed(CatalibPlugin):
        @hook.send_message
        def on_send_message_hook(self, account, params):
            return None

        @menu_item("Пункт")
        def act(self, context):
            return None

        @xposed(fqn, "m")
        def h(self, param):
            return None

    plugin = Mixed()
    plugin.on_plugin_load()
    assert ("send_message", 0) in plugin.registered_hooks
    assert len(plugin.registered_menu_items) == 1
    assert len(plugin.registered_xposed) == 1
