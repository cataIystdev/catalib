"""Тесты декларативной обработки событий жизненного цикла приложения.

Проверяются формы декоратора ``@hook.app_event``, диспетчер
``CatalibPlugin.on_app_event`` и обратная совместимость: пустой плагин не
получает поведения (как до 0.2.0), прямое переопределение ``on_app_event``
в подклассе по-прежнему работает.
"""

from __future__ import annotations

from catalib.support import CatalibPlugin, hook
from catalib.support.sdk import AppEvent


class Lifecycle(CatalibPlugin):
    def __init__(self) -> None:
        super().__init__()
        self.events: list[str] = []

    @hook.app_event
    def any_event(self, event_type):
        self.events.append(f"any:{event_type}")

    @hook.app_event(AppEvent.START)
    def on_start(self, event_type):
        self.events.append(f"start:{event_type}")

    @hook.app_event(AppEvent.PAUSE, AppEvent.RESUME)
    def on_pause_resume(self, event_type):
        self.events.append(f"pr:{event_type}")


def test_app_events_collected_at_class_creation() -> None:
    names = {name for name, _spec in Lifecycle._catalib_app_events}
    assert names == {"any_event", "on_start", "on_pause_resume"}


def test_bare_decorator_subscribes_to_all_events() -> None:
    plugin = Lifecycle()
    plugin.on_app_event(AppEvent.STOP)
    assert plugin.events == ["any:STOP"]


def test_specific_event_only_fires_on_match() -> None:
    plugin = Lifecycle()
    plugin.on_app_event(AppEvent.START)
    assert "start:START" in plugin.events
    assert "any:START" in plugin.events
    assert all("pr:" not in e for e in plugin.events)


def test_multi_event_handler() -> None:
    plugin = Lifecycle()
    plugin.on_app_event(AppEvent.PAUSE)
    plugin.on_app_event(AppEvent.RESUME)
    pr = [e for e in plugin.events if e.startswith("pr:")]
    assert pr == ["pr:PAUSE", "pr:RESUME"]


def test_parenthesized_decorator_means_all_events() -> None:
    class P(CatalibPlugin):
        def __init__(self) -> None:
            super().__init__()
            self.seen: list[str] = []

        @hook.app_event()
        def handler(self, event_type):
            self.seen.append(event_type)

    plugin = P()
    plugin.on_app_event(AppEvent.START)
    plugin.on_app_event(AppEvent.STOP)
    assert plugin.seen == ["START", "STOP"]


def test_empty_plugin_on_app_event_is_noop() -> None:
    """Обратная совместимость: без декораторов on_app_event ничего не делает."""

    class Empty(CatalibPlugin):
        pass

    plugin = Empty()
    plugin.on_app_event(AppEvent.START)  # не должно бросать
    assert plugin._catalib_app_events == ()


def test_direct_override_still_works() -> None:
    """Сырой стиль SDK (переопределение on_app_event) сохраняется."""

    class Raw(CatalibPlugin):
        def __init__(self) -> None:
            super().__init__()
            self.calls: list[str] = []

        def on_app_event(self, event_type):
            self.calls.append(event_type)

    plugin = Raw()
    plugin.on_app_event(AppEvent.RESUME)
    assert plugin.calls == ["RESUME"]


def test_app_event_does_not_disturb_hook_and_menu_registration() -> None:
    """app_event-сбор не ломает прежнюю авторегистрацию хуков/меню."""

    class Mixed(CatalibPlugin):
        @hook.send_message
        def on_send_message_hook(self, account, params):
            return None

        @hook.app_event(AppEvent.START)
        def boot(self, event_type):
            return None

    plugin = Mixed()
    plugin.on_plugin_load()
    assert ("send_message", 0) in plugin.registered_hooks
