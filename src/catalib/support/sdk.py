"""Безопасные импорты SDK exteraGram с заглушками для офлайн-тестов.

Единственная точка адаптации к SDK: если плагин исполняется в exteraGram —
используются настоящие классы и функции; вне приложения (юнит-тесты на
обычном Python) подключаются минимальные заглушки с тем же интерфейсом.
Это устраняет россыпь ``try/except`` по плагину и даёт офлайн-тестируемость
доменной логики. Код только стандартной библиотеки и SDK.
"""

from __future__ import annotations

import tempfile
from typing import Any

#: Истинно, если плагин исполняется внутри exteraGram (SDK доступен).
SDK_AVAILABLE: bool

try:  # pragma: no cover - ветка выполняется только на устройстве
    from base_plugin import (
        BasePlugin,
        HookResult,
        HookStrategy,
        MenuItemData,
        MenuItemType,
    )

    SDK_AVAILABLE = True
except Exception:  # pragma: no cover - ветка для обычного Python
    SDK_AVAILABLE = False

    class HookStrategy:
        """Заглушка стратегий хука, повторяющая значения SDK."""

        DEFAULT = "DEFAULT"
        CANCEL = "CANCEL"
        MODIFY = "MODIFY"
        MODIFY_FINAL = "MODIFY_FINAL"

    class HookResult:
        """Заглушка результата хука."""

        def __init__(self, strategy: str | None = None, params: Any = None) -> None:
            self.strategy = strategy or HookStrategy.DEFAULT
            self.params = params

    class MenuItemType:
        """Заглушка типов пунктов меню (значения как в SDK exteraGram)."""

        DRAWER_MENU = "DRAWER_MENU"
        MESSAGE_CONTEXT_MENU = "MESSAGE_CONTEXT_MENU"
        CHAT_ACTION_MENU = "CHAT_ACTION_MENU"
        PROFILE_ACTION_MENU = "PROFILE_ACTION_MENU"

    class MenuItemData:
        """Заглушка описания пункта меню."""

        def __init__(self, **kwargs: Any) -> None:
            self.__dict__.update(kwargs)

    class BasePlugin:
        """Заглушка базового класса плагина для офлайн-тестов.

        Повторяет минимальный публичный интерфейс SDK, фиксируя вызовы
        регистрации, чтобы их можно было проверить в тестах.
        """

        def __init__(self) -> None:
            self._settings: dict[str, Any] = {}
            self.registered_hooks: list[Any] = []
            self.registered_menu_items: list[Any] = []
            self.registered_xposed: list[Any] = []
            self.unhooked: list[Any] = []
            self.logged: list[str] = []

        def add_on_send_message_hook(self, priority: int = 0) -> None:
            self.registered_hooks.append(("send_message", priority))

        def hook_method(self, member: Any, hook: Any, priority: int = 10) -> Any:
            """Зафиксировать Xposed-хук; вернуть дескриптор для unhook."""
            handle = ("xposed", member, hook, priority)
            self.registered_xposed.append(handle)
            return handle

        def unhook_method(self, handle: Any) -> None:
            """Зафиксировать снятие Xposed-хука."""
            self.unhooked.append(handle)

        def add_hook(self, name: str, priority: int = 0) -> None:
            self.registered_hooks.append((name, priority))

        def add_menu_item(self, data: Any) -> None:
            self.registered_menu_items.append(data)

        def get_setting(self, key: str, default: Any = None) -> Any:
            return self._settings.get(key, default)

        def set_setting(self, key: str, value: Any) -> None:
            self._settings[key] = value

        def log(self, message: str) -> None:
            self.logged.append(message)


# --------------------------------------------------------------------------
# Расширенный SDK (события приложения и Xposed-хуки).
#
# Импортируется НЕЗАВИСИМЫМИ ``try/except``, отдельно от ядра выше: на
# старой сборке SDK какого-то из этих имён может не быть, и это не должно
# сбрасывать ``SDK_AVAILABLE`` и подменять ядро (``BasePlugin`` и пр.)
# заглушками. Каждое имя при отсутствии получает собственную офлайн-заглушку
# с тем же интерфейсом — для офлайн-тестов.
# --------------------------------------------------------------------------

try:  # pragma: no cover - ветка выполняется только на устройстве
    from base_plugin import AppEvent
except Exception:  # pragma: no cover - ветка для обычного Python

    class AppEvent:
        """Заглушка событий жизненного цикла приложения (значения как в SDK)."""

        START = "START"
        STOP = "STOP"
        PAUSE = "PAUSE"
        RESUME = "RESUME"


try:  # pragma: no cover - ветка выполняется только на устройстве
    from base_plugin import BaseHook
except Exception:  # pragma: no cover - ветка для обычного Python

    class BaseHook:
        """Заглушка базового класса Xposed-хука."""


try:  # pragma: no cover - ветка выполняется только на устройстве
    from base_plugin import MethodHook
except Exception:  # pragma: no cover - ветка для обычного Python

    class MethodHook(BaseHook):
        """Заглушка хука метода: переопределяемые before/after — no-op офлайн."""

        def before_hooked_method(self, param: Any) -> None:
            """Вызывается до оригинального метода (офлайн — ничего не делает)."""

        def after_hooked_method(self, param: Any) -> None:
            """Вызывается после оригинального метода (офлайн — ничего не делает)."""


try:  # pragma: no cover - ветка выполняется только на устройстве
    from base_plugin import MethodReplacement
