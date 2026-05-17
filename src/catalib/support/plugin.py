"""Базовый класс плагина с автоматической регистрацией хуков и меню.

``CatalibPlugin`` устраняет шаблон и класс ошибок «хук определён, но не
зарегистрирован»: помеченные :mod:`~catalib.support.hooks` методы и
объявленные пункты меню регистрируются автоматически в ``on_plugin_load``.
Прямой доступ к API SDK не ограничивается — слой только убирает шаблон.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from catalib.support.hooks import HOOK_ATTR, HookSpec
from catalib.support.sdk import BasePlugin
from catalib.support.settings import SettingItem

#: Атрибут-маркер метода-обработчика пункта меню.
MENU_ATTR = "__catalib_menu__"


@dataclass(frozen=True, slots=True)
class MenuSpec:
    """Описание пункта меню, привязанного к методу-обработчику."""

    text: str
    item_type: str


def menu_item(text: str, item_type: str = "DRAWER") -> Callable[[Callable], Callable]:
    """Пометить метод как обработчик пункта меню.

    :param text: подпись пункта меню.
    :param item_type: тип пункта (``DRAWER`` | ``CHAT_ACTION_MENU``).
    """
    if not isinstance(text, str) or not text:
        raise ValueError("текст пункта меню должен быть непустой строкой")

    def decorator(func: Callable) -> Callable:
        setattr(func, MENU_ATTR, MenuSpec(text=text, item_type=item_type))
        return func

    return decorator


class CatalibPlugin(BasePlugin):
    """Базовый класс плагина catalib с автоматической регистрацией.

    Подклассы реализуют помеченные хуки/меню и при необходимости методы
    ``settings`` (вернуть список :class:`SettingItem`) и ``on_load``
    (пользовательская инициализация). Регистрация хуков и меню происходит
    автоматически — повторять её вручную не нужно.
    """

    #: Распознаётся загрузчиком как класс плагина (см. bootstrap).
    __catalib_plugin__ = True

    #: Собранные при создании класса хуки: list[(имя_метода, HookSpec)].
    _catalib_hooks: tuple[tuple[str, HookSpec], ...] = ()
    #: Собранные пункты меню: list[(имя_метода, MenuSpec)].
    _catalib_menu: tuple[tuple[str, MenuSpec], ...] = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        hooks: list[tuple[str, HookSpec]] = []
        menu: list[tuple[str, MenuSpec]] = []
        for attr_name in dir(cls):
            member = getattr(cls, attr_name, None)
            if not callable(member):
                continue
            hook_spec = getattr(member, HOOK_ATTR, None)
            if isinstance(hook_spec, HookSpec):
                hooks.append((attr_name, hook_spec))
            menu_spec = getattr(member, MENU_ATTR, None)
            if isinstance(menu_spec, MenuSpec):
                menu.append((attr_name, menu_spec))
        cls._catalib_hooks = tuple(sorted(hooks))
        cls._catalib_menu = tuple(sorted(menu))

    def on_plugin_load(self) -> None:
        """Зарегистрировать объявленные хуки и меню, затем вызвать on_load."""
        for _attr_name, spec in self._catalib_hooks:
            if spec.kind == "send_message":
                self._register_send_message_hook(spec.priority)
            elif spec.kind == "request":
                self.add_hook(spec.name)
        for attr_name, menu_spec in self._catalib_menu:
            self._register_menu_item(attr_name, menu_spec)
        self.on_load()

    def _register_send_message_hook(self, priority: int) -> None:
        """Зарегистрировать хук исходящих сообщений с приоритетом, если он поддержан."""
        try:
            self.add_on_send_message_hook(priority)
        except TypeError:
            # Старые сборки SDK: метод без аргумента приоритета.
            self.add_on_send_message_hook()

    def _register_menu_item(self, attr_name: str, menu_spec: MenuSpec) -> None:
        """Построить и зарегистрировать пункт меню для метода-обработчика."""
        from catalib.support.sdk import MenuItemData

        handler = getattr(self, attr_name)
        self.add_menu_item(
            MenuItemData(text=menu_spec.text, item_type=menu_spec.item_type, on_click=handler)
        )

    def settings(self) -> list[SettingItem]:
        """Переопределяемый метод: вернуть список элементов настроек."""
        return []

    def create_settings(self) -> list[object]:
        """Построить элементы настроек для exteraGram из объявленных."""
        return [item.build() for item in self.settings()]

    def on_load(self) -> None:
        """Переопределяемый хук пользовательской инициализации плагина."""
