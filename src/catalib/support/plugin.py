"""Базовый класс плагина с автоматической регистрацией хуков и меню.

``CatalibPlugin`` устраняет шаблон и класс ошибок «хук определён, но не
зарегистрирован»: помеченные :mod:`~catalib.support.hooks` методы и
объявленные пункты меню регистрируются автоматически в ``on_plugin_load``.
Прямой доступ к API SDK не ограничивается — слой только убирает шаблон.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from catalib.support.hooks import (
    APP_EVENT_ATTR,
    HOOK_ATTR,
    REQUEST_HOOK_KINDS,
    AppEventSpec,
    HookSpec,
)
from catalib.support.sdk import BasePlugin
from catalib.support.settings import SettingItem
from catalib.support.xposed import (
    XPOSED_ATTR,
    XposedSpec,
    register_xposed,
    unregister_xposed,
)

#: Атрибут-маркер метода-обработчика пункта меню.
MENU_ATTR = "__catalib_menu__"


#: Допустимые типы меню exteraGram (значения MenuItemType).
MENU_TYPES = (
    "DRAWER_MENU",
    "MESSAGE_CONTEXT_MENU",
    "CHAT_ACTION_MENU",
    "PROFILE_ACTION_MENU",
)


@dataclass(frozen=True, slots=True)
class MenuSpec:
    """Описание пункта меню, привязанного к методу-обработчику.

    Метод-обработчик получает один аргумент ``context: dict`` (см. SDK).

    :param item_id: необязательный стабильный идентификатор пункта.
    :param condition: необязательный предикат показа пункта (как в SDK).
    :param priority: необязательный приоритет пункта (по умолчанию 0 —
        в ``MenuItemData`` не передаётся, действует значение SDK).
    """

    text: str
    menu_type: str
    icon: str = ""
    subtext: str = ""
    item_id: str = ""
    condition: Any = None
    priority: int = 0


def menu_item(
    text: str,
    menu_type: str = "DRAWER_MENU",
    icon: str = "",
    subtext: str = "",
    *,
    item_id: str = "",
    condition: Any = None,
    priority: int = 0,
) -> Callable[[Callable], Callable]:
    """Пометить метод как обработчик пункта меню.

    :param text: подпись пункта меню.
    :param menu_type: тип меню — одно из значений :data:`MENU_TYPES`
        (``DRAWER_MENU``, ``MESSAGE_CONTEXT_MENU``, ``CHAT_ACTION_MENU``,
        ``PROFILE_ACTION_MENU``).
    :param icon: необязательное имя иконки (drawable).
    :param subtext: необязательная подпись под текстом.
    :param item_id: необязательный стабильный идентификатор пункта.
    :param condition: необязательный предикат показа пункта.
    :param priority: необязательный приоритет (0 — не передаётся в SDK).

    Декорируемый метод обязан принимать аргумент ``context: dict``.
    Новые параметры — keyword-only; прежние позиционные вызовы и
    формируемый ``MenuItemData`` не меняются.
    """
    if not isinstance(text, str) or not text:
        raise ValueError("текст пункта меню должен быть непустой строкой")
    if menu_type not in MENU_TYPES:
        raise ValueError(f"menu_type должен быть одним из {MENU_TYPES}")

    def decorator(func: Callable) -> Callable:
        setattr(
            func,
            MENU_ATTR,
            MenuSpec(
                text=text,
                menu_type=menu_type,
                icon=icon,
                subtext=subtext,
                item_id=item_id,
                condition=condition,
                priority=priority,
            ),
        )
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
    #: Собранные обработчики событий приложения: list[(имя_метода, AppEventSpec)].
    _catalib_app_events: tuple[tuple[str, AppEventSpec], ...] = ()
    #: Собранные Xposed-хуки: list[(имя_метода, XposedSpec)].
    _catalib_xposed: tuple[tuple[str, XposedSpec], ...] = ()

    def __init_subclass__(cls, **kwargs: object) -> None:
        super().__init_subclass__(**kwargs)
        hooks: list[tuple[str, HookSpec]] = []
        menu: list[tuple[str, MenuSpec]] = []
        app_events: list[tuple[str, AppEventSpec]] = []
        xposed: list[tuple[str, XposedSpec]] = []
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
            app_event_spec = getattr(member, APP_EVENT_ATTR, None)
            if isinstance(app_event_spec, AppEventSpec):
                app_events.append((attr_name, app_event_spec))
            xposed_spec = getattr(member, XPOSED_ATTR, None)
            if isinstance(xposed_spec, XposedSpec):
                xposed.append((attr_name, xposed_spec))
        cls._catalib_hooks = tuple(sorted(hooks))
        cls._catalib_menu = tuple(sorted(menu))
        cls._catalib_app_events = tuple(sorted(app_events, key=lambda pair: pair[0]))
        cls._catalib_xposed = tuple(sorted(xposed, key=lambda pair: pair[0]))

    #: Дескрипторы зарегистрированных Xposed-хуков (для on_plugin_unload).
    #: Класс-умолчание — безопасный неизменяемый ``()``; экземпляр получает
    #: новый список в ``on_plugin_load`` (нет общего мутабельного состояния).
    _catalib_xposed_handles: tuple[Any, ...] | list[Any] = ()

    def on_plugin_load(self) -> None:
        """Зарегистрировать хуки, меню и Xposed-хуки, затем вызвать on_load."""
        for _attr_name, spec in self._catalib_hooks:
            if spec.kind == "send_message":
                self._register_send_message_hook(spec.priority)
            elif spec.kind == "request":
                self.add_hook(spec.name)
            elif spec.kind in REQUEST_HOOK_KINDS:
                self._register_request_hook(spec)
        for attr_name, menu_spec in self._catalib_menu:
            self._register_menu_item(attr_name, menu_spec)
        handles: list[Any] = []
        for attr_name, xposed_spec in self._catalib_xposed:
            handle = register_xposed(self, attr_name, xposed_spec)
            if handle is not None:
                handles.append(handle)
        self._catalib_xposed_handles = handles
        self.on_load()

    def on_plugin_unload(self) -> None:
        """Снять зарегистрированные Xposed-хуки и вызвать on_unload.

        Прежнее поведение сохранено: без Xposed-хуков и без переопределения
        ``on_unload`` метод фактически ничего не делает (как до 0.2.0, когда
        ``on_plugin_unload`` не определялся вовсе). Подкласс, переопределивший
        ``on_plugin_unload`` напрямую, продолжает работать как раньше.
        """
        for handle in getattr(self, "_catalib_xposed_handles", ()):
            unregister_xposed(self, handle)
        self._catalib_xposed_handles = []
        self.on_unload()

    def on_app_event(self, event_type: Any) -> None:
        """Диспетчер событий жизненного цикла приложения.

        exteraGram вызывает этот метод при смене состояния приложения.
        Вызывает все методы, помеченные ``@hook.app_event``, у которых
        событие подходит (без указанных событий — на любое). Обработчику
        передаётся ``event_type``.

        Прямое переопределение ``on_app_event`` в подклассе по-прежнему
        работает (поведение SDK не ограничивается). Если декораторы не
        использовались, метод ничего не делает — это эквивалентно
        отсутствию обработчика, как было до 0.2.0.
        """
        for attr_name, spec in self._catalib_app_events:
            if not spec.events or event_type in spec.events:
                getattr(self, attr_name)(event_type)

    def _register_request_hook(self, spec: HookSpec) -> None:
        """Зарегистрировать имя запроса/апдейта через ``add_hook``.

        SDK по этому имени будет вызывать фиксированные методы
        ``pre_request_hook``/``post_request_hook``/``on_update_hook``/
        ``on_updates_hook``; их реализуют диспетчеры ниже. Сигнатура
        ``add_hook`` на старых сборках без ``match_substring``/``priority``
        — graceful fallback.
        """
        try:
            self.add_hook(
                spec.name,
                match_substring=spec.match_substring,
                priority=spec.priority,
            )
        except TypeError:
            self.add_hook(spec.name)

    def _dispatch_request_hook(self, kind: str, name: str, *args: Any) -> Any:
        """Вызвать помеченные ``@hook.<kind>`` обработчики по имени.

        Совпадение по равенству имени либо по подстроке (если у спецификации
        ``match_substring``). Возвращается первый не-``None`` результат
        обработчика, иначе ``HookResult()`` (стратегия DEFAULT — поведение
        не меняется, если обработчиков нет: эквивалентно их отсутствию до
        0.3.0). Прямое переопределение метода-хука в подклассе по-прежнему
        перекрывает диспетчер (MRO).
        """
        from catalib.support.sdk import HookResult

        for attr_name, spec in self._catalib_hooks:
            if spec.kind != kind:
                continue
            matched = (
                spec.name in name if spec.match_substring else spec.name == name
            )
            if not matched:
                continue
            result = getattr(self, attr_name)(name, *args)
            if result is not None:
                return result
        return HookResult()

    def pre_request_hook(self, request_name: str, account: int, request: Any) -> Any:
        """Диспетчер ``@hook.pre_request`` (см. :meth:`_dispatch_request_hook`)."""
        return self._dispatch_request_hook(
            "pre_request", request_name, account, request
        )

    def post_request_hook(
        self, request_name: str, account: int, response: Any, error: Any
    ) -> Any:
        """Диспетчер ``@hook.post_request``."""
        return self._dispatch_request_hook(
            "post_request", request_name, account, response, error
        )

    def on_update_hook(self, update_name: str, account: int, update: Any) -> Any:
        """Диспетчер ``@hook.on_update``."""
        return self._dispatch_request_hook(
            "on_update", update_name, account, update
        )

    def on_updates_hook(
        self, container_name: str, account: int, updates: Any
    ) -> Any:
        """Диспетчер ``@hook.on_updates``."""
        return self._dispatch_request_hook(
            "on_updates", container_name, account, updates
        )

    def _register_send_message_hook(self, priority: int) -> None:
        """Зарегистрировать хук исходящих сообщений с приоритетом, если он поддержан."""
        try:
            self.add_on_send_message_hook(priority)
        except TypeError:
            # Старые сборки SDK: метод без аргумента приоритета.
            self.add_on_send_message_hook()

    def _register_menu_item(self, attr_name: str, menu_spec: MenuSpec) -> None:
        """Построить и зарегистрировать пункт меню для метода-обработчика.

        Использует реальный API SDK: ``MenuItemData(menu_type=MenuItemType.X,
        text=..., on_click=...)``. Обработчик получает ``context: dict``.
        """
        from catalib.support.sdk import MenuItemData, MenuItemType

        handler = getattr(self, attr_name)
        kwargs = {
            "menu_type": getattr(MenuItemType, menu_spec.menu_type),
            "text": menu_spec.text,
            "on_click": handler,
        }
        if menu_spec.icon:
            kwargs["icon"] = menu_spec.icon
        if menu_spec.subtext:
            kwargs["subtext"] = menu_spec.subtext
        # Необязательные поля пробрасываются только когда заданы: прежний
        # вызов (без них) формирует тот же MenuItemData, что и раньше.
        if menu_spec.item_id:
            kwargs["item_id"] = menu_spec.item_id
        if menu_spec.condition is not None:
            kwargs["condition"] = menu_spec.condition
        if menu_spec.priority:
            kwargs["priority"] = menu_spec.priority
        self.add_menu_item(MenuItemData(**kwargs))

    def settings(self) -> list[SettingItem]:
        """Переопределяемый метод: вернуть список элементов настроек."""
        return []

    def create_settings(self) -> list[object]:
        """Построить элементы настроек для exteraGram из объявленных."""
        return [item.build() for item in self.settings()]

    def on_load(self) -> None:
        """Переопределяемый хук пользовательской инициализации плагина."""

    def on_unload(self) -> None:
        """Переопределяемый хук пользовательской очистки плагина.

        Вызывается из ``on_plugin_unload`` после автоснятия Xposed-хуков.
        По умолчанию ничего не делает.
        """
