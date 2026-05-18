"""Декларативная разметка хуков плагина.

Документированная типичная ошибка: реализовать ``on_send_message_hook`` и
забыть вызвать ``add_on_send_message_hook`` в ``on_plugin_load``. Здесь метод
помечается декоратором, а :class:`~catalib.support.plugin.CatalibPlugin`
регистрирует его автоматически — забыть регистрацию невозможно.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

#: Имя атрибута-маркера на функции с описанием хука.
HOOK_ATTR = "__catalib_hook__"

#: Имя атрибута-маркера на методе-обработчике события приложения.
APP_EVENT_ATTR = "__catalib_app_event__"


#: Виды хуков, привязанных к фиксированным методам SDK по имени
#: запроса/апдейта (диспетчеризуются :class:`CatalibPlugin`).
REQUEST_HOOK_KINDS = ("pre_request", "post_request", "on_update", "on_updates")


@dataclass(frozen=True, slots=True)
class HookSpec:
    """Описание хука, привязанного к методу плагина.

    :param kind: ``"send_message"`` — хук исходящих сообщений;
        ``"request"`` — общая регистрация по имени запроса (как раньше);
        ``"pre_request"``/``"post_request"``/``"on_update"``/
        ``"on_updates"`` — конкретные хук-методы SDK с диспетчеризацией.
    :param name: имя запроса/апдейта (для ``send_message`` — пусто).
    :param priority: приоритет регистрации хука.
    :param match_substring: матчить ``name`` как подстроку (как в
        ``add_hook(match_substring=True)``); по умолчанию ``False``.
    """

    kind: str
    name: str
    priority: int
    match_substring: bool = False


@dataclass(frozen=True, slots=True)
class AppEventSpec:
    """Описание подписки метода на события жизненного цикла приложения.

    :param events: кортеж событий (значения ``AppEvent``); пустой кортеж —
        обработчик вызывается на всех событиях.
    """

    events: tuple[Any, ...]


def _mark(func: Callable, spec: HookSpec) -> Callable:
    setattr(func, HOOK_ATTR, spec)
    return func


def _mark_app_event(func: Callable, events: tuple[Any, ...]) -> Callable:
    setattr(func, APP_EVENT_ATTR, AppEventSpec(events=events))
    return func


class _Hook:
    """Фабрика декораторов хуков (экземпляр доступен как ``hook``)."""

    def send_message(self, func: Callable | None = None, *, priority: int = 0) -> Callable:
        """Пометить метод как хук исходящих сообщений.

        Применяется и как ``@hook.send_message``, и как
        ``@hook.send_message(priority=5)``.
        """

        def decorator(target: Callable) -> Callable:
            return _mark(target, HookSpec(kind="send_message", name="", priority=priority))

        return decorator(func) if func is not None else decorator

    def request(self, name: str, *, priority: int = 0) -> Callable[[Callable], Callable]:
        """Пометить метод как хук сетевого запроса ``name``."""
        if not isinstance(name, str) or not name:
            raise ValueError("имя запроса для hook.request должно быть непустой строкой")

        def decorator(target: Callable) -> Callable:
            return _mark(target, HookSpec(kind="request", name=name, priority=priority))

        return decorator

    def _request_kind(
        self, kind: str, name: str, priority: int, match_substring: bool
    ) -> Callable[[Callable], Callable]:
        """Общий конструктор декораторов хук-методов запроса/апдейта."""
        if not isinstance(name, str) or not name:
            raise ValueError(f"имя для hook.{kind} должно быть непустой строкой")

        def decorator(target: Callable) -> Callable:
            return _mark(
                target,
                HookSpec(
                    kind=kind,
                    name=name,
                    priority=priority,
                    match_substring=match_substring,
                ),
            )

        return decorator

    def pre_request(
        self, name: str, *, priority: int = 0, match_substring: bool = False
    ) -> Callable[[Callable], Callable]:
        """Пометить метод как хук ``pre_request_hook`` запроса ``name``.

        Обработчик: ``handler(request_name, account, request) ->
        HookResult | None``. catalib регистрирует ``add_hook(name)`` и
        диспетчеризует вызов ``pre_request_hook`` в помеченный метод.
        """
        return self._request_kind("pre_request", name, priority, match_substring)

    def post_request(
        self, name: str, *, priority: int = 0, match_substring: bool = False
    ) -> Callable[[Callable], Callable]:
        """Пометить метод как хук ``post_request_hook`` запроса ``name``.

        Обработчик: ``handler(request_name, account, response, error) ->
        HookResult | None``.
        """
        return self._request_kind("post_request", name, priority, match_substring)

    def on_update(
        self, name: str, *, priority: int = 0, match_substring: bool = False
    ) -> Callable[[Callable], Callable]:
        """Пометить метод как хук ``on_update_hook`` апдейта ``name``.

        Обработчик: ``handler(update_name, account, update) ->
        HookResult | None``.
        """
        return self._request_kind("on_update", name, priority, match_substring)

    def on_updates(
        self, name: str, *, priority: int = 0, match_substring: bool = False
    ) -> Callable[[Callable], Callable]:
        """Пометить метод как хук ``on_updates_hook`` контейнера ``name``.

        Обработчик: ``handler(container_name, account, updates) ->
        HookResult | None``.
        """
        return self._request_kind("on_updates", name, priority, match_substring)

    def app_event(self, *events: Any) -> Callable:
        """Пометить метод как обработчик событий жизненного цикла приложения.

        exteraGram вызывает ``plugin.on_app_event(event_type)`` при смене
        состояния приложения. :class:`~catalib.support.plugin.CatalibPlugin`
        реализует диспетчер ``on_app_event``, который вызывает помеченные
        методы; ручная проверка ``event_type`` в одном большом методе не
        нужна. Сам обработчик получает ``event_type``.

        Формы применения:

        - ``@hook.app_event`` или ``@hook.app_event()`` — все события;
        - ``@hook.app_event(AppEvent.START)`` — только указанные события;
        - ``@hook.app_event(AppEvent.PAUSE, AppEvent.RESUME)`` — несколько.

        :param events: значения ``AppEvent``; без аргументов — все события.
            Перечень событий не валидируется: будущая сборка SDK может
            добавить новые, и catalib не должен их отвергать.
        """
        # Бар-форма: @hook.app_event — единственный аргумент это сам метод
        # (он callable; значения AppEvent — не callable).
        if len(events) == 1 and callable(events[0]):
            return _mark_app_event(events[0], ())

        def decorator(target: Callable) -> Callable:
            return _mark_app_event(target, tuple(events))

        return decorator


#: Единственный публичный экземпляр фабрики декораторов хуков.
hook = _Hook()