except Exception:  # pragma: no cover - ветка для обычного Python

    class MethodReplacement(BaseHook):
        """Заглушка полной замены метода (офлайн — возвращает ``None``)."""

        def replace_hooked_method(self, param: Any) -> Any:
            """Замещает оригинальный метод (офлайн — ничего не делает)."""
            return None


try:  # pragma: no cover - ветка выполняется только на устройстве
    from base_plugin import HookFilter
except Exception:  # pragma: no cover - ветка для обычного Python

    class HookFilter:
        """Заглушка фильтров Xposed-хуков.

        Константы — строки, параметрические фильтры возвращают кортеж-маркер
        ``(имя, *аргументы)``. Этого достаточно офлайн-тестам, чтобы
        проверить, что фильтр дошёл до регистрации без изменений.
        """

        RESULT_IS_NULL = "RESULT_IS_NULL"
        RESULT_IS_TRUE = "RESULT_IS_TRUE"
        RESULT_IS_FALSE = "RESULT_IS_FALSE"
        RESULT_NOT_NULL = "RESULT_NOT_NULL"

        @staticmethod
        def ResultIsInstanceOf(clazz: Any) -> tuple:
            """Результат является экземпляром ``clazz``."""
            return ("ResultIsInstanceOf", clazz)

        @staticmethod
        def ResultEqual(value: Any) -> tuple:
            """Результат равен ``value``."""
            return ("ResultEqual", value)

        @staticmethod
        def ResultNotEqual(value: Any) -> tuple:
            """Результат не равен ``value``."""
            return ("ResultNotEqual", value)

        @staticmethod
        def ArgumentIsNull(index: int) -> tuple:
            """Аргумент ``index`` равен ``null``."""
            return ("ArgumentIsNull", index)

        @staticmethod
        def ArgumentNotNull(index: int) -> tuple:
            """Аргумент ``index`` не ``null``."""
            return ("ArgumentNotNull", index)

        @staticmethod
        def ArgumentIsFalse(index: int) -> tuple:
            """Аргумент ``index`` равен ``false``."""
            return ("ArgumentIsFalse", index)

        @staticmethod
        def ArgumentIsTrue(index: int) -> tuple:
            """Аргумент ``index`` равен ``true``."""
            return ("ArgumentIsTrue", index)

        @staticmethod
        def ArgumentIsInstanceOf(index: int, clazz: Any) -> tuple:
            """Аргумент ``index`` является экземпляром ``clazz``."""
            return ("ArgumentIsInstanceOf", index, clazz)

        @staticmethod
        def ArgumentEqual(index: int, value: Any) -> tuple:
            """Аргумент ``index`` равен ``value``."""
            return ("ArgumentEqual", index, value)

        @staticmethod
        def ArgumentNotEqual(index: int, value: Any) -> tuple:
            """Аргумент ``index`` не равен ``value``."""
            return ("ArgumentNotEqual", index, value)

        @staticmethod
        def Condition(mvel_expr: str, obj: Any = None) -> tuple:
            """MVEL-выражение истинно."""
            return ("Condition", mvel_expr, obj)

        @staticmethod
        def Or(*filters: Any) -> tuple:
            """Хотя бы один из вложенных фильтров истинен."""
            return ("Or", *filters)


try:  # pragma: no cover - ветка выполняется только на устройстве
    from base_plugin import hook_filters
except Exception:  # pragma: no cover - ветка для обычного Python

    def hook_filters(*filters: Any) -> Any:
        """Заглушка декоратора фильтров Xposed-хука.

        Офлайн сохраняет фильтры в атрибуте функции (``__catalib_filters__``),
        чтобы тест мог проверить, что фильтры применены, и возвращает функцию
        без изменений.
        """

        def decorator(func: Any) -> Any:
            existing = getattr(func, "__catalib_filters__", ())
            func.__catalib_filters__ = tuple(existing) + tuple(filters)
            return func

        return decorator


try:  # pragma: no cover - ветка выполняется только на устройстве
    from hook_utils import find_class
except Exception:  # pragma: no cover - ветка для обычного Python

    def find_class(name: str) -> Any:
        """Заглушка поиска Java-класса: вне exteraGram класса нет."""
        return None


def log(message: str) -> None:
    """Записать строку в лог приложения (или в no-op вне exteraGram)."""
    try:  # pragma: no cover - на устройстве
        from android_utils import log as _log

        _log(message)
    except Exception:
        pass


def run_on_ui_thread(callback: Any) -> None:
    """Выполнить callback в UI-потоке (на устройстве) или сразу (офлайн)."""
    try:  # pragma: no cover - на устройстве
        from android_utils import run_on_ui_thread as _ui

        _ui(callback)
        return
    except Exception:
        callback()


def get_plugins_dir() -> str:
    """Каталог плагинов на устройстве; во офлайн-режиме — временный каталог."""
    try:  # pragma: no cover - на устройстве
        from file_utils import get_plugins_dir as _dir

        return _dir()
    except Exception:
        return tempfile.gettempdir()


__all__ = [
    "SDK_AVAILABLE",
    "AppEvent",
    "BaseHook",
    "BasePlugin",
    "HookFilter",
    "HookResult",
    "HookStrategy",
    "MenuItemData",
    "MenuItemType",
    "MethodHook",
    "MethodReplacement",
    "find_class",
    "get_plugins_dir",
    "hook_filters",
    "log",
    "run_on_ui_thread",
]
