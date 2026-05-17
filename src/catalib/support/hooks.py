"""Декларативная разметка хуков плагина.

Документированная типичная ошибка: реализовать ``on_send_message_hook`` и
забыть вызвать ``add_on_send_message_hook`` в ``on_plugin_load``. Здесь метод
помечается декоратором, а :class:`~catalib.support.plugin.CatalibPlugin`
регистрирует его автоматически — забыть регистрацию невозможно.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

#: Имя атрибута-маркера на функции с описанием хука.
HOOK_ATTR = "__catalib_hook__"


@dataclass(frozen=True, slots=True)
class HookSpec:
    """Описание хука, привязанного к методу плагина.

    :param kind: ``"send_message"`` для хука исходящих сообщений либо
        ``"request"`` для хука сетевого запроса.
    :param name: имя запроса для ``kind == "request"`` (например
        ``"messages.sendMessage"``); для ``send_message`` — пусто.
    :param priority: приоритет регистрации хука.
    """

    kind: str
    name: str
    priority: int


def _mark(func: Callable, spec: HookSpec) -> Callable:
    setattr(func, HOOK_ATTR, spec)
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


#: Единственный публичный экземпляр фабрики декораторов хуков.
hook = _Hook()
